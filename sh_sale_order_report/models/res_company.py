# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Texto institucional con los aspectos técnicos por defecto que se vuelcan
    # en cada cotización al crearla. Se puede sobreescribir por cotización.
    sh_technical_aspects = fields.Html(
        string="Default Technical Aspects",
        translate=False,
        help="Texto por defecto de aspectos técnicos para las cotizaciones de la compañía.",
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
