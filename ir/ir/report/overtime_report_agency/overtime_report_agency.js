// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.query_reports["Overtime Report Agency"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			on_change: function () {
				var from_date = frappe.query_report.get_filter_value('from_date')
				frappe.call({
					method: "ir.utils.get_to_date",
					args: {
						from_date: from_date
					},
					callback(r) {
						frappe.query_report.set_filter_value('to_date', r.message);
						frappe.query_report.refresh();
					}
				})
			}
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": () => {
				return {
					filters: {
						'employment_type': 'Agency'
					}
				};
			}

		},
		{
			"fieldname":"agency_name",
			"label": __("Agency"),
			"fieldtype": "Link",
			"options": "Agency",
		},
	],
	onload: function (report) {
		var to_date = frappe.query_report.get_filter('to_date');
		to_date.refresh();
		var from_date = frappe.query_report.get_filter('from_date');
		from_date.refresh();
		var previous_month_end_date = frappe.datetime.add_months(frappe.datetime.month_end(),0);
    	to_date.set_input(previous_month_end_date);
		var previous_month_start_date = frappe.datetime.add_months(frappe.datetime.month_start(),0);
    	from_date.set_input(previous_month_start_date);
	}
};
