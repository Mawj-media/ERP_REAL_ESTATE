from __future__ import annotations

import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = [
        {"label": "Broker", "fieldname": "broker", "fieldtype": "Data", "width": 150},
        {"label": "Booking", "fieldname": "booking", "fieldtype": "Link", "options": "Booking", "width": 150},
        {"label": "Commission Amount", "fieldname": "commission_amount", "fieldtype": "Currency", "width": 140},
        {"label": "TDS Amount", "fieldname": "tds_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Net Payable", "fieldname": "net_payable", "fieldtype": "Currency", "width": 140},
        {"label": "Total Paid", "fieldname": "total_paid", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

    conditions = "1=1"
    params = []

    if filters:
        project = filters.get("real_estate_project")
        broker = filters.get("broker")
        status = filters.get("status")

        if project:
            conditions += " AND bc.real_estate_project = %s"
            params.append(project)
        if broker:
            conditions += " AND bc.broker = %s"
            params.append(broker)
        if status:
            conditions += " AND bc.status = %s"
            params.append(status)

    commissions = frappe.db.sql(f"""
        SELECT
            bc.name,
            bc.booking,
            bc.broker,
            bc.commission_amount,
            bc.tds_amount,
            bc.net_payable,
            bc.status
        FROM `tabBroker Commission` bc
        WHERE {conditions}
        ORDER BY bc.commission_date DESC
    """, params, as_dict=True)

    data = []
    for c in commissions:
        payments = frappe.get_all(
            "Commission Payment",
            filters={"parent": c.name, "parenttype": "Broker Commission"},
            pluck="paid_amount",
        )
        total_paid = sum(flt(p) for p in payments)
        broker_name = frappe.db.get_value("Broker", c.broker, "broker_name") if c.broker else ""

        data.append({
            "broker": broker_name or c.broker,
            "booking": c.booking,
            "commission_amount": c.commission_amount,
            "tds_amount": c.tds_amount,
            "net_payable": c.net_payable,
            "total_paid": total_paid,
            "balance": flt(c.net_payable) - total_paid,
            "status": c.status,
        })

    return columns, data
