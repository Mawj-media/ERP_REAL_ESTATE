from __future__ import annotations

import frappe


def on_sales_invoice_cancel(sales_invoice, method=None):
    """When a Sales Invoice linked to a Booking is cancelled, reset the installment."""

    installments = frappe.db.get_all(
        "Booking Installment",
        {"sales_invoice": sales_invoice.name, "parenttype": "Booking"},
        ["name"],
    )

    if not installments:
        return

    for inst in installments:
        inst_doc = frappe.get_doc("Booking Installment", inst.name)
        inst_doc.sales_invoice = None
        inst_doc.payment_entry = None
        inst_doc.paid_amount = 0
        inst_doc.outstanding = inst_doc.amount
        inst_doc.status = "Pending"
        inst_doc.db_update()
