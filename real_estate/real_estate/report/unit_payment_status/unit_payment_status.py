from __future__ import annotations

import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 180},
        {"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 100},
        {"label": "Sale Value", "fieldname": "sale_value", "fieldtype": "Currency", "width": 130},
        {"label": "Total Paid", "fieldname": "total_paid", "fieldtype": "Currency", "width": 130},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 130},
        {"label": "Current Phase", "fieldname": "current_phase", "fieldtype": "Data", "width": 150},
    ]

    conditions = []
    condition_params = {}

    if filters:
        if filters.get("real_estate_project"):
            conditions.append("bk.real_estate_project = %(project)s")
            condition_params["project"] = filters["real_estate_project"]
        if filters.get("customer"):
            conditions.append("bk.customer = %(customer)s")
            condition_params["customer"] = filters["customer"]

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = """
        SELECT
            bk.name AS booking_name,
            bk.customer,
            cu.customer_name,
            u.unit_number AS unit,
            bk.sale_value,
            COALESCE(SUM(inst.paid_amount), 0) AS total_paid,
            COALESCE(SUM(CASE
                WHEN LOWER(inst.milestone_label) LIKE %(dp_like)s OR LOWER(inst.milestone_label) LIKE %(dp_like2)s
                THEN inst.outstanding ELSE 0
            END), 0) AS dp_outstanding,
            COALESCE(SUM(CASE
                WHEN LOWER(inst.milestone_label) LIKE %(m_like)s OR LOWER(inst.milestone_label) LIKE %(m_like2)s
                THEN inst.outstanding ELSE 0
            END), 0) AS monthly_outstanding,
            COALESCE(SUM(CASE
                WHEN LOWER(inst.milestone_label) LIKE %(p_like)s
                THEN inst.outstanding ELSE 0
            END), 0) AS possession_outstanding
        FROM
            `tabBooking` bk
        INNER JOIN `tabUnit` u ON u.name = bk.unit
        LEFT JOIN `tabCustomer` cu ON cu.name = bk.customer
        LEFT JOIN `tabBooking Installment` inst ON inst.parent = bk.name AND inst.parenttype = 'Booking'
        WHERE
            bk.docstatus = 1
            AND bk.status != 'Cancelled'
            AND {where_clause}
        GROUP BY
            bk.name
        ORDER BY
            cu.customer_name ASC
    """

    params = {
        "dp_like": "%down%",
        "dp_like2": "%downpayment%",
        "m_like": "%installment%",
        "m_like2": "%monthly%",
        "p_like": "%possession%",
        **condition_params,
    }

    bookings = frappe.db.sql(query.format(where_clause=where_clause), params, as_dict=True)

    data = []
    for row in bookings:
        total_paid = flt(row.total_paid)
        sale_value = flt(row.sale_value)
        balance = sale_value - total_paid

        dp_outstanding = flt(row.dp_outstanding)
        monthly_outstanding = flt(row.monthly_outstanding)
        possession_outstanding = flt(row.possession_outstanding)

        if dp_outstanding > 0:
            current_phase = "Down Payment"
        elif monthly_outstanding > 0:
            current_phase = "Installments"
        elif possession_outstanding > 0:
            current_phase = "On Possession"
        else:
            current_phase = "Paid Off"

        data.append({
            "customer": row.customer_name or row.customer,
            "unit": row.unit,
            "sale_value": sale_value,
            "total_paid": total_paid,
            "balance": balance,
            "current_phase": current_phase,
        })

    return columns, data
