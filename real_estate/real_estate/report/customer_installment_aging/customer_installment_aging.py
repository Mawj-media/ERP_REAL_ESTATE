from __future__ import annotations

import frappe
from frappe.utils import flt, nowdate, date_diff


def execute(filters=None):
    columns = [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
        {"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 100},
        {"label": "Milestone", "fieldname": "milestone_label", "fieldtype": "Data", "width": 150},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Paid", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 120},
        {"label": "Days Overdue", "fieldname": "days_overdue", "fieldtype": "Int", "width": 100},
    ]

    conditions = "1=1"
    params = []

    if filters:
        project = filters.get("real_estate_project")
        customer = filters.get("customer")
        status = filters.get("status")

        if project:
            conditions += " AND rep.name = %s"
            params.append(project)
        if customer:
            conditions += " AND bk.customer = %s"
            params.append(customer)
        if status:
            conditions += " AND inst.status = %s"
            params.append(status)

    data = frappe.db.sql(f"""
        SELECT
            bk.customer,
            bk.customer_name,
            u.unit_number AS unit,
            inst.milestone_label,
            inst.due_date,
            inst.amount,
            inst.paid_amount,
            inst.outstanding,
            inst.status,
            bk.name AS booking_name
        FROM
            `tabBooking Installment` inst
        INNER JOIN `tabBooking` bk ON bk.name = inst.parent
        LEFT JOIN `tabUnit` u ON u.name = bk.unit
        LEFT JOIN `tabReal Estate Project` rep ON rep.name = bk.real_estate_project
        WHERE
            {conditions}
        ORDER BY
            inst.due_date ASC
    """, params, as_dict=True)

    today = nowdate()
    for row in data:
        if row.due_date and row.status in ("Pending", "Overdue"):
            row.days_overdue = date_diff(today, row.due_date)
            if row.days_overdue > 0:
                row.status = "Overdue"
        else:
            row.days_overdue = 0

    return columns, data
