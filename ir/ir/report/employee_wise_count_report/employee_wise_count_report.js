// Copyright (c) 2023, Abdulla P I and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Wise Count Report"] = {
	"filters": [
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.nowdate(),  
			reqd: 1,
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.nowdate(),  
			reqd: 1,
		},
		{
			fieldname: 'employee',
			label: __('Employee'),
			fieldtype: 'Link',
			options: 'Employee',
		},
		{
			fieldname: 'custom_employee_category',
			label: __('Employee Category'),
			fieldtype: 'Link',
			options: 'Employee Category',
		}
	]
};
