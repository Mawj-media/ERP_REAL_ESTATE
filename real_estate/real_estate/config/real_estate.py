from frappe import _


def get_data():
	return [
		{
			"label": _("Real Estate"),
			"icon": "octicon octicon-building",
			"items": [
				{
					"type": "doctype",
					"name": "Real Estate Project",
					"label": _("Projects"),
					"description": _("Manage real estate development projects"),
				},
				{
					"type": "doctype",
					"name": "Unit",
					"label": _("Units"),
					"description": _("Manage building units"),
				},
				{
					"type": "doctype",
					"name": "Unit Type",
					"label": _("Unit Types"),
					"description": _("Configure unit categories"),
				},
				{
					"type": "doctype",
					"name": "Booking",
					"label": _("Bookings"),
					"description": _("Customer unit reservations"),
				},
				{
					"type": "doctype",
					"name": "Payment Plan Template",
					"label": _("Payment Plans"),
					"description": _("Standard installment templates"),
				},
			],
		},
		{
			"label": _("Partners & Brokers"),
			"icon": "octicon octicon-people",
			"items": [
				{
					"type": "doctype",
					"name": "Partner",
					"label": _("Partners"),
					"description": _("Manage project investors"),
				},
				{
					"type": "doctype",
					"name": "Partner Capital Account",
					"label": _("Partner Capital Accounts"),
					"description": _("Track capital contributions and distributions"),
				},
				{
					"type": "doctype",
					"name": "Broker",
					"label": _("Brokers"),
					"description": _("Real estate agents"),
				},
				{
					"type": "doctype",
					"name": "Broker Commission",
					"label": _("Broker Commissions"),
					"description": _("Commission tracking"),
				},
			],
		},
		{
			"label": _("Costs & Budgets"),
			"icon": "octicon octicon-dollar",
			"items": [
				{
					"type": "doctype",
					"name": "Project Cost Budget",
					"label": _("Cost Budgets"),
					"description": _("Project cost budgets"),
				},
				{
					"type": "doctype",
					"name": "Cost Category",
					"label": _("Cost Categories"),
					"description": _("Expense classification"),
				},
				{
					"type": "doctype",
					"name": "Change Order",
					"label": _("Change Orders"),
					"description": _("Budget variations"),
				},
				{
					"type": "doctype",
					"name": "Progress Claim",
					"label": _("Progress Claims"),
					"description": _("Contractor payment applications"),
				},
			],
		},
		{
			"label": _("Handover"),
			"icon": "octicon octicon-check",
			"items": [
				{
					"type": "doctype",
					"name": "Unit Handover",
					"label": _("Unit Handovers"),
					"description": _("Final unit transfer to buyers"),
				},
			],
		},
		{
			"label": _("Reports"),
			"icon": "octicon octicon-report",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Unit Payment Status",
					"label": _("Unit Payment Status"),
					"description": _("Customer payment status by unit"),
					"doctype": "Booking",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Unit Sales Status",
					"label": _("Unit Sales Status"),
					"description": _("Unit availability and sales status"),
					"doctype": "Unit",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customer Installment Aging",
					"label": _("Installment Aging"),
					"description": _("Overdue installment tracking"),
					"doctype": "Booking",
				},
			],
		},
		{
			"label": _("Tools"),
			"icon": "octicon octicon-tools",
			"items": [
				{
					"type": "page",
					"name": "bulk-import-payments",
					"label": _("Bulk Import Payments"),
					"description": _("Import customer payments from CSV"),
				},
			],
		},
	]
