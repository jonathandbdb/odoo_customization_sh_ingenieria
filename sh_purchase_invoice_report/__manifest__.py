# -*- coding: utf-8 -*-
{
    "name": "sh_purchase_invoice_report",
    "version": "1.0.0",
    "summary": "Agrega columna de secuencia al reporte de factura de proveedor",
    "description": """
Personalización del reporte de factura de proveedor para SH Ingeniería.
- Agrega columna SECUENCIA a la tabla de líneas del reporte de factura
    """,
    "category": "Custom",
    "author": "NEXIT",
    "website": "https://www.nexit.com.uy",
    "license": "OPL-1",
    "depends": [
        "account",
    ],
    "data": [
        "data/paperformat.xml",
        "views/report_invoice.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
