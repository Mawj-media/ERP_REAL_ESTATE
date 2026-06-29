frappe.query_reports["Unit Payment Status"] = {
	"filters": [
		{
			"fieldname": "real_estate_project",
			"label": __("Real Estate Project"),
			"fieldtype": "Link",
			"options": "Real Estate Project"
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		}
	]
}
