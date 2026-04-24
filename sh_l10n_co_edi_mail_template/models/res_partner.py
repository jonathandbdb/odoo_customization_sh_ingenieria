# -*- coding: utf-8 -*-
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _l10n_co_dian_update_data(self, company):
        """
        Extiende el método original para evitar actualizar el campo email
        cuando el contacto es de tipo dirección de facturación (type = 'invoice').

        Para esos contactos se sigue consultando la DIAN y se actualizan todos
        los demás campos (ej: name), pero se descarta el email para evitar que
        sea sobreescrito antes de que Odoo envíe el correo de la factura.
        """
        if self.type != 'invoice':
            return super()._l10n_co_dian_update_data(company)

        # Para direcciones de facturación: actualizar todo excepto el email.
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
