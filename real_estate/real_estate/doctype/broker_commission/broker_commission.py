from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class BrokerCommission(Document):
    def before_save(self):
        self._compute_amounts()
        self._update_status_from_payments()

    def _compute_amounts(self):
        if self.sale_value and self.commission_rate:
            self.commission_amount = flt(self.sale_value) * flt(self.commission_rate) / 100

        if self.commission_amount and self.tds_percent:
            self.tds_amount = flt(self.commission_amount) * flt(self.tds_percent) / 100

        self.net_payable = flt(self.commission_amount) - flt(self.tds_amount)

    def _update_status_from_payments(self):
        total_paid = sum(
            flt(p.paid_amount) for p in self.payment_entries
        )

        if not self.payment_entries or total_paid <= 0:
            self.status = "Accrued"
        elif total_paid >= flt(self.net_payable):
            self.status = "Paid"
        else:
            self.status = "Partially Paid"
