from __future__ import annotations

import frappe
from frappe.model.document import Document


class ProjectCostBudget(Document):
    def before_save(self):
        seen = set()
        total_budget = 0
        total_actual = 0
        for row in self.budget_lines:
            if row.cost_category in seen:
                frappe.throw(
                    f"Duplicate cost category {row.cost_category} in budget lines."
                )
            seen.add(row.cost_category)
            total_budget += row.budgeted_amount or 0
            total_actual += row.actual_amount or 0
        self.total_budget_amount = total_budget
        self.total_actual_amount = total_actual
        self.total_variance = total_actual - total_budget
