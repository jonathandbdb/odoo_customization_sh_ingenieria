# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models

# Mapa de nombres de días y meses en español para formateo de fechas
DIAS_SEMANA = {
    0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
    4: 'viernes', 5: 'sábado', 6: 'domingo',
}
MESES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Primera sección del presupuesto (usada en el encabezado/cabecera de archivo)
    sh_first_section_name = fields.Char(
        string="First Section",
        compute="_compute_sh_first_section_name",
    )

    # Primera nota del presupuesto, usada como título central del reporte
    sh_first_note_name = fields.Char(
        string="First Note",
        compute="_compute_sh_first_note_name",
    )

    # Garantía configurable mostrada en las condiciones comerciales del reporte
    sh_warranty = fields.Char(
        string="Garantía",
        default="",
        help="Texto de la garantía aplicable a la cotización.",
    )

    # Aspectos técnicos editables por cotización; se inicializan desde el
    # campo equivalente de la compañía si está configurado.
    sh_technical_aspects = fields.Html(
        string="Technical Aspects",
        help="Texto con los aspectos técnicos específicos de esta cotización.",
    )

    @api.model
    def default_get(self, fields_list):
        """
        Inicializar `sh_technical_aspects` con el valor configurado en la
        compañía. Se hace en `default_get` (en lugar de `default=`) para que
        la lectura de `res.company.sh_technical_aspects` ocurra sólo al crear
        cotizaciones desde la interfaz, evitando errores cuando el campo aún
        no existe en la columna durante actualizaciones de módulo.
        """
        defaults = super().default_get(fields_list)
        if "sh_technical_aspects" in fields_list and not defaults.get("sh_technical_aspects"):
            company = self.env.company
            if company and "sh_technical_aspects" in company._fields:
                defaults["sh_technical_aspects"] = company.sh_technical_aspects
        return defaults

    @api.depends("order_line", "order_line.display_type", "order_line.name", "order_line.sequence")
    def _compute_sh_first_section_name(self):
        """
        Obtener el nombre de la primera sección (display_type='line_section') del
        presupuesto, usado en el encabezado del archivo del reporte.
        """
        for order in self:
            sections = order.order_line.sorted("sequence").filtered(
                lambda l: l.display_type == "line_section"
            )
            order.sh_first_section_name = sections[:1].name if sections else ""

    @api.depends("order_line", "order_line.display_type", "order_line.name", "order_line.sequence")
    def _compute_sh_first_note_name(self):
        """
        Obtener el nombre de la primera nota (display_type='line_note') del
        presupuesto, usada como título central del reporte. Si no hay notas,
        no se imprime título.
        """
        for order in self:
            notes = order.order_line.sorted("sequence").filtered(
                lambda l: l.display_type == "line_note"
            )
            order.sh_first_note_name = notes[:1].name if notes else ""

    def _get_first_note_line_id(self):
        """
        Devolver el ID de la primera línea tipo nota del presupuesto. Se
        utiliza desde el reporte para omitir esa línea dentro de la tabla,
        evitando que aparezca duplicada (ya se muestra como título central).
        """
        self.ensure_one()
        notes = self.order_line.sorted("sequence").filtered(
            lambda l: l.display_type == "line_note"
        )
        return notes[:1].id if notes else False

    def _get_date_format(self, dt_value):
        """
        Formatear una fecha/datetime en formato legible en español.
        Ejemplo: 'Lunes, 9 de Marzo de 2026'

        :param dt_value: Fecha o datetime a formatear
        :type dt_value: datetime or date or False
        :return: Fecha formateada en español
        :rtype: str
        """
        if not dt_value:
            return ''
        if isinstance(dt_value, datetime):
            # Convertir a zona horaria del usuario
            user_tz = self.env.user.tz or 'UTC'
            try:
                import pytz
                local_tz = pytz.timezone(user_tz)
                if dt_value.tzinfo is None:
                    dt_value = pytz.UTC.localize(dt_value)
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

    def _get_date_short(self, dt_value):
        """
        Formatear una fecha en formato corto dd-mm-yyyy para encabezados.

        :param dt_value: Fecha o datetime
        :return: Fecha formateada
        :rtype: str
        """
        if not dt_value:
            return ''
        if isinstance(dt_value, datetime):
            date_val = dt_value.date()
        else:
            date_val = dt_value
        return date_val.strftime('%d-%m-%Y')

    def _get_days_between(self, date_from, date_to):
        """
        Obtener cantidad de días entre dos fechas/datetimes.

        :param date_from: Fecha inicial
        :param date_to: Fecha final
        :return: Cantidad de días como string o ''
        :rtype: str
        """
        if not date_from or not date_to:
            return ''
        # Normalizar ambos a date para evitar mezcla date/datetime
        if isinstance(date_from, datetime):
            date_from = date_from.date()
        if isinstance(date_to, datetime):
            date_to = date_to.date()
        delta = (date_to - date_from).days
        return str(delta) if delta >= 0 else ''

    def _get_section_blocks(self):
        """
        Agrupar las líneas del pedido en bloques por sección, calculando el
        subtotal (Vr. Capítulo) de cada bloque.

        :return: Lista de dicts con estructura:
            [{'section': <line or False>, 'lines': [<line>, ...], 'subtotal': float}]
        :rtype: list
        """
        self.ensure_one()
        blocks = []
        current = {'section': False, 'lines': [], 'subtotal': 0.0}
        for line in self.order_line.sorted("sequence"):
            if line.display_type == "line_section":
                if current['section'] or current['lines']:
                    blocks.append(current)
                current = {'section': line, 'lines': [], 'subtotal': 0.0}
            else:
                current['lines'].append(line)
                if not line.display_type:
                    current['subtotal'] += line.price_subtotal
        if current['section'] or current['lines']:
            blocks.append(current)
        return blocks
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
