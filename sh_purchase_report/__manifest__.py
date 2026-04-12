# -*- coding: utf-8 -*-
{
    "name": "sh_purchase_report",
    "version": "1.0.0",
    "summary": "Reporte personalizado de Orden de Compra para SH Ingeniería",
    "description": """
Reporte personalizado de Orden de Compra para SH Ingeniería.
- Formato corporativo con logo, encabezado y pie de página
- Detalle de proveedor, fechas, forma de pago
- Líneas con IVA por línea
- Total en letras (español)
- Firma responsable
    """,
    "category": "Custom",
    "author": "Conecta",
    "website": "https://www.conecta.sh",
    "license": "OPL-1",
    "depends": [
        "purchase",
        "sh_base_config",
    ],
    "data": [
        "data/paperformat.xml",
        "report/report_purchase_order.xml",
        "report/report_actions.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
