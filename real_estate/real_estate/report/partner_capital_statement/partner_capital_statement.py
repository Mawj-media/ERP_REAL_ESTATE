from __future__ import annotations

import frappe


def execute(filters=None):
    columns = [
        {"label": "Date", "fieldname": "transaction_date", "fieldtype": "Date", "width": 100},
        {"label": "Partner", "fieldname": "partner", "fieldtype": "Data", "width": 150},
        {"label": "Transaction Type", "fieldname": "transaction_type", "fieldtype": "Data", "width": 160},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 140},
        {"label": "Running Balance", "fieldname": "partner_balance_after", "fieldtype": "Currency", "width": 140},
        {"label": "Reference", "fieldname": "reference_journal_entry", "fieldtype": "Link", "options": "Journal Entry", "width": 150},
        {"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 200},
    ]

    conditions = "docstatus = 1"
    params = []

    if filters:
        partner = filters.get("partner")
        project = filters.get("real_estate_project")

        if partner:
            conditions += " AND partner = %s"
            params.append(partner)
        if project:
            conditions += " AND real_estate_project = %s"
            params.append(project)

    data = frappe.db.sql(f"""
        SELECT
            transaction_date,
            partner,
            (SELECT partner_name FROM `tabPartner` WHERE name = pca.partner) AS partner_name,
            transaction_type,
            amount,
            partner_balance_after,
            reference_journal_entry,
            remarks
        FROM `tabPartner Capital Account` pca
        WHERE {conditions}
        ORDER BY partner, transaction_date ASC, creation ASC
    """, params, as_dict=True)

    for row in data:
        row["partner"] = row.pop("partner_name", None) or row.get("partner", "")

    return columns, data
