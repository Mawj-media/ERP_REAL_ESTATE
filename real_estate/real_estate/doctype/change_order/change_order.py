from __future__ import annotations

import frappe
from frappe.model.document import Document


class ChangeOrder(Document):
    def before_save(self):
        if self.original_amount is not None and self.change_amount is not None:
            self.revised_amount = self.original_amount + self.change_amount
