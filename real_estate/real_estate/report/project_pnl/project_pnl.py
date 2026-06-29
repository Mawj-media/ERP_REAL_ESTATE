from __future__ import annotations

import frappe
from frappe.utils import flt

from real_estate.real_estate.doctype.real_estate_project.real_estate_project import get_project_pnl


def execute(filters=None):
    columns = [
        {"label": "Metric", "fieldname": "metric", "fieldtype": "Data", "width": 250},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 180},
    ]

    project = filters.get("real_estate_project") if filters else None
    if not project:
        return columns, []

    pnl = get_project_pnl(project)

    data = [
        {"metric": "Total Revenue (Paid Installments)", "amount": pnl.get("total_revenue", 0)},
        {"metric": "Total Cost (Budget Actuals)", "amount": pnl.get("total_cost", 0)},
        {"metric": "---", "amount": None},
        {"metric": "Net Profit / Loss", "amount": pnl.get("net_profit", 0)},
        {"metric": "Profit Margin %", "amount": pnl.get("profit_margin_percent", 0)},
    ]

    return columns, data
