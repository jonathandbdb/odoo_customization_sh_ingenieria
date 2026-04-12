# -*- coding: utf-8 -*-
{
    "name": "SH Stock Picking Report",

    "version": "1.0.0",

    "summary": "Reporte personalizado de Remisión para SH Ingeniería",

    "description": """
Reporte personalizado de Remisión (stock.picking) para SH Ingeniería.
- Header con logo corporativo y NIT
- Footer con datos de contacto
- Tablas de proveedor, dirección, fechas, elaborado por, forma de pago
- Tabla de líneas de producto con seriales, cantidad y unidad de medida
- Firmas de entrega y recepción
- Formato de papel personalizado (sin header estándar Odoo)
    """,

    "category": "Inventory/Reporting",

    "license": "OPL-1",

    "depends": [
        "purchase_stock",
        "sale_stock",
        "sh_base_config",
    ],

    "data": [
        "report/report_layouts.xml",
        "report/report_delivery.xml",
        "report/report_actions.xml",
    ],

    "assets": {},

    "installable": True,

    "application": False,

    "auto_install": False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
