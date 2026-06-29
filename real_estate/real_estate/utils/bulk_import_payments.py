from __future__ import annotations

import csv
import re

import frappe
from frappe.utils import flt, getdate, nowdate


def import_customer_payments(csv_path: str, company: str | None = None):
    """Import customer payments from a CSV file and create submitted Payment Entries.

    Expected CSV columns:
        customer, booking, amount, payment_date, mode_of_payment, ref_no, ref_date, project

    The script:
    1. Looks up the Booking and its unpaid installments
    2. Auto-creates Sales Invoices for installments that don't have one yet
    3. Distributes the payment amount across unpaid installments in order
    4. Creates and submits a Payment Entry with proper Sales Invoice references
    """
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        frappe.msgprint("CSV file is empty or has no data rows.")
        return

    stats = {"processed": 0, "skipped": 0, "errors": []}

    for i, row in enumerate(rows, start=1):
        try:
            _process_row(row, company)
            stats["processed"] += 1
        except Exception as e:
            stats["errors"].append(f"Row {i}: {e}")
            stats["skipped"] += 1

    _print_summary(csv_path, stats)


def _normalize_unit(raw: str) -> str:
    s = raw.replace(" ", "")
    m = re.match(r"^([A-Za-z]+)-(\d+)$", s)
    if m:
        prefix, num = m.group(1), m.group(2)
        return f"{prefix}-{int(num):04d}"
    if s.isdigit():
        return s.zfill(4)
    return s


def _resolve_booking(raw_unit: str):
    normalized = _normalize_unit(raw_unit)
    bookings = frappe.get_all(
        "Booking",
        filters={"unit": normalized, "docstatus": 1, "status": ["!=", "Cancelled"]},
        limit=1,
    )
    if bookings:
        return frappe.get_doc("Booking", bookings[0].name)

    bookings = frappe.get_all(
        "Booking",
        filters={"unit": normalized, "docstatus": 1},
        limit=1,
    )
    if bookings:
        b = frappe.get_doc("Booking", bookings[0].name)
        raise ValueError(
            f"Booking for unit {normalized} (Customer: {b.customer}) is {b.status}"
        )

    if normalized != raw_unit:
        raise ValueError(
            f"No booking found for unit '{raw_unit}' (normalized: '{normalized}')"
        )
    raise ValueError(f"No booking found for unit '{raw_unit}'")


def _get_effective_outstanding(inst) -> float:
    outstanding = flt(inst.outstanding)
    if outstanding > 0:
        return outstanding
    return max(0, flt(inst.amount) - flt(inst.paid_amount))


def _resolve_sale_item() -> str:
    from frappe.model.document import Document

    try:
        settings = frappe.get_single("Real Estate Settings")
        if settings.default_sale_item:
            return settings.default_sale_item
    except Exception:
        pass

    item = frappe.db.get_value("Item", {"item_name": "Unit Sale"}, "name")
    if item:
        return item

    item = frappe.get_all("Item", pluck="name", limit=1)
    if item:
        return item[0]

    raise ValueError(
        "No sale item found. Set default_sale_item in Real Estate Settings "
        "or create an Item named 'Unit Sale'."
    )


def _ensure_sales_invoice(
    customer: str, installment, booking, company: str, posting_date: str
) -> str:
    if installment.sales_invoice:
        si_exists = frappe.db.exists(
            "Sales Invoice", installment.sales_invoice
        )
        if si_exists:
            return installment.sales_invoice

    item_code = _resolve_sale_item()
    outstanding = _get_effective_outstanding(installment)

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "company": company,
        "posting_date": posting_date,
        "due_date": posting_date,
        "currency": frappe.db.get_value("Company", company, "default_currency") or "PKR",
        "items": [
            {
                "item_code": item_code,
                "qty": 1,
                "rate": outstanding,
                "amount": outstanding,
            }
        ],
        "custom_real_estate_project": booking.real_estate_project,
        "custom_booking": booking.name,
    })

    si.flags.ignore_permissions = True
    si.flags.ignore_mandatory = True
    prev = getattr(frappe.flags, "in_import", False)
    frappe.flags.in_import = True
    try:
        si.insert()
    finally:
        frappe.flags.in_import = prev

    if si.docstatus == 0:
        si.submit()

    frappe.db.set_value(
        "Booking Installment", installment.name, "sales_invoice", si.name
    )
    installment.sales_invoice = si.name

    print(f"    \u2713 Created Sales Invoice {si.name} for {customer} (Installment: {installment.name}, {outstanding})")
    return si.name


def _get_installment_priority(inst) -> int:
    label = (inst.milestone_label or "").lower()
    if "down" in label or "downpayment" in label:
        return 1
    if "installment" in label or "monthly" in label:
        return 2
    if "possession" in label:
        return 3
    return 99


def _process_row(row: dict, company_override: str | None):
    customer = row.get("customer", "").strip()
    unit_raw = row.get("booking", "").strip()
    amount = flt(row.get("amount"))
    raw_payment_date = row.get("payment_date", "").strip()
    payment_date = str(getdate(raw_payment_date)) if raw_payment_date else nowdate()
    mode_of_payment = row.get("mode_of_payment", "").strip()
    ref_no = row.get("ref_no", "").strip()
    raw_ref_date = row.get("ref_date", "").strip()
    ref_date = str(getdate(raw_ref_date)) if raw_ref_date else payment_date

    if not customer or not unit_raw or amount <= 0:
        raise ValueError(
            f"Missing required fields: customer='{customer}', booking='{unit_raw}', "
            f"amount={amount}"
        )

    booking = _resolve_booking(unit_raw)

    if booking.customer != customer:
        raise ValueError(
            f"Customer '{customer}' does not match Booking {booking.name}'s "
            f"customer '{booking.customer}'"
        )

    company = company_override or frappe.db.get_value(
        "Real Estate Project", booking.real_estate_project, "company"
    )
    if not company:
        raise ValueError(f"Could not determine company for booking {booking.name}")

    unpaid_installments = [
        inst for inst in booking.installments
        if inst.outstanding != 0 or inst.status != "Paid"
    ]

    if not unpaid_installments:
        raise ValueError(
            f"Booking {booking.name} has no unpaid installments"
        )

    unpaid_installments.sort(key=_get_installment_priority)

    for inst in unpaid_installments:
        _ensure_sales_invoice(customer, inst, booking, company, payment_date)

    si_names = [inst.sales_invoice for inst in unpaid_installments if inst.sales_invoice]
    si_outstanding_map = {}
    if si_names:
        rows = frappe.db.sql("""
            SELECT name, grand_total, outstanding_amount
            FROM `tabSales Invoice`
            WHERE name IN %s
        """, [si_names], as_dict=True)
        for r in rows:
            si_outstanding_map[r.name] = flt(r.outstanding_amount)
            total_paid_via_si = flt(r.grand_total) - flt(r.outstanding_amount)
            inst_for_si = next(
                (inst for inst in unpaid_installments if inst.sales_invoice == r.name),
                None,
            )
            if inst_for_si and inst_for_si.paid_amount != total_paid_via_si:
                new_paid = total_paid_via_si
                new_outstanding = max(0, flt(inst_for_si.amount) - new_paid)
                frappe.db.set_value("Booking Installment", inst_for_si.name, {
                    "paid_amount": new_paid,
                    "outstanding": new_outstanding,
                })
                inst_for_si.paid_amount = new_paid
                inst_for_si.outstanding = new_outstanding

    total_outstanding = sum(
        si_outstanding_map.get(inst.sales_invoice, 0)
        for inst in unpaid_installments
    )

    if amount > total_outstanding:
        frappe.msgprint(
            f"Payment amount {amount} exceeds total outstanding {total_outstanding} "
            f"for Booking {booking.name}. Capping at {total_outstanding}."
        )
        amount = total_outstanding

    if amount <= 0:
        raise ValueError(f"Effective payment amount is 0 for Booking {booking.name}")

    paid_to = _resolve_paid_to(company, mode_of_payment)
    paid_from = _resolve_paid_from(company)
    remaining = amount

    references = []
    allocated_insts = []
    for inst in unpaid_installments:
        if remaining <= 0:
            break
        si_outstanding = si_outstanding_map.get(inst.sales_invoice, 0)
        if si_outstanding <= 0:
            continue
        alloc = min(remaining, si_outstanding)
        references.append({
            "reference_doctype": "Sales Invoice",
            "reference_name": inst.sales_invoice,
            "allocated_amount": alloc,
        })
        allocated_insts.append((inst, alloc))
        remaining -= alloc

    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "party_type": "Customer",
        "party": customer,
        "company": company,
        "paid_amount": amount,
        "received_amount": amount,
        "paid_to": paid_to,
        "paid_from": paid_from,
        "mode_of_payment": mode_of_payment or None,
        "reference_no": ref_no or None,
        "reference_date": ref_date,
        "posting_date": payment_date,
        "custom_real_estate_project": booking.real_estate_project,
        "custom_booking": booking.name,
        "references": references,
    })

    pe.flags.ignore_permissions = True
    pe.insert()
    pe.submit()

    for inst, alloc in allocated_insts:
        new_paid = flt(inst.paid_amount) + alloc
        new_outstanding = max(0, flt(inst.amount) - new_paid)
        new_status = "Paid" if new_outstanding <= 0 else inst.status
        frappe.db.set_value("Booking Installment", inst.name, {
            "paid_amount": new_paid,
            "outstanding": new_outstanding,
            "payment_entry": pe.name,
            "status": new_status,
        })
        inst.paid_amount = new_paid
        inst.outstanding = new_outstanding
        inst.payment_entry = pe.name
        inst.status = new_status

    frappe.db.commit()

    print(f"  \u2713 Payment Entry {pe.name} created for {customer} (Booking {booking.name}): {amount}")


def _resolve_paid_to(company: str, mode_of_payment: str | None) -> str:
    if mode_of_payment:
        accounts = frappe.get_all(
            "Mode of Payment Account",
            filters={"parent": mode_of_payment, "company": company},
            pluck="default_account",
        )
        if accounts:
            return accounts[0]

    default_bank = frappe.db.get_value("Company", company, "default_bank_account")
    if default_bank:
        return default_bank

    cash_account = frappe.db.get_value(
        "Account",
        {"company": company, "account_name": "Cash", "is_group": 0},
        "name",
    )
    if cash_account:
        return cash_account

    raise ValueError(
        f"No payment account found for company {company}. "
        f"Set a default_bank_account on the Company or a Mode of Payment with a default account."
    )


def _resolve_paid_from(company: str) -> str:
    receivable = frappe.db.get_value("Company", company, "default_receivable_account")
    if receivable:
        return receivable

    debtors = frappe.db.get_value(
        "Account",
        {"company": company, "account_name": "Debtors", "is_group": 0},
        "name",
    )
    if debtors:
        return debtors

    raise ValueError(
        f"No receivable account found for company {company}. "
        f"Set a default_receivable_account on the Company record."
    )


def _print_summary(csv_path: str, stats: dict):
    print()
    print("=" * 60)
    print(f"BULK IMPORT SUMMARY: {csv_path}")
    print("=" * 60)
    print(f"  Processed:  {stats['processed']}")
    print(f"  Skipped:    {stats['skipped']}")
    if stats["errors"]:
        print(f"  Errors:")
        for err in stats["errors"]:
            print(f"    - {err}")
    print("=" * 60)
