# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Diccionarios para conversión de números a letras en español
UNIDADES = (
    '', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE',
    'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS', 'DIECISIETE',
    'DIECIOCHO', 'DIECINUEVE', 'VEINTE',
)
DECENAS = (
    'VENTI', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA',
    'SETENTA', 'OCHENTA', 'NOVENTA',
)
CENTENAS = (
    '', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS',
    'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS',
)


def _number_to_words(number):
    """
    Convertir un número entero a su representación en letras (español).
    """
    if number == 0:
        return 'CERO'
    if number < 0:
        return 'MENOS ' + _number_to_words(-number)

    resultado = ''

    if number >= 1000000000:
        if number // 1000000000 == 1:
            resultado += 'MIL '
        else:
            resultado += _number_to_words(number // 1000000000) + ' MIL '
        number %= 1000000000

    if number >= 1000000:
        if number // 1000000 == 1:
            resultado += 'UN MILLON '
        else:
            resultado += _number_to_words(number // 1000000) + ' MILLONES '
        number %= 1000000

    if number >= 1000:
        if number // 1000 == 1:
            resultado += 'MIL '
        else:
            resultado += _number_to_words(number // 1000) + ' MIL '
        number %= 1000

    if number >= 100:
        if number == 100:
            resultado += 'CIEN'
            return resultado.strip()
        resultado += CENTENAS[number // 100] + ' '
        number %= 100

    if number <= 20:
        resultado += UNIDADES[number]
    elif number < 30:
        resultado += 'VEINTI' + UNIDADES[number - 20]
    else:
        decena = (number // 10) - 2
        unidad = number % 10
        resultado += DECENAS[decena]
        if unidad:
            resultado += ' Y ' + UNIDADES[unidad]

    return resultado.strip()


def amount_to_words(amount, currency_name='PESOS'):
    """
    Convertir un monto monetario a su representación en letras.
    """
    entero = int(amount)
    centavos = round((amount - entero) * 100)
    texto = _number_to_words(entero)
    texto += ' ' + currency_name
    if centavos:
        texto += ' CON ' + _number_to_words(centavos) + ' CENTAVOS'
    return texto


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

    def _get_name_invoice_report(self):
        """
        Usar reporte personalizado para facturas de venta y notas crédito.
        """
        self.ensure_one()
        if self.move_type in ('out_invoice', 'out_refund'):
            return 'sh_customer_invoice_report.report_invoice_document_sh'
        return super()._get_name_invoice_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
