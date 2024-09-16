frappe.ui.form.on('On Duty Application', {
	onload: function (frm) {
		if (frm.doc.workflow_state == 'Review Pending') {
			frm.fields_dict.approval_mark.$wrapper.empty();
			frm.fields_dict.html.$wrapper.empty();
		}

			
	},
	validate: function(frm) {
		var multi = frm.doc.multi_employee;
		if (multi.length == 0) {
			frappe.throw('Please choose at least one Employee');
		}
		
	},
	refresh: function (frm) {
		frm.set_df_property('multi_employee', 'cannot_add_rows', true); 
		
		
		frm.ignore_user_permission = false;
		frm.fields_dict.html.$wrapper.empty();
		frm.fields_dict.approval_mark.$wrapper.empty();
		if (!frm.is_new()) {
			if (frm.doc.workflow_state == 'Approved') {
				frm.call('show_html').then(r => {
					frm.fields_dict.html.$wrapper.empty().append(r.message);
				});
			}
		}
		frappe.breadcrumbs.add("HR", "On Duty Application");
		if (!frm.is_new()) {
			if (frm.doc.workflow_state == 'Approved') {
				frm.fields_dict.approval_mark.$wrapper.empty().append('<img src="/files/approved.jpg" alt="Approved" width="300" height="200">');
			}
		}
		if (frm.doc.__islocal) {
			if(frappe.session.user!="Administrator"){
			frappe.call({
				method: 'ir.ir.doctype.on_duty_application.on_duty_application.get_employees',
				args: {}
			}).then(function(r) {
				frm.clear_table('multi_employee');
				frm.set_value("employee", r.message[0]);
				frm.set_value("employee_name", r.message[1]);
				frm.add_child("multi_employee", {
					"employee_id": r.message[0],
					"employee_name": r.message[1],
					"department": r.message[2],
					"designation": r.message[3]
				});
				frm.refresh_field('multi_employee');
				// if (r.message[2]) {
				// 	if (frappe.user.has_role('HOD')) {
				// 		frm.call('get_gm', { department: r.message[2] }).then(r => {
				// 			frm.set_value('approver', r.message);
				// 		});
				// 	} else {
				// 		frm.call('get_hod', { department: r.message[2] }).then(r => {
				// 			frm.set_value('approver', r.message);
				// 		});
				// 	}
				// }
			});
		}
		}
	},
	from_date: function (frm) {
		frm.trigger('validate_cutoff');
		frm.trigger("calculate_total_days");
		// frm.trigger("allowed_from_date");
		if (frm.doc.to_date && frm.doc.from_date) {
			if (frm.doc.from_date != frm.doc.to_date) {
				if (frm.doc.from_date < frm.doc.to_date) {
					frm.trigger("calculate_total_days");
				} else {
					validated = false;
					frappe.msgprint("From Date Must be Lesser than or Equal to To Date");
					frm.set_value("from_date", "");
				}
			}
		}
	},
	to_time: function (frm) {
		frm.trigger("diff_calculation");
	},
	to_date: function (frm) {
		frm.trigger("calculate_total_days");
		frm.trigger("allowed_from_to_date");
		if (frm.doc.from_date && frm.doc.to_date) {
			if (frm.doc.from_date != frm.doc.to_date) {
				if (frm.doc.from_date < frm.doc.to_date) {
					frm.trigger("calculate_total_days");
				} else {
					validated = false;
					frappe.msgprint("To Date Must be Greater than or Equal to From Date");
					frm.set_value("to_date", "");
				}
			}
		}
	},
	from_date_session: function (frm) {
		frm.trigger("calculate_total_days");
	},
	calculate_total_days: function (frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.employee) {
			var date_dif = frappe.datetime.get_diff(frm.doc.to_date, frm.doc.from_date) + 1;
			return frappe.call({
				"method": 'ir.ir.doctype.on_duty_application.on_duty_application.get_number_of_leave_days',
				args: {
					"employee": frm.doc.employee,
					"from_date": frm.doc.from_date,
					"from_date_session": frm.doc.from_date_session,
					"to_date": frm.doc.to_date,
					"date_dif": date_dif
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value('total_number_of_days', r.message);
					}
				}
			});
		}
	},
	diff_calculation: function (frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.employee) {
			frappe.call({
				"method": 'ir.ir.doctype.on_duty_application.on_duty_application.get_time_diff',
				args: {
					"from_time": frm.doc.from_time,
					"to_time": frm.doc.to_time,
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value('od_time', r.message);
					}
				}
			});
		}
	},
	validate: function(frm) {
        if (frm.doc.custom_employe && frm.doc.from_date) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'On Duty Application',
                    filters: [
                        ['custom_employe', '=', frm.doc.custom_employe],
                        ['from_date', '=', frm.doc.from_date],
                        ['workflow_state', '!=', 'Rejected'],
						['docstatus','!=',2]
                        ['name', '!=', frm.doc.name]  // Exclude the current document
                    ],
                    fields: ['name']
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        frappe.msgprint(__('The employee has already applied for On Duty on this date.'));
                        frappe.validated = false;
                    }
					else {
                        // This section handles the case where no applications are found
                        frappe.validated = true;
                    }
                }
            });
        }
    }
});
