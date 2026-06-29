from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class RealEstateProject(Document):
    def before_save(self):
        if not self.total_units:
            self.total_units = frappe.db.count("Unit", {"real_estate_project": self.name})


@frappe.whitelist()
def get_project_pnl(project_name):
    """Compute project-level profit & loss."""
    project = frappe.get_doc("Real Estate Project", project_name)

    bookings = frappe.get_all(
        "Booking",
        filters={
            "real_estate_project": project_name,
            "docstatus": 1,
            "status": ["!=", "Cancelled"],
        },
        pluck="name",
    )

    total_revenue = 0
    for b in bookings:
        paid = frappe.get_all(
            "Booking Installment",
            filters={"parent": b, "parenttype": "Booking"},
            pluck="paid_amount",
        )
        total_revenue += sum(flt(p) for p in paid)

    total_cost = 0
    cost_budgets = frappe.get_all(
        "Project Cost Budget",
        filters={
            "real_estate_project": project_name,
            "docstatus": 1,
        },
        pluck="name",
    )

    for cb in cost_budgets:
        budget = frappe.get_doc("Project Cost Budget", cb)
        total_cost += flt(budget.total_actual_amount)

    pnl = total_revenue - total_cost

    return {
        "project_name": project.project_name,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "net_profit": pnl,
        "profit_margin_percent": (pnl / total_revenue * 100) if total_revenue else 0,
    }
