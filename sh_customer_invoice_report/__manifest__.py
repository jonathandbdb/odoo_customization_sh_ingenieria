# -*- coding: utf-8 -*-
{
    "name": "SH Customer Invoice Report",

    "version": "1.0.0",

    "summary": "Reporte personalizado de Factura de Venta para SH Ingeniería",

    "description": """
Reporte personalizado de Factura de Venta Electrónica / Nota Crédito / Nota Débito
para SH Ingeniería.
- Header con logo corporativo y número de documento
- Footer con datos de contacto
- Datos de empresa emisora y cliente
- Tabla de fechas y forma de pago
- Observaciones
- Tabla de líneas de factura (Item, Código, Descripción, UM, Cant, Precio U, IVA%, Total)
- Totales, retenciones (Retefuente, Reteiva, Reteica)
- Valor en letras
- Información bancaria y legal
- Formato de papel personalizado (sin header estándar Odoo)
    """,

    "category": "Accounting/Reporting",

    "license": "OPL-1",

    "depends": [
        "account",
        "account_debit_note",
        "l10n_co_edi",
        "sh_base_config",
    ],

    "data": [
        "report/report_layouts.xml",
        "report/report_invoice.xml",
        "report/report_actions.xml",
    ],

    "assets": {},

    "installable": True,

    "application": False,

    "auto_install": False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
