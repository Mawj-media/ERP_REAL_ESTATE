from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt, add_days, today, nowdate


class Booking(Document):
    def before_save(self):
        self._set_base_sale_value()
        self._populate_installments_from_template()
        self._validate_unit_availability()

    def on_submit(self):
        self._set_unit_status("Booked")
        self._create_invoice_for_pending_installments()
        self._update_project_sales_value()
        self._create_broker_commission()

    def cancel(self):
        for si_name in frappe.get_all("Sales Invoice", {"custom_booking": self.name}, pluck="name"):
            frappe.db.set_value("Sales Invoice", si_name, "custom_booking", None)
        for pe_name in frappe.get_all("Payment Entry", {"custom_booking": self.name}, pluck="name"):
            frappe.db.set_value("Payment Entry", pe_name, "custom_booking", None)
        super().cancel()

    def on_cancel(self):
        self._cancel_broker_commission()
        self._cancel_linked_payment_entries()
        self._cancel_linked_sales_invoices()
        self._clear_unit_handover_reference()
        self._set_unit_status("Available")
        self._set_cancellation_metadata()
        self._update_project_sales_value()

    def _set_base_sale_value(self):
        if not self.base_sale_value and self.sale_value:
            company = frappe.db.get_value(
                "Unit", self.unit, "real_estate_project"
            )
            if company:
                project_company = frappe.db.get_value(
                    "Real Estate Project", company, "company"
                )
                if project_company:
                    self.base_sale_value = self.sale_value

    def _populate_installments_from_template(self):
        if self.installments or not self.payment_plan_template:
            return

        template = frappe.get_doc("Payment Plan Template", self.payment_plan_template)
        if not template.installment_milestones:
            return

        booking_date = self.booking_date or today()

        for milestone in template.installment_milestones:
            amount = flt(self.sale_value) * flt(milestone.percentage) / 100
            due_date = (
                add_days(booking_date, milestone.days_from_booking)
                if milestone.days_from_booking
                else booking_date
            )

            self.append(
                "installments",
                {
                    "milestone_label": milestone.milestone_label,
                    "percentage": milestone.percentage,
                    "amount": amount,
                    "base_amount": amount,
                    "due_date": due_date,
                    "status": "Pending",
                },
            )

    def _validate_unit_availability(self):
        if self.get("__islocal"):
            unit_status = frappe.db.get_value("Unit", self.unit, "status")
            if unit_status and unit_status not in ("Available",):
                frappe.throw(
                    f"Unit {self.unit} is already {unit_status}. "
                    "Please select an available unit."
                )

    def _set_unit_status(self, status):
        if not self.unit:
            return
        unit = frappe.get_doc("Unit", self.unit)
        unit.status = status
        unit.save(ignore_permissions=True)

    def _create_invoice_for_pending_installments(self):
        for installment in self.installments:
            if installment.status == "Paid" or installment.sales_invoice:
                continue
            self._create_sales_invoice(installment)
        for installment in self.installments:
            if installment.sales_invoice:
                frappe.db.set_value("Booking Installment", installment.name, {
                    "sales_invoice": installment.sales_invoice,
                    "status": "Pending",
                })

    def _create_sales_invoice(self, installment):
        company = self._get_project_company()
        if not company:
            return

        income_account = frappe.get_cached_value(
            "Company", company, "default_income_account"
        )
        cost_center = frappe.get_cached_value("Company", company, "cost_center")
        item_name = f"Unit Sale - {self.unit}"

        si = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "customer": self.customer,
                "posting_date": installment.due_date or nowdate(),
                "due_date": installment.due_date or nowdate(),
                "company": company,
                "cost_center": cost_center,
                "custom_real_estate_project": self.real_estate_project,
                "custom_booking": self.name,
                "items": [
                    {
                        "item_code": self._get_sale_item(),
                        "item_name": item_name,
                        "description": f"{installment.milestone_label} - Booking {self.name}",
                        "qty": 1,
                        "rate": installment.amount,
                        "amount": installment.amount,
                        "income_account": income_account,
                        "cost_center": cost_center,
                    }
                ],
            }
        )

        si.flags.ignore_permissions = True
        si.flags.from_real_estate = True
        si.insert()
        si.submit()

        installment.sales_invoice = si.name
        installment.status = "Pending"

    def _get_sale_item(self):
        try:
            item_code = frappe.db.get_single_value(
                "Real Estate Settings", "default_sale_item"
            )
            if item_code:
                return item_code
        except Exception:
            pass

        existing = frappe.db.get_value(
            "Item", {"item_name": "Unit Sale"}, "name"
        )
        if existing:
            return existing

        return frappe.db.get_value("Item", {}, "name")

    def _get_project_company(self):
        if not self.real_estate_project:
            return None
        return frappe.db.get_value(
            "Real Estate Project", self.real_estate_project, "company"
        )

    def _set_cancellation_metadata(self):
        self.db_set("cancellation_date", today())
        self.db_set("status", "Cancelled")

    def _cancel_broker_commission(self):
        commission_name = frappe.db.exists(
            "Broker Commission", {"booking": self.name, "docstatus": 1}
        )
        if not commission_name:
            return

        commission = frappe.get_doc("Broker Commission", commission_name)
        commission.cancel()
        commission.db_set("status", "Cancelled")
        frappe.db.set_value("Broker Commission", commission_name, "booking", None)

    def _cancel_linked_sales_invoices(self):
        for installment in self.installments:
            if installment.sales_invoice and frappe.db.exists(
                "Sales Invoice", installment.sales_invoice
            ):
                si = frappe.get_doc("Sales Invoice", installment.sales_invoice)
                if si.docstatus == 1:
                    si.cancel()
                frappe.db.set_value(
                    "Sales Invoice", si.name, "custom_booking", None
                )

    def _cancel_linked_payment_entries(self):
        for installment in self.installments:
            if installment.payment_entry and frappe.db.exists(
                "Payment Entry", installment.payment_entry
            ):
                pe = frappe.get_doc("Payment Entry", installment.payment_entry)
                if pe.docstatus == 1:
                    pe.cancel()
                frappe.db.set_value(
                    "Payment Entry", pe.name, "custom_booking", None
                )

    def _clear_unit_handover_reference(self):
        handover = frappe.db.get_value(
            "Unit Handover", {"booking": self.name, "docstatus": ["!=", 1]}, "name"
        )
        if handover:
            frappe.db.set_value("Unit Handover", handover, "booking", None)

    def _create_broker_commission(self):
        if not self.broker:
            return

        existing = frappe.db.exists(
            "Broker Commission", {"booking": self.name}
        )
        if existing:
            return

        commission = frappe.get_doc(
            {
                "doctype": "Broker Commission",
                "naming_series": "BC-",
                "booking": self.name,
                "commission_date": self.booking_date,
                "sale_value": self.sale_value,
                "commission_rate": self.broker_commission_rate or 0,
                "status": "Accrued",
            }
        )
        commission.flags.ignore_permissions = True
        commission.insert()
        commission.submit()

    def _update_project_sales_value(self):
        if not self.real_estate_project:
            return

        total = frappe.db.get_all(
            "Booking",
            filters={
                "real_estate_project": self.real_estate_project,
                "docstatus": 1,
                "status": ["!=", "Cancelled"],
            },
            pluck="sale_value",
        )
        grand_total = sum(flt(t) for t in total)

        project = frappe.get_doc("Real Estate Project", self.real_estate_project)
        project.total_sales_value = grand_total
        project.db_update()
