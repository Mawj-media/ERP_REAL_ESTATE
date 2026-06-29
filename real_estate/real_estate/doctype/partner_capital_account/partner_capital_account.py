from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PartnerCapitalAccount(Document):
    def before_save(self):
        self._compute_balance()

    def on_submit(self):
        self._update_project_partner_contributions()

    def on_cancel(self):
        self._update_project_partner_contributions()

    def _compute_balance(self):
        if not self.partner:
            return

        rows = frappe.db.get_all(
            "Partner Capital Account",
            filters={
                "partner": self.partner,
                "docstatus": 1,
                "name": ["!=", self.name],
            },
            pluck="partner_balance_after",
            order_by="transaction_date desc, creation desc",
            limit=1,
        )
        prior_balance = flt(rows[0]) if rows else 0

        self.partner_balance_after = prior_balance + flt(self.amount)

    def _update_project_partner_contributions(self):
        if not self.real_estate_project:
            return

        project = frappe.get_doc("Real Estate Project", self.real_estate_project)
        if not project.partner_shares:
            return

        for share in project.partner_shares:
            if share.partner != self.partner:
                continue

            rows = frappe.db.get_all(
                "Partner Capital Account",
                filters={
                    "partner": self.partner,
                    "real_estate_project": self.real_estate_project,
                    "docstatus": 1,
                    "transaction_type": "Capital Contribution",
                },
                pluck="amount",
            )
            total_contributed = sum(flt(r) for r in rows)

            share.capital_contributed = total_contributed
            share.db_update()
            break


@frappe.whitelist()
def distribute_project_profit(project_name, profit_amount):
    """Distribute net profit to partners based on their share percentages."""
    project = frappe.get_doc("Real Estate Project", project_name)
    if not project.partner_shares:
        return

    total_share = sum(
        flt(s.share_percentage) for s in project.partner_shares
    )
    if total_share <= 0:
        frappe.throw("Partner shares not configured for this project.")

    profit = flt(profit_amount)

    for share in project.partner_shares:
        partner_amount = profit * flt(share.share_percentage) / total_share
        if partner_amount == 0:
            continue

        entry = frappe.get_doc(
            {
                "doctype": "Partner Capital Account",
                "partner": share.partner,
                "real_estate_project": project_name,
                "transaction_date": frappe.utils.today(),
                "transaction_type": "Profit Allocation",
                "amount": partner_amount,
                "remarks": f"Profit distribution for {project.project_name}",
            }
        )
        entry.flags.ignore_permissions = True
        entry.insert()
        entry.submit()

    return True
