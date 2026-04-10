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

    :param number: Número entero a convertir
    :type number: int
    :return: Representación en letras
    :rtype: str
    """
    if number == 0:
        return 'CERO'
    if number < 0:
        return 'MENOS ' + _number_to_words(-number)

    resultado = ''

    # Miles de millones
    if number >= 1000000000:
        if number // 1000000000 == 1:
            resultado += 'MIL '
        else:
            resultado += _number_to_words(number // 1000000000) + ' MIL '
        number %= 1000000000

    # Millones
    if number >= 1000000:
        if number // 1000000 == 1:
            resultado += 'UN MILLON '
        else:
            resultado += _number_to_words(number // 1000000) + ' MILLONES '
        number %= 1000000

    # Miles
    if number >= 1000:
        if number // 1000 == 1:
            resultado += 'MIL '
        else:
            resultado += _number_to_words(number // 1000) + ' MIL '
        number %= 1000

    # Centenas
    if number >= 100:
        if number == 100:
            resultado += 'CIEN'
            return resultado.strip()
        resultado += CENTENAS[number // 100] + ' '
        number %= 100

    # Decenas y unidades
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

    :param amount: Monto a convertir
    :type amount: float
    :param currency_name: Nombre de la moneda
    :type currency_name: str
    :return: Representación en letras del monto
    :rtype: str
    """
    entero = int(amount)
    centavos = round((amount - entero) * 100)
    texto = _number_to_words(entero)
    texto += ' ' + currency_name
    if centavos:
        texto += ' CON ' + _number_to_words(centavos) + ' CENTAVOS'
    return texto


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Total en letras (campo computado)
    total_letras = fields.Char(
        string="Amount in Words",
        compute="_compute_total_letras",
    )

    @api.depends("amount_total", "currency_id")
    def _compute_total_letras(self):
        """
        Calcular el total de la orden de compra en letras.
        """
        for order in self:
            currency_name = 'PESOS'
            if order.currency_id and order.currency_id.name == 'USD':
                currency_name = 'DOLARES'
            order.total_letras = amount_to_words(
                order.amount_total, currency_name
            ).lower()

    def _get_date_format(self, date_value):
        """
        Formatear una fecha/datetime al formato legible para reportes.

        :param date_value: Fecha o datetime a formatear
        :type date_value: datetime or date or False
        :return: Fecha formateada como cadena
        :rtype: str
        """
        if not date_value:
            return ''
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%A, %d de %B de %Y')
        return str(date_value)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
