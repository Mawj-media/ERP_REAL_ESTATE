from __future__ import annotations

import frappe
from frappe.model.document import Document


class UnitPriceRevision(Document):
    def before_save(self):
        if not self.old_price:
            self.old_price = frappe.db.get_value("Unit", self.unit, "current_price")
