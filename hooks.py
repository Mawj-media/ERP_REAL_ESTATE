app_name = "real_estate"
app_title = "Real Estate"
app_publisher = "Your Company"
app_description = "Real Estate Development Management"
app_icon = "fa fa-building"
app_color = "#2c3e50"
app_email = "dev@example.com"
app_license = "MIT"
source_link = "https://github.com/Mawj-media/ERP_REAL_ESTATE"
app_logo_url = "/assets/real_estate/images/logo.svg"
app_home = "/app/real-estate"

develop_version = "0.0.1"

# Apps to ignore from translation
ignore_translatable_strings_from = ["frappe", "erpnext"]

# Doc events for ERPNext integration
doc_events = {
	"Payment Entry": {
		"on_submit": "real_estate.real_estate.doc_events.payment_entry.on_payment_entry_submit",
		"on_cancel": "real_estate.real_estate.doc_events.payment_entry.on_payment_entry_cancel",
	},
	"Sales Invoice": {
		"on_cancel": "real_estate.real_estate.doc_events.sales_invoice.on_sales_invoice_cancel",
	},
}

# Whitelisted API methods
api_whitelist = {
	"GET": [
		"real_estate.real_estate.doctype.real_estate_project.real_estate_project.get_project_pnl",
	],
	"POST": [
		"real_estate.real_estate.doctype.partner_capital_account.partner_capital_account.distribute_project_profit",
	],
}

# Custom fields on ERPNext doctypes
custom_fields = {
	"Sales Invoice": [
		{
			"fieldname": "custom_real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project",
			"insert_after": "project",
			"allow_on_submit": 1,
			"search_index": 1,
		},
		{
			"fieldname": "custom_booking",
			"label": "Booking",
			"fieldtype": "Link",
			"options": "Booking",
			"insert_after": "custom_real_estate_project",
			"allow_on_submit": 1,
			"search_index": 1,
		},
	],
	"Purchase Invoice": [
		{
			"fieldname": "custom_real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project",
			"insert_after": "project",
			"allow_on_submit": 1,
			"search_index": 1,
		},
		{
			"fieldname": "custom_cost_category",
			"label": "Cost Category",
			"fieldtype": "Link",
			"options": "Cost Category",
			"insert_after": "custom_real_estate_project",
			"allow_on_submit": 1,
			"search_index": 1,
		},
		{
			"fieldname": "custom_progress_claim",
			"label": "Progress Claim",
			"fieldtype": "Link",
			"options": "Progress Claim",
			"insert_after": "custom_cost_category",
			"allow_on_submit": 1,
			"search_index": 1,
		},
	],
	"Payment Entry": [
		{
			"fieldname": "custom_real_estate_project",
			"label": "Real Estate Project",
			"fieldtype": "Link",
			"options": "Real Estate Project",
			"insert_after": "project",
			"allow_on_submit": 1,
			"search_index": 1,
		},
		{
			"fieldname": "custom_booking",
			"label": "Booking",
			"fieldtype": "Link",
			"options": "Booking",
			"insert_after": "custom_real_estate_project",
			"allow_on_submit": 1,
			"search_index": 1,
		},
	],
	"Supplier": [
		{
			"fieldname": "custom_is_contractor",
			"label": "Is Contractor",
			"fieldtype": "Check",
			"insert_after": "supplier_type",
		},
		{
			"fieldname": "custom_contractor_category",
			"label": "Contractor Category",
			"fieldtype": "Link",
			"options": "Cost Category",
			"insert_after": "custom_is_contractor",
		},
	],
}

# App lifecycle hooks
after_install = "real_estate.real_estate.setup.install.after_install"
after_migrate = "real_estate.real_estate.setup.install.after_migrate"

# Fixtures
# fixtures = ["Custom Field"]
