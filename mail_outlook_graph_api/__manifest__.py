# -*- coding: utf-8 -*-
{
    "name": "Mail Outlook Graph API",
    "version": "1.0.0",
    "summary": "Enviar correos salientes mediante Microsoft Graph API en lugar de SMTP",
    "description": """
Módulo que intercepta el envío de correos por SMTP para servidores Outlook OAuth
y los redirige a través de la API REST de Microsoft Graph.

- Útil cuando el puerto 587 (SMTP) está bloqueado en el servidor.
- Reutiliza la autenticación OAuth2 del módulo nativo microsoft_outlook.
- Requiere agregar el permiso Microsoft Graph > Mail.Send en la App Registration de Azure AD.
    """,
    "category": "Custom",
    "author": "NEXIT",
    "website": "https://www.nexit.com.uy",
    "license": "OPL-1",
    "depends": ["microsoft_outlook"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
