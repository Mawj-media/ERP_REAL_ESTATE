from __future__ import annotations

import csv
import io

import frappe
from frappe import _

from real_estate.real_estate.utils.bulk_import_payments import (
    _normalize_unit,
    _process_row,
)

TEMPLATE_HEADERS = [
    "customer",
    "booking",
    "amount",
    "payment_date",
    "mode_of_payment",
    "ref_no",
    "ref_date",
    "project",
]


@frappe.whitelist()
def download_template():
    frappe.response["filename"] = "customer_payments_template.csv"
    frappe.response["filecontent"] = _generate_template_csv()
    frappe.response["content_type"] = "text/csv"
    frappe.response["type"] = "binary"


def _generate_template_csv() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(TEMPLATE_HEADERS)
    writer.writerow([
        "NAILA BADRUDDIN",
        "G-0001",
        "500000",
        "2026-01-15",
        "Bank",
        "CHQ-001",
        "2026-01-14",
        "RE-00001",
    ])
    return output.getvalue()


@frappe.whitelist()
def preview_csv():
    file_url = frappe.local.form_dict.get("file_url")
    if not file_url:
        frappe.throw(_("No file selected"))

    _file = frappe.get_doc("File", {"file_url": file_url})
    content = _file.get_content()
    reader = csv.DictReader(io.StringIO(content))

    rows = []
    for row in reader:
        if not any(v.strip() if v else "" for v in row.values()):
            continue
        r = {k: v.strip() if v else "" for k, v in row.items()}
        unit_raw = r.get("booking", "").replace(" ", "")
        if unit_raw:
            normalized = _normalize_unit(unit_raw)
            booking = frappe.db.get_value(
                "Booking",
                {"unit": normalized, "docstatus": 1, "status": ["!=", "Cancelled"]},
                ["name", "customer"],
                as_dict=True,
            )
            if booking:
                r["__booking_status"] = "Found"
            else:
                r["__booking_status"] = f"Not Found (normalized: {normalized})"
        else:
            r["__booking_status"] = "Missing"
        rows.append(r)

    return {
        "columns": TEMPLATE_HEADERS,
        "rows": rows,
        "count": len(rows),
    }


@frappe.whitelist()
def import_csv():
    file_url = frappe.local.form_dict.get("file_url")
    if not file_url:
        frappe.throw(_("No file selected"))

    _file = frappe.get_doc("File", {"file_url": file_url})
    content = _file.get_content()
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        frappe.throw(_("CSV file is empty"))

    stats = {"processed": 0, "skipped": 0, "errors": []}

    for i, row in enumerate(rows, start=1):
        if not any(v.strip() if v else "" for v in row.values()):
            stats["skipped"] += 1
            continue
        try:
            _process_row(row, company_override=None)
            stats["processed"] += 1
        except Exception as e:
            stats["errors"].append(f"Row {i}: {e}")
            stats["skipped"] += 1

    return stats
