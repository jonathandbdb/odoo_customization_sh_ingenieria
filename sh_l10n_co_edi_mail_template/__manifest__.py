# -*- coding: utf-8 -*-
{
    "name": "sh_l10n_co_edi_mail_template",
    "version": "19.0.1.0.2",
    "summary": "Plantilla de correo personalizada para documentos electrónicos Colombia (SH Ingeniería SAS)",
    "description": """
Sobrescribe la plantilla de correo utilizada por Odoo para el envío de documentos
electrónicos (Factura, Nota Crédito, Nota Débito) en la localización colombiana,
aplicando la maquetación y datos corporativos solicitados por SH INGENIERIA SAS.

Funcionalidades:
- Remitente fijo: "SH INGENIERIA SAS" <notificacioneserp@shingenieria.com>, independiente del usuario.
- Responder a: contabilidad@shingenieria.com.
- Asunto con estructura requerida por la DIAN / SH Ingeniería.
- Cuerpo HTML maquetado con logos, datos del documento y pie corporativo.
- Sin firma de usuario (user.signature) ni datos dinámicos del usuario remitente.
    """,
    "category": "Accounting/Localizations/EDI",
    "author": "CONECTA",
    "website": "https://www.conecta.sh",
    "license": "OPL-1",
    "depends": [
        "l10n_co_dian",
    ],
    "data": [
        "data/mail_template_edi_invoice.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
