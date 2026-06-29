from __future__ import annotations

import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = [
        {"label": "Cost Category", "fieldname": "cost_category", "fieldtype": "Data", "width": 200},
        {"label": "Budgeted", "fieldname": "budgeted_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Actual", "fieldname": "actual_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Committed", "fieldname": "committed_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Variance", "fieldname": "variance", "fieldtype": "Currency", "width": 140},
        {"label": "% Used", "fieldname": "percent_used", "fieldtype": "Percent", "width": 100},
        {"label": "Contractor", "fieldname": "contractor", "fieldtype": "Data", "width": 150},
    ]

    project = filters.get("real_estate_project") if filters else None
    cost_category_filter = filters.get("cost_category") if filters else None

    if not project:
        return columns, []

    budgets = frappe.get_all(
        "Project Cost Budget",
        filters={"real_estate_project": project, "docstatus": 1},
        pluck="name",
    )

    data = []
    seen_categories = set()

    for budget_name in budgets:
        budget = frappe.get_doc("Project Cost Budget", budget_name)
        for line in budget.budget_lines:
            cat = line.cost_category
            if cost_category_filter and cat != cost_category_filter:
                continue
            if cat in seen_categories:
                continue
            seen_categories.add(cat)

            cat_name = frappe.db.get_value("Cost Category", cat, "category_name") if cat else ""
            budgeted = flt(line.budgeted_amount)
            actual = flt(line.actual_amount)
            committed = flt(line.committed_amount)
            variance = flt(line.variance)
            percent_used = (actual / budgeted * 100) if budgeted else 0
            contractor_name = frappe.db.get_value("Supplier", line.contractor, "supplier_name") if line.contractor else ""

            data.append({
                "cost_category": cat_name or cat,
                "budgeted_amount": budgeted,
                "actual_amount": actual,
                "committed_amount": committed,
                "variance": variance,
                "percent_used": percent_used,
                "contractor": contractor_name,
            })

    return columns, data
