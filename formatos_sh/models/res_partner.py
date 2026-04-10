# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Número de identificación tributaria (NIT) sin dígito de verificación
    # Se auto-calcula a partir del campo vat, removiendo el dígito de verificación
    vat_num = fields.Char(
        string="Tax ID Number",
        compute="_compute_vat_num",
        store=True,
        readonly=False,
        help="Tax identification number without verification digit. Auto-computed from VAT.",
    )

    @api.depends("vat")
    def _compute_vat_num(self):
        """
        Calcular el número de identificación sin dígito de verificación.
        Si el VAT contiene un guión (ej. 800231215-1), se toma solo la parte
        antes del guión. Si no contiene guión, se usa el VAT completo.
        Permite edición manual (readonly=False, store=True).
        """
        for partner in self:
            if partner.vat:
                partner.vat_num = partner.vat.split('-')[0].strip()
            else:
                partner.vat_num = False
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
