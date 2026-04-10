# -*- coding: utf-8 -*-
{
    "name": "formatos_sh",
    "version": "1.0.0",
    "summary": "Reportes personalizados para SH Ingeniería",
    "description": """
Reportes personalizados para SH Ingeniería.
- Orden de Compra personalizada
- Remisión (Entrega / Recepción)
- Factura de Venta Electrónica
- Factura de Proveedor
- Cotización / Orden de Venta
- Headers y footers corporativos
    """,
    "category": "Custom",
    "author": "Conecta",
    "website": "https://www.conecta.sh",
    "license": "OPL-1",
    "depends": [
        "base",
        "account",
        "purchase_stock",
        "sale_stock",
        "web",
    ],
    "data": [
        "report/report_layouts.xml",
        "report/report_purchase_order.xml",
        "report/report_delivery.xml",
        "report/report_invoice.xml",
        "report/report_vendor_bill.xml",
        "report/report_sale_order.xml",
        "report/report_actions.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
