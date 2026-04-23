# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @api.model
    def _sh_is_co_dian_move(self, move):
        """
        Indica si la factura pertenece al flujo DIAN (Colombia) y ya tiene
        el documento firmado aceptado disponible para empaquetar junto al PDF.

        Se exige además que ``move.name`` esté asignado (no ``False`` ni ``"/"``)
        porque ``_l10n_co_dian_get_attached_document_filename`` aplica un
        ``re.sub`` sobre ``self.name`` y falla con ``TypeError`` si el campo es
        ``False`` (caso típico en facturas recién importadas vía XML sin postear).
        """
        # Validación defensiva: sin nombre secuencial válido no hay nombre de ZIP posible
        move_name = move.name
        if not move_name or not isinstance(move_name, str) or move_name == "/":
            return False
        return (
            getattr(move, "l10n_co_dian_is_enabled", False)
            and bool(move.l10n_co_dian_attachment_id)
        )

    @api.model
    def _sh_build_zip_from_existing(self, move):
        """
        Construye un ir.attachment ZIP a partir del PDF de la factura y del
        documento firmado DIAN ya existentes en el registro. Reutiliza el ZIP
        si ya fue generado previamente para evitar duplicados.
        """
        filename = move._l10n_co_dian_get_attached_document_filename() + ".zip"
        existing = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.move"),
                ("res_id", "=", move.id),
                ("name", "=", filename),
                ("mimetype", "=", "application/zip"),
            ],
            limit=1,
        )
        if existing:
            return existing

        attached_xml = move.l10n_co_dian_attachment_id
        pdf_report = move.invoice_pdf_report_id
        if not attached_xml or not pdf_report:
            return self.env["ir.attachment"]

        zip_content = (attached_xml + pdf_report)._build_zip_from_attachments()
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "raw": zip_content,
                "res_model": "account.move",
                "res_id": move.id,
                "mimetype": "application/zip",
            }
        )

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    @api.model
    def _get_invoice_extra_attachments(self, move):
        """
        En facturas DIAN ya aceptadas devuelve el ZIP combinado (PDF + XML
        firmado) en lugar del PDF suelto, garantizando que el wizard "Enviar"
        y los adjuntos reales del correo se basen en un único ZIP.
        """
        if self._sh_is_co_dian_move(move):
            zip_attachment = self._sh_build_zip_from_existing(move)
            if zip_attachment:
                return zip_attachment
        return super()._get_invoice_extra_attachments(move)

    def _get_placeholder_mail_attachments_data(
        self, move, invoice_edi_format=None, extra_edis=None, pdf_report=None
    ):
        """
        Extiende el comportamiento estándar para proponer el placeholder del
        ZIP (PDF + XML firmado) también en facturas DIAN antes de que el PDF
        haya sido generado.
        """
        results = super()._get_placeholder_mail_attachments_data(
            move,
            invoice_edi_format=invoice_edi_format,
            extra_edis=extra_edis,
            pdf_report=pdf_report,
        )

        if not self._sh_is_co_dian_move(move):
            return results

        filename = move._l10n_co_dian_get_attached_document_filename() + ".zip"
        placeholder_id = f"placeholder_{filename}"

        # Excluir placeholders PDF y el placeholder ZIP duplicado del upstream
        filtered = []
        for item in results:
            item_mime = item.get("mimetype") or ""
            if item.get("id") == placeholder_id:
                continue
            if item_mime == "application/pdf":
                continue
            filtered.append(item)

        # Si el PDF y el XML firmado ya existen, el ZIP real se adjuntará
        # vía _get_invoice_extra_attachments: no hace falta placeholder.
        if move.invoice_pdf_report_id:
            return filtered

        filtered.append(
            {
                "id": placeholder_id,
                "name": filename,
                "mimetype": "application/zip",
                "placeholder": True,
            }
        )
        return filtered

    @api.model
    def _get_mail_params(self, move, move_data):
        """
        Extiende la generación de adjuntos del correo para garantizar que,
        cuando la factura DIAN ya tiene PDF + XML firmado aceptado, se envíe
        el ZIP combinado y se excluyan los PDF/XML sueltos.
        """
        if not self._sh_is_co_dian_move(move):
            return super()._get_mail_params(move, move_data)

        if move_data.get("l10n_co_dian_attached_document"):
            # Caso cubierto por l10n_co_dian (primer envío combinado DIAN+mail)
            return super()._get_mail_params(move, move_data)

        params = super()._get_mail_params(move, move_data)

        zip_attachment = self._sh_build_zip_from_existing(move)
        if not zip_attachment:
            return params

        mail_attachments_widget = move_data.get("mail_attachments_widget") or []
        filename_zip = zip_attachment.name

        # IDs de adjuntos que el usuario dejó marcados en el widget
        kept_ids = set()
        for att_data in mail_attachments_widget:
            if att_data.get("skip"):
                continue
            try:
                kept_ids.add(int(att_data["id"]))
            except (TypeError, ValueError):
                continue

        # Eliminar del correo el PDF y el XML firmado que queden como adjuntos sueltos
        excluded_ids = set()
        if move.invoice_pdf_report_id:
            excluded_ids.add(move.invoice_pdf_report_id.id)
        if move.l10n_co_dian_attachment_id:
            excluded_ids.add(move.l10n_co_dian_attachment_id.id)

        kept_ids -= excluded_ids
        kept_ids.add(zip_attachment.id)

        attachments = []
        seen_names = set()
        for att in self.env["ir.attachment"].browse(list(kept_ids)).exists():
            if att.name in seen_names:
                continue
            attachments.append((att.name, att.raw))
            seen_names.add(att.name)

        # Garantizar el ZIP como único adjunto DIAN final
        attachments = [a for a in attachments if a[0] != filename_zip]
        attachments.append((filename_zip, zip_attachment.raw))

        params["attachments"] = attachments
        return params

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
