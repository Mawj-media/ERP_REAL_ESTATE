from __future__ import annotations

import frappe
from frappe.model.document import Document


class PaymentPlanTemplate(Document):
    def before_save(self):
        total = sum(
            row.percentage for row in self.installment_milestones if row.percentage
        )
        self.total_percentage = total
        if total != 100:
            frappe.throw(
                f"Installment milestone percentages must total 100%. Current total: {total}%"
            )
