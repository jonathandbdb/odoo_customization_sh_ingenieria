# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Texto de actividades económicas para el encabezado del reporte de factura
    invoice_economic_activities = fields.Text(
        string="Economic Activities (Invoice)",
        help="Economic activities text displayed on the invoice report header below the DIAN resolution.",
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
