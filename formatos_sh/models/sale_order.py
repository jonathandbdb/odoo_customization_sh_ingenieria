# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Fecha de escritura formateada para reportes
    formatted_write_date = fields.Char(
        string="Formatted Write Date",
        compute="_compute_formatted_write_date",
    )

    @api.depends("write_date")
    def _compute_formatted_write_date(self):
        """
        Calcular la fecha de última modificación formateada.
        """
        for order in self:
            if order.write_date:
                order.formatted_write_date = order.write_date.strftime(
                    '%d de %B de %Y'
                )
            else:
                order.formatted_write_date = ''

    def get_uppercase_string(self, text):
        """
        Convertir un texto a mayúsculas para uso en reportes.

        :param text: Texto a convertir
        :type text: str
        :return: Texto en mayúsculas
        :rtype: str
        """
        if text:
            return text.upper()
        return ''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
