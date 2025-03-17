// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on('Resignation Form', {
	employee(frm){
		if (frm.doc.employee){
			frappe.call({
				'method':'ir.ir.doctype.resignation_form.resignation_form.get_user_details',
				'args':{	
					user_id:frm.doc.reports_to
				},
				callback(r){
					frm.set_value('reporting_to',r.message)
				}
			})
		}
		
	},

	onload(frm){
		if(frm.doc.workfow_state == "Draft"){
			frm.set_df_property('hod_relieving_date','hidden', 1);
		}
	
	}

});

