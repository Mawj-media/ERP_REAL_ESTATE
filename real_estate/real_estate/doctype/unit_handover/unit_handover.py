from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class UnitHandover(Document):
    def before_save(self):
        self._compute_financials()

    def on_submit(self):
        self._update_unit_status()

    def on_cancel(self):
        self._update_unit_status("Sold")

    def _compute_financials(self):
        if not self.booking:
            return

        installments = frappe.get_all(
            "Booking Installment",
            filters={"parent": self.booking, "parenttype": "Booking"},
            pluck="paid_amount",
        )

        self.total_amount_paid = sum(flt(p) for p in installments)
        self.balance_due = flt(self.total_consideration) - flt(self.total_amount_paid)

        deposit = flt(self.maintenance_deposit)
        legal = flt(self.legal_charges)
        other = flt(self.other_charges)
        self.grand_total_due = self.balance_due + deposit + legal + other

    def _update_unit_status(self, status="Handed Over"):
        if not self.unit:
            return
        unit = frappe.get_doc("Unit", self.unit)
        unit.status = status
        unit.save(ignore_permissions=True)
