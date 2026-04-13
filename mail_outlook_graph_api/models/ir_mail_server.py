# -*- coding: utf-8 -*-
import base64
import json
import logging
import time

import requests

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Constantes para la API de Microsoft Graph
GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'
GRAPH_SEND_MAIL_ENDPOINT = '{base}/users/{user}/sendMail'
GRAPH_SCOPE = 'https://graph.microsoft.com/Mail.Send'
TOKEN_REQUEST_TIMEOUT = 10

# Umbral de validez del token en segundos (renovar 30s antes de expirar)
GRAPH_TOKEN_VALIDITY_THRESHOLD = 30


class _GraphApiSession:
    """
    Objeto sesión dummy que reemplaza la conexión SMTP para servidores Outlook.
    mail.mail.send() pre-establece una conexión SMTP llamando a _connect__()
    ANTES de llamar a send_email(). Si el puerto 587 está bloqueado, esa conexión
    falla y el batch se marca como excepción sin ejecutar nuestro override.

    Esta clase simula la interfaz mínima de un objeto SMTP para que el flujo
    de mail.mail funcione sin intentar conectar por SMTP.
    """

    def __init__(self, mail_server):
        # Atributos que usa _prepare_email_message__() y el flujo de mail.mail
        self.from_filter = mail_server.from_filter or ''
        self.smtp_from = mail_server.smtp_user or ''
        self._mail_server = mail_server

    def ehlo(self):
        """Operación no-op para compatibilidad."""

    def quit(self):
        """Operación no-op — no hay conexión real que cerrar."""

    def send_message(self, message, smtp_from, smtp_to_list):
        """
        No-op: el envío real se hace en send_email() vía Graph API.
        Este método existe por si algún flujo intenta usarlo.
        """
        pass


class IrMailServer(models.Model):
    """
    Extensión del servidor de correo para enviar emails vía Microsoft Graph API
    en lugar de SMTP, útil cuando el puerto 587 está bloqueado.
    """
    _inherit = 'ir.mail_server'

    def _connect__(self, host=None, port=None, user=None, password=None, encryption=None,
                   smtp_from=None, ssl_certificate=None, ssl_private_key=None,
                   smtp_debug=False, mail_server_id=None, allow_archived=False):
        """
        Interceptar la conexión SMTP. Si el servidor es Outlook, retornar un
        objeto sesión dummy en lugar de intentar conectar por SMTP (que fallaría
        si el puerto 587 está bloqueado).

        Esto es crítico porque mail.mail.send() llama a _connect__() ANTES de
        send_email(). Si _connect__() falla, el batch completo se marca como
        excepción y nuestro override de send_email() nunca se ejecuta.
        """
        # Resolver el servidor para verificar si es Outlook
        mail_server = None
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
        elif not host:
            mail_server, smtp_from = self.sudo()._find_mail_server(smtp_from)

        # Si es servidor Outlook, retornar sesión dummy (sin tocar SMTP)
        if mail_server and mail_server.smtp_authentication == 'outlook':
            _logger.info(
                'Graph API: retornando sesión dummy para servidor Outlook "%s" (sin conexión SMTP)',
                mail_server.name,
            )
            return _GraphApiSession(mail_server)

        # Para otros servidores, flujo SMTP normal
        return super()._connect__(
            host=host, port=port, user=user, password=password,
            encryption=encryption, smtp_from=smtp_from,
            ssl_certificate=ssl_certificate, ssl_private_key=ssl_private_key,
            smtp_debug=smtp_debug, mail_server_id=mail_server_id,
            allow_archived=allow_archived,
        )

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_ssl_certificate=None, smtp_ssl_private_key=None,
                   smtp_debug=False, smtp_session=None):
        """
        Interceptar el envío de correo. Si el servidor usa autenticación Outlook,
        enviar vía Microsoft Graph API. Caso contrario, delegar al flujo SMTP normal.

        :param message: Objeto email.message.Message con el correo a enviar
        :param mail_server_id: ID del servidor de correo a utilizar
        :return: Message-ID del correo enviado
        """
        # Detectar si la sesión es nuestra sesión dummy de Graph API
        if isinstance(smtp_session, _GraphApiSession):
            mail_server = smtp_session._mail_server
        else:
            # Resolver el servidor de correo por otros medios
            mail_server = self._resolve_outlook_server(message, mail_server_id, smtp_server)

        # Si no es un servidor Outlook, delegar al flujo SMTP normal
        if not mail_server or mail_server.smtp_authentication != 'outlook':
            return super().send_email(
                message, mail_server_id=mail_server_id,
                smtp_server=smtp_server, smtp_port=smtp_port,
                smtp_user=smtp_user, smtp_password=smtp_password,
                smtp_encryption=smtp_encryption,
                smtp_ssl_certificate=smtp_ssl_certificate,
                smtp_ssl_private_key=smtp_ssl_private_key,
                smtp_debug=smtp_debug, smtp_session=smtp_session,
            )

        # No enviar correos en modo test
        if self._disable_send():
            _logger.debug("Graph API: omitir envío en modo test")
            return message['Message-Id']

        _logger.info('Graph API: enviando correo mediante Microsoft Graph para servidor "%s"', mail_server.name)

        # Obtener token de acceso para Graph API (con caché)
        access_token = self._get_graph_access_token(mail_server)

        # Construir payload desde el mensaje RFC2822
        sender_email = mail_server.smtp_user
        payload = self._build_graph_payload(message)

        # Ejecutar el envío vía Graph API
        self._send_via_graph(access_token, sender_email, payload, message)

        return message['Message-Id']

    def _resolve_outlook_server(self, message, mail_server_id, smtp_server):
        """
        Resolver el registro ir.mail_server correspondiente.

        :param message: Mensaje email
        :param mail_server_id: ID del servidor de correo
        :param smtp_server: Host SMTP manual
        :return: Registro ir.mail_server o None
        """
        if mail_server_id:
            return self.sudo().browse(mail_server_id)
        if not smtp_server:
            mail_server, _smtp_from = self.sudo()._find_mail_server(message['From'])
            return mail_server
        return None

    def _get_graph_access_token(self, mail_server):
        """
        Obtener un token de acceso válido para Microsoft Graph API.
        Usa el refresh_token del servidor Outlook para solicitar un token
        con scope de Graph API (Mail.Send).

        Implementa caché in-memory: si el token aún es válido, lo reutiliza.
        Esto evita pedir un token nuevo para cada correo del mismo batch.

        :param mail_server: Registro ir.mail_server con autenticación Outlook
        :return: Access token válido para Graph API
        :raises UserError: Si no se puede obtener el token
        """
        if not mail_server.microsoft_outlook_refresh_token:
            raise UserError(_(
                'Please connect with your Outlook account before using it. '
                'Server: %s', mail_server.name
            ))

        # Verificar caché del token Graph API (almacenado en el contexto del server)
        cache_key = f'_graph_api_token_{mail_server.id}'
        cache_exp_key = f'_graph_api_token_exp_{mail_server.id}'
        cached_token = getattr(mail_server, cache_key, None)
        cached_exp = getattr(mail_server, cache_exp_key, 0)
        now = int(time.time())

        if cached_token and cached_exp > now + GRAPH_TOKEN_VALIDITY_THRESHOLD:
            _logger.info(
                'Graph API: reutilizando token cacheado para servidor "%s" (expira en %d min)',
                mail_server.name, (cached_exp - now) // 60,
            )
            return cached_token

        Config = self.env['ir.config_parameter'].sudo()
        client_id = Config.get_param('microsoft_outlook_client_id')
        client_secret = Config.get_param('microsoft_outlook_client_secret')

        if not client_id or not client_secret:
            raise UserError(_(
                'Microsoft Outlook client credentials are not configured. '
                'Please set microsoft_outlook_client_id and microsoft_outlook_client_secret '
                'in System Parameters.'
            ))

        endpoint = self.env['ir.config_parameter'].sudo().get_param(
            'microsoft_outlook.endpoint',
            'https://login.microsoftonline.com/common/oauth2/v2.0/',
        )
        token_url = endpoint.rstrip('/') + '/token'

        try:
            response = requests.post(
                token_url,
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': mail_server.microsoft_outlook_refresh_token,
                    'scope': f'offline_access {GRAPH_SCOPE}',
                },
                timeout=TOKEN_REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            _logger.error('Graph API: error de red al obtener token: %s', e)
            raise UserError(_(
                'Could not connect to Microsoft authentication service. %s', str(e)
            ))

        if not response.ok:
            try:
                error_data = response.json()
                error_desc = error_data.get('error_description', str(error_data))
            except Exception:
                error_desc = response.text
            _logger.error('Graph API: error al obtener token: %s', error_desc)
            raise UserError(_(
                'Could not obtain Microsoft Graph access token. '
                'Make sure the Azure AD app has the "Mail.Send" permission with Admin Consent. '
                'Error: %s', error_desc
            ))

        token_data = response.json()
        access_token = token_data.get('access_token')

        if not access_token:
            raise UserError(_('Microsoft returned an empty access token.'))

        # Actualizar refresh_token si Microsoft devuelve uno nuevo
        new_refresh_token = token_data.get('refresh_token')
        if new_refresh_token and new_refresh_token != mail_server.microsoft_outlook_refresh_token:
            mail_server.sudo().write({
                'microsoft_outlook_refresh_token': new_refresh_token,
            })
            _logger.info('Graph API: refresh token actualizado para servidor "%s"', mail_server.name)

        # Cachear el token en el objeto para reutilizar en el mismo batch
        expires_in = int(token_data.get('expires_in', 3600))
        try:
            setattr(mail_server, cache_key, access_token)
            setattr(mail_server, cache_exp_key, now + expires_in)
        except Exception:
            pass  # Si no se puede cachear, no es crítico

        return access_token

    def _build_graph_payload(self, message):
        """
        Construir el payload JSON para el endpoint sendMail de Microsoft Graph
        a partir de un objeto email.message.Message.

        :param message: Objeto email.message.Message
        :return: Dict con la estructura requerida por Graph API
        """
        # Extraer destinatarios
        to_recipients = self._parse_email_addresses(message.get('To', ''))
        cc_recipients = self._parse_email_addresses(message.get('Cc', ''))
        bcc_recipients = self._parse_email_addresses(message.get('Bcc', ''))

        # Extraer cuerpo (preferir HTML)
        body_content, body_type = self._extract_body(message)

        # Extraer adjuntos
        attachments = self._extract_attachments(message)

        # Construir el payload según la especificación de Graph API
        payload = {
            'message': {
                'subject': message.get('Subject', ''),
                'body': {
                    'contentType': body_type,
                    'content': body_content or '',
                },
                'toRecipients': to_recipients,
                'ccRecipients': cc_recipients,
                'bccRecipients': bcc_recipients,
            },
            'saveToSentItems': True,
        }

        # Agregar Message-Id como Internet Message Header si existe
        message_id = message.get('Message-Id')
        if message_id:
            payload['message']['internetMessageHeaders'] = [
                {
                    'name': 'X-Odoo-Message-Id',
                    'value': message_id,
                }
            ]

        # Agregar Reply-To si existe
        reply_to = message.get('Reply-To')
        if reply_to:
            payload['message']['replyTo'] = self._parse_email_addresses(reply_to)

        # Agregar adjuntos si hay
        if attachments:
            payload['message']['attachments'] = attachments

        return payload

    @api.model
    def _parse_email_addresses(self, header_value):
        """
        Parsear una cabecera de email con direcciones y convertir al formato
        requerido por Graph API.

        :param header_value: String con direcciones email (ej: "Name <email@test.com>, other@test.com")
        :return: Lista de dicts con formato Graph API
        """
        if not header_value:
            return []

        from email.utils import getaddresses
        addresses = getaddresses([header_value])
        recipients = []
        for display_name, email_addr in addresses:
            if email_addr:
                recipient = {'emailAddress': {'address': email_addr}}
                if display_name:
                    recipient['emailAddress']['name'] = display_name
                recipients.append(recipient)
        return recipients

    @api.model
    def _extract_body(self, message):
        """
        Extraer el cuerpo del mensaje, priorizando HTML sobre texto plano.

        :param message: Objeto email.message.Message
        :return: Tupla (contenido, tipo) donde tipo es 'HTML' o 'Text'
        """
        html_body = None
        text_body = None

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                # Ignorar las partes que son adjuntos
                if 'attachment' in content_disposition:
                    continue
                if content_type == 'text/html' and html_body is None:
                    html_body = part.get_payload(decode=True)
                    if html_body:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = html_body.decode(charset, errors='replace')
                elif content_type == 'text/plain' and text_body is None:
                    text_body = part.get_payload(decode=True)
                    if text_body:
                        charset = part.get_content_charset() or 'utf-8'
                        text_body = text_body.decode(charset, errors='replace')
        else:
            content_type = message.get_content_type()
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or 'utf-8'
                decoded = payload.decode(charset, errors='replace')
                if content_type == 'text/html':
                    html_body = decoded
                else:
                    text_body = decoded

        if html_body:
            return html_body, 'HTML'
        return text_body or '', 'Text'

    @api.model
    def _extract_attachments(self, message):
        """
        Extraer adjuntos del mensaje y convertirlos al formato Graph API (Base64).

        :param message: Objeto email.message.Message
        :return: Lista de dicts con adjuntos en formato Graph API
        """
        attachments = []
        if not message.is_multipart():
            return attachments

        for part in message.walk():
            content_disposition = str(part.get('Content-Disposition', ''))
            if 'attachment' not in content_disposition and part.get_content_maintype() != 'application':
                # Si no es explícitamente un adjunto y no es application/*, verificar
                # si es una parte inline con nombre de archivo
                filename = part.get_filename()
                if not filename:
                    continue

            filename = part.get_filename()
            if not filename:
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            # Limitar adjuntos inline a 4MB (límite de Graph API para adjuntos en el payload)
            if len(payload) > 4 * 1024 * 1024:
                _logger.warning(
                    'Graph API: adjunto "%s" excede 4MB (%d bytes), se omite',
                    filename, len(payload)
                )
                continue

            attachment = {
                '@odata.type': '#microsoft.graph.fileAttachment',
                'name': filename,
                'contentBytes': base64.b64encode(payload).decode('ascii'),
            }

            # Intentar establecer el content type
            content_type = part.get_content_type()
            if content_type:
                attachment['contentType'] = content_type

            # Marcar como inline si corresponde
            if 'inline' in content_disposition:
                content_id = part.get('Content-Id', '').strip('<>')
                if content_id:
                    attachment['isInline'] = True
                    attachment['contentId'] = content_id

            attachments.append(attachment)

        return attachments

    def _send_via_graph(self, access_token, sender_email, payload, message):
        """
        Ejecutar el envío del correo vía Microsoft Graph API.

        :param access_token: Token de acceso válido para Graph API
        :param sender_email: Email del remitente (UPN en Azure AD)
        :param payload: Dict con el payload del correo
        :param message: Mensaje original (para logging)
        :raises UserError: Si el envío falla
        """
        url = GRAPH_SEND_MAIL_ENDPOINT.format(
            base=GRAPH_API_BASE,
            user=sender_email,
        )

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            _logger.error('Graph API: error de red al enviar correo: %s', e)
            raise UserError(_(
                'Could not connect to Microsoft Graph API. %s', str(e)
            ))

        # Graph API retorna 202 Accepted para envío exitoso
        if response.status_code == 202:
            _logger.info(
                'Graph API: correo enviado exitosamente [%s] -> %s',
                message.get('Subject', '(sin asunto)'),
                message.get('To', '(sin destinatario)'),
            )
            return True

        # Manejar errores
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', str(error_data))
            error_code = error_data.get('error', {}).get('code', 'Unknown')
        except Exception:
            error_msg = response.text
            error_code = str(response.status_code)

        _logger.error(
            'Graph API: error al enviar correo [%s]: %s - %s',
            error_code, error_msg, message.get('Subject', '')
        )
        raise UserError(_(
            'Mail delivery failed via Microsoft Graph API.\n'
            'Error code: %(code)s\n'
            'Message: %(message)s',
            code=error_code,
            message=error_msg,
        ))
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
