# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Diccionarios para conversión de números a letras en español
UNIDADES = (
    '', 'un', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve',
    'diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciseis', 'diecisiete',
    'dieciocho', 'diecinueve', 'veinte',
)
DECENAS = (
    'veinti', 'treinta', 'cuarenta', 'cincuenta', 'sesenta',
    'setenta', 'ochenta', 'noventa',
)
CENTENAS = (
    '', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos',
    'seiscientos', 'setecientos', 'ochocientos', 'novecientos',
)

# Mapa de nombres de días y meses en español
DIAS_SEMANA = {
    0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
    4: 'viernes', 5: 'sábado', 6: 'domingo',
}
MESES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}


def _number_to_words(number):
    """
    Convertir un número entero a su representación en letras (español).

    :param number: Número entero a convertir
    :type number: int
    :return: Representación en letras
    :rtype: str
    """
    if number == 0:
        return 'cero'
    if number < 0:
        return 'menos ' + _number_to_words(-number)

    resultado = ''

    # Miles de millones
    if number >= 1000000000:
        if number // 1000000000 == 1:
            resultado += 'mil '
        else:
            resultado += _number_to_words(number // 1000000000) + ' mil '
        number %= 1000000000

    # Millones
    if number >= 1000000:
        if number // 1000000 == 1:
            resultado += 'un millón '
        else:
            resultado += _number_to_words(number // 1000000) + ' millones '
        number %= 1000000

    # Miles
    if number >= 1000:
        if number // 1000 == 1:
            resultado += 'mil '
        else:
            resultado += _number_to_words(number // 1000) + ' mil '
        number %= 1000

    # Centenas
    if number >= 100:
        if number == 100:
            resultado += 'cien'
            return resultado.strip()
        resultado += CENTENAS[number // 100] + ' '
        number %= 100

    # Decenas y unidades
    if number <= 20:
        resultado += UNIDADES[number]
    elif number < 30:
        resultado += 'veinti' + UNIDADES[number - 20]
    else:
        decena = (number // 10) - 2
        unidad = number % 10
        resultado += DECENAS[decena]
        if unidad:
            resultado += ' y ' + UNIDADES[unidad]

    return resultado.strip()


def amount_to_words(amount, currency_name='pesos'):
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
    texto = _number_to_words(entero) + ' ' + currency_name
    texto += ' con ' + _number_to_words(centavos) + ' centavos'
    return texto


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Monto total en letras para impresión en reportes
    total_letras = fields.Char(
        string="Total in Words",
        compute="_compute_total_letras",
        help="Total amount expressed in words for printing on reports.",
    )

    @api.depends("amount_total", "currency_id")
    def _compute_total_letras(self):
        """
        Calcular el total en letras según la moneda de la orden.
        Mapea el nombre de la moneda a su nombre en español para la cadena.
        """
        # Mapa de monedas a su nombre en español
        currency_map = {
            'COP': 'pesos',
            'USD': 'dólares',
            'EUR': 'euros',
            'UYU': 'pesos uruguayos',
        }
        for order in self:
            currency_name = currency_map.get(
                order.currency_id.name, order.currency_id.name or 'pesos'
            )
            order.total_letras = amount_to_words(order.amount_total, currency_name)

    def _get_date_format(self, dt_value):
        """
        Formatear una fecha/datetime en formato legible en español.
        Ejemplo: 'miércoles, 11 de marzo de 2026'

        :param dt_value: Fecha o datetime a formatear
        :type dt_value: datetime or date or False
        :return: Fecha formateada en español
        :rtype: str
        """
        if not dt_value:
            return ''
        # Convertir datetime a date si es necesario
        if hasattr(dt_value, 'date'):
            # Convertir a zona horaria del usuario si es datetime
            user_tz = self.env.user.tz or 'UTC'
            try:
                import pytz
                local_tz = pytz.timezone(user_tz)
                dt_value = dt_value.astimezone(local_tz)
            except Exception:
                pass
            date_val = dt_value.date()
        else:
            date_val = dt_value

        dia_semana = DIAS_SEMANA.get(date_val.weekday(), '')
        dia = date_val.day
        mes = MESES.get(date_val.month, '')
        anio = date_val.year
        return f"{dia_semana.capitalize()}, {dia} de {mes.capitalize()} de {anio}"
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
