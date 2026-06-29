from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ProgressClaim(Document):
    def before_save(self):
        self._compute_retention()
        self._compute_totals()
        self._compute_net_payable()

    def on_submit(self):
        self._update_project_cost()

    def on_cancel(self):
        self._update_project_cost()

    def _compute_retention(self):
        if self.amount_certified and self.retention_percentage:
            self.retention_amount = (
                flt(self.amount_certified) * flt(self.retention_percentage) / 100
            )

    def _compute_totals(self):
        self.total_work_completed_amount = flt(self.previous_claimed) + flt(
            self.current_claim_amount
        )
        if self.contract_value:
            self.total_work_completed_percentage = (
                flt(self.total_work_completed_amount) / flt(self.contract_value) * 100
            )

    def _compute_net_payable(self):
        certified = flt(self.amount_certified)
        retention = flt(self.retention_amount)
        released = flt(self.previous_retention_released) + flt(
            self.retention_released_amount
        )
        self.net_payable = certified - retention + released

    def _update_project_cost(self):
        if not self.real_estate_project:
            return

        budget = frappe.db.get_value(
            "Project Cost Budget",
            {
                "real_estate_project": self.real_estate_project,
                "docstatus": 1,
                "approval_status": "Approved",
            },
            "name",
        )

        if not budget or not self.cost_category:
            return

        total_actual = frappe.db.get_all(
            "Purchase Invoice",
            filters={
                "custom_cost_category": self.cost_category,
                "custom_real_estate_project": self.real_estate_project,
                "docstatus": 1,
            },
            pluck="base_total",
        )

        actual_sum = sum(flt(t) for t in total_actual)

        budget_doc = frappe.get_doc("Project Cost Budget", budget)
        for line in budget_doc.budget_lines:
            if line.cost_category == self.cost_category:
                line.actual_amount = actual_sum
                line.variance = actual_sum - flt(line.budgeted_amount)
                line.db_update()
                break
