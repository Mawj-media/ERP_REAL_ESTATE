from __future__ import annotations

import frappe
from frappe.utils import flt


def on_payment_entry_submit(payment_entry, method=None):
    """When a Payment Entry is submitted, update linked Booking Installments."""
    _update_booking_installments(payment_entry)


def on_payment_entry_cancel(payment_entry, method=None):
    """When a Payment Entry is cancelled, reset linked Booking Installments."""
    _update_booking_installments(payment_entry, cancelled=True)


def _update_booking_installments(payment_entry, cancelled=False):
    """Find Booking Installments linked via Sales Invoice references and update payment status."""

    for ref in payment_entry.references or []:
        if ref.reference_doctype != "Sales Invoice" or not ref.reference_name:
            continue

        si_name = ref.reference_name

        booking_installments = frappe.db.get_all(
            "Booking Installment",
            filters={"sales_invoice": si_name, "parenttype": "Booking"},
            fields=["name", "amount"],
        )

        if not booking_installments:
            continue

        total_allocated = flt(ref.allocated_amount) if not cancelled else 0
        si_outstanding = flt(
            frappe.db.get_value("Sales Invoice", si_name, "outstanding_amount")
        ) if cancelled else flt(ref.outstanding_amount)

        for inst in booking_installments:
            installment = frappe.get_doc("Booking Installment", inst.name)
            inst_amt = flt(inst.amount)
            if not cancelled:
                installment.paid_amount = min(total_allocated, inst_amt)
                installment.outstanding = inst_amt - installment.paid_amount
            else:
                installment.paid_amount = 0
                installment.outstanding = inst_amt
            installment.payment_entry = (
                None if cancelled else payment_entry.name
            )
            installment.status = (
                "Pending" if cancelled or flt(installment.outstanding) > 0 else "Paid"
            )
            installment.db_update()
