frappe.query_reports["Unit Sales Status"] = {
	"filters": [
		{
			"fieldname": "real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project"
		},
		{
			"fieldname": "unit_type",
			"label": "Unit Type",
			"fieldtype": "Link",
			"options": "Unit Type"
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": "\nAvailable\nBlocked\nBooked\nSold\nHanded Over"
		}
	]
}
