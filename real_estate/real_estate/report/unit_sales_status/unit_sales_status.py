from __future__ import annotations

import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = [
        {"label": "Unit #", "fieldname": "unit_number", "fieldtype": "Data", "width": 120},
        {"label": "Unit Type", "fieldname": "unit_type", "fieldtype": "Data", "width": 100},
        {"label": "Floor", "fieldname": "floor", "fieldtype": "Data", "width": 80},
        {"label": "Area (Sq Ft)", "fieldname": "area_sqft", "fieldtype": "Float", "width": 100},
        {"label": "Current Price", "fieldname": "current_price", "fieldtype": "Currency", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
        {"label": "Booking Date", "fieldname": "booking_date", "fieldtype": "Date", "width": 100},
        {"label": "Sale Value", "fieldname": "sale_value", "fieldtype": "Currency", "width": 120},
        {"label": "Total Paid", "fieldname": "total_paid", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    conditions = {}
    if filters:
        if filters.get("real_estate_project"):
            conditions["real_estate_project"] = filters["real_estate_project"]
        if filters.get("unit_type"):
            conditions["unit_type"] = filters["unit_type"]
        if filters.get("status"):
            conditions["status"] = filters["status"]

    units = frappe.get_all("Unit", filters=conditions, fields=["*"])

    data = []
    for unit in units:
        row = {
            "unit_number": unit.unit_number,
            "unit_type": unit.unit_type,
            "floor": unit.floor,
            "area_sqft": unit.area_sqft,
            "current_price": unit.current_price,
            "status": unit.status,
            "customer": "",
            "booking_date": "",
            "sale_value": 0,
            "total_paid": 0,
            "balance": 0,
        }

        if unit.status in ("Booked", "Sold", "Handed Over"):
            booking = frappe.db.get_value(
                "Booking",
                {"unit": unit.name, "docstatus": 1, "status": ["!=", "Cancelled"]},
                ["customer", "booking_date", "sale_value", "name"],
                as_dict=True,
            )
            if booking:
                row["customer"] = frappe.db.get_value("Customer", booking.customer, "customer_name")
                row["booking_date"] = booking.booking_date
                row["sale_value"] = booking.sale_value

                installments = frappe.get_all(
                    "Booking Installment",
                    filters={"parent": booking.name, "parenttype": "Booking"},
                    pluck="paid_amount",
                )
                total_paid = sum(flt(p) for p in installments)
                row["total_paid"] = total_paid
                row["balance"] = flt(booking.sale_value) - total_paid

        data.append(row)

    return columns, data
