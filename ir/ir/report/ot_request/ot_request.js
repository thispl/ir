// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.query_reports["OT Request"] = {
	"filters": [
		{
			"label": __("From Date"),
			"fieldname": "from_date",
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"label": __("To Date"),
			"fieldname": "to_date",
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"label": __("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": () => {
				return {
					filters: {
						'employment_type': ['!=', 'Agency']
					}
				};
			}
		},
		{
			"label": __("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": 'Department'
		}
	]
};
