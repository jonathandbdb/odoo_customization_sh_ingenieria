# -*- coding: utf-8 -*-
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _l10n_co_dian_update_data(self, company):
        """
        Extiende el método original para evitar actualizar el campo email
        en cualquier tipo de contacto.

        Se sigue consultando la DIAN y se actualizan todos los demás campos,
        pero se descarta el email para evitar que sea sobreescrito.
        """
        self.ensure_one()
        data = self._l10n_co_dian_call_get_acquirer({
            'identification_type': self._l10n_co_edi_get_carvajal_code_for_identification_type(),
            'identification_number': self._get_vat_without_verification_code(),
            'company': company,
        })
        if data:
            data.pop('email', None)
            self.write(data)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
