// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Compensatory Off Request", {
	refresh(frm) {

	},
    calculate_total_days: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date) {
			let from_date = Date.parse(frm.doc.from_date);
			let to_date = Date.parse(frm.doc.to_date);

			if (to_date < from_date) {
				frappe.msgprint(__("To Date cannot be less than From Date"));
				frm.set_value("to_date", "");
				return;
			}
			return frappe.call({
				method: "ir.ir.doctype.compensatory_off_request.compensatory_off_request.get_number_of_leave_days",
				args: {
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"half_day": frm.doc.half_day,
					"half_day_date": frm.doc.half_day_date,
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value("total_leave_days", r.message);
					}
				}
			});
		}
	},
    half_day: function(frm) {
		if (frm.doc.half_day) {
			if (frm.doc.from_date == frm.doc.to_date) {
				frm.set_value("half_day_date", frm.doc.from_date);
			} 
		} 
		frm.trigger("calculate_total_days");
	},

	from_date: function(frm) {
		frm.trigger("calculate_total_days");
	},

	to_date: function(frm) {
		frm.trigger("calculate_total_days");
	},
});
