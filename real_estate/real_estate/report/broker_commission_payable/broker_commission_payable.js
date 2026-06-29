frappe.query_reports["Broker Commission Payable"] = {
	"filters": [
		{
			"fieldname": "real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project"
		},
		{
			"fieldname": "broker",
			"label": "Broker",
			"fieldtype": "Link",
			"options": "Broker"
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": "\nAccrued\nPartially Paid\nPaid\nCancelled"
		}
	]
}
