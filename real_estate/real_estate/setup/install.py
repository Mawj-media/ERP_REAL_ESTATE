from __future__ import annotations

import frappe
from frappe.utils import nowdate


def after_install():
    create_real_estate_role()
    create_real_estate_accounts()


def after_migrate():
    create_real_estate_role()
    create_real_estate_accounts()


def create_real_estate_role():
    if not frappe.db.exists("Role", "Real Estate User"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "Real Estate User",
            "desk_access": 1,
        }).insert(ignore_permissions=True)


def create_real_estate_accounts():
    companies = frappe.get_all("Company", pluck="name")
    for company in companies:
        _add_accounts_for_company(company)


def _add_accounts_for_company(company):
    currency = frappe.db.get_value("Company", company, "default_currency")

    accounts_to_create = [
        {
            "account_name": "Unit Sales Revenue",
            "parent_account": _get_parent(company, ["Direct Income", "Indirect Income"], "Income"),
            "root_type": "Income",
            "account_type": "Income Account",
            "account_currency": currency,
            "is_group": 0,
        },
        {
            "account_name": "Retention Payable",
            "parent_account": _get_parent(company, ["Current Liabilities", "Current Liability"], "Liability"),
            "root_type": "Liability",
            "account_type": "Payable",
            "account_currency": currency,
            "is_group": 0,
        },
        {
            "account_name": "Broker Commission Payable",
            "parent_account": _get_parent(company, ["Current Liabilities", "Current Liability"], "Liability"),
            "root_type": "Liability",
            "account_type": "Payable",
            "account_currency": currency,
            "is_group": 0,
        },
        {
            "account_name": "Partner Capital",
            "parent_account": _get_parent(company, ["Equity", "Capital"], "Equity"),
            "root_type": "Equity",
            "account_type": "",
            "account_currency": currency,
            "is_group": 1,
        },
    ]

    for acc in accounts_to_create:
        _create_account(company, acc, currency)


def _get_parent(company, parent_names, root_type):
    if isinstance(parent_names, str):
        parent_names = [parent_names]
    for name in parent_names:
        existing = frappe.db.get_value(
            "Account",
            {"company": company, "account_name": name},
            "name",
        )
        if existing:
            return existing
    root = frappe.db.get_value(
        "Account",
        {"company": company, "root_type": root_type, "is_group": 1, "parent_account": ("is", "not set")},
        "name",
    )
    return root


def _create_account(company, spec, currency):
    name = f"{spec['account_name']} - {frappe.db.get_value('Company', company, 'abbr')}"
    if frappe.db.exists("Account", name):
        return

    doc = frappe.get_doc({
        "doctype": "Account",
        "account_name": spec["account_name"],
        "company": company,
        "parent_account": spec["parent_account"],
        "root_type": spec["root_type"],
        "account_type": spec["account_type"],
        "account_currency": currency,
        "is_group": spec["is_group"],
    })
    doc.flags.ignore_permissions = True
    doc.insert()
