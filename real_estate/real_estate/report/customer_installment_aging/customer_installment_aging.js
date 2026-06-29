frappe.query_reports["Customer Installment Aging"] = {
	"filters": [
		{
			"fieldname": "real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project"
		},
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": "\nPending\nOverdue\nPaid\nWaived"
		}
	]
}
