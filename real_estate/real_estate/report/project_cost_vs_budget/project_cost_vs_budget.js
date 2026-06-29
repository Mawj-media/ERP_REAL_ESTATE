frappe.query_reports["Project Cost vs Budget"] = {
	"filters": [
		{
			"fieldname": "real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project",
			"reqd": 1
		},
		{
			"fieldname": "cost_category",
			"label": "Cost Category",
			"fieldtype": "Link",
			"options": "Cost Category"
		}
	]
}
