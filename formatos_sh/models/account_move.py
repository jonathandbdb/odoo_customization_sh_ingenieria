# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .purchase_order import amount_to_words


class AccountMove(models.Model):
    _inherit = "account.move"

    # Total en letras para facturas
    total_letras = fields.Char(
        string="Amount in Words",
        compute="_compute_total_letras",
    )

    @api.depends("amount_total", "currency_id")
    def _compute_total_letras(self):
        """
        Calcular el total de la factura en letras.
        """
        for move in self:
            currency_name = 'PESOS'
            if move.currency_id and move.currency_id.name == 'USD':
                currency_name = 'DOLARES'
            move.total_letras = amount_to_words(
                move.amount_total, currency_name
            ).lower()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
