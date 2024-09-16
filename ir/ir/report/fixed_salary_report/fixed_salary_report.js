frappe.query_reports["Fixed Salary Report"] = {
	"filters": [
		{
            "fieldname": "employee_number",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options":"Employee",
		},
        {
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options":"Department",
		},
    ]
};
