# -*- coding: utf-8 -*-
{
    "name": "sh_sale_order_report",
    "version": "1.0.0",
    "summary": "Reporte personalizado de Presupuesto / Cotización para SH Ingeniería",
    "description": """
Reporte personalizado de Cotización (sale.order) para SH Ingeniería.
- Encabezado con logo corporativo y número de cotización
- Datos del cliente (nombre, dirección, teléfono, email)
- Tabla de líneas con Ref., Descripción, UM, Cantidad, Valor Unitario y Total
- Agrupación por secciones con subtotal por capítulo (Vr. Capítulo)
- Totales: Subtotal, IVA, Total
- Condiciones comerciales: plazos, tiempo de entrega, validez, garantía, sitio de entrega
- Firma del vendedor con datos de contacto
- Observaciones / notas
- Pie de página con datos de contacto de la compañía
    """,
    "category": "Sales/Reporting",
    "author": "CONECTA",
    "website": "https://www.conecta.sh",
    "depends": [
        "sale_management",
        "sh_base_config",
    ],
    "data": [
        "data/paperformat.xml",
        "views/sale_order_views.xml",
        "report/report_sale_order.xml",
        "report/report_actions.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
