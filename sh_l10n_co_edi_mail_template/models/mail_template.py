# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# XMLIDs de las plantillas de correo custom a normalizar
_SH_MAIL_TEMPLATE_XMLIDS = (
    "l10n_co_dian.email_template_edi_invoice",
    "l10n_co_dian.email_template_edi_credit_note",
    "account.email_template_edi_invoice",
)

# Campos traducibles que deben forzarse al valor en_US
_SH_TRANSLATABLE_FIELDS = ("name", "subject", "body_html", "description")


class MailTemplate(models.Model):
    _inherit = "mail.template"

    @api.model
    def _sh_normalize_edi_templates(self):
        """
        Normalizar las plantillas de correo EDI Colombia custom.

        Las plantillas originales de Odoo tienen traducciones cargadas
        (es_ES, es_CO, etc.). Cuando el partner destinatario usa un idioma
        distinto a en_US, el render del body_html aplica la traducción
        antigua en lugar del contenido custom. Este método fuerza el valor
        de en_US en TODOS los idiomas instalados para garantizar que el
        render use siempre el contenido custom, sin importar el idioma.

        Se invoca vía <function> en el XML de datos para que se ejecute
        tanto en la instalación como en cada actualización del módulo.
        """
        installed_langs = self.env["res.lang"].search([("active", "=", True)]).mapped("code")
        for xmlid in _SH_MAIL_TEMPLATE_XMLIDS:
            template = self.env.ref(xmlid, raise_if_not_found=False)
            if not template:
                _logger.info("Plantilla %s no encontrada, se omite.", xmlid)
                continue
            # Leer valores de referencia desde en_US (cargado por el XML)
            source_vals = {
                field_name: template.with_context(lang="en_US")[field_name]
                for field_name in _SH_TRANSLATABLE_FIELDS
            }
            # Replicar el valor en_US en cada idioma instalado para
            # eliminar las traducciones remanentes de la plantilla original.
            for lang_code in installed_langs:
                template.with_context(lang=lang_code).write(source_vals)
            _logger.info(
                "Plantilla %s normalizada en idiomas: %s.",
                xmlid,
                ", ".join(installed_langs),
            )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
