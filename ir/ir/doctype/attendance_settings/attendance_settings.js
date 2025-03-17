// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Settings', {
	refresh:function(frm){
		frm.disable_save()
	},
	process_checkins(frm){
		if (frm.doc.employee){
		
			frappe.call({
				"method": "ir.mark_attendance.get_urc_to_ec",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"employee": frm.doc.employee 
				},
				freeze: true,
				freeze_message: 'Processing UnRegistered Employee Checkin to Employee Checkin....',
				callback(r){
					
					if(r.message == "ok"){
						frappe.msgprint("Checkins are created Successfully")
					}
				}
			})
		}
		else{
			
			frappe.call({
				"method": "ir.mark_attendance.enqueue_get_urc_to_ec_without_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date 
				},
				freeze: true,
				freeze_message: 'Processing UnRegistered Employee Checkin to Employee Checkin....',
				callback(r){
					if(r.message == "ok"){
						frappe.msgprint("Checkins are created Successfully")
					}
				}
			})
		}
	},
	process_attendance(frm){
		
		if (frm.doc.employee){
			
			frappe.call({
				"method": "ir.mark_attendance.update_att_with_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"employee": frm.doc.employee 
				},
				freeze: true,
				freeze_message: 'Processing Attendance....',
				callback(r){
				
					if(r.message == "OK"){
						frappe.msgprint("Attendance are created Successfully")
					}
				}
			})
		}
		else if(frm.doc.department && ! frm.doc.employee){
			frappe.call({
				"method": "ir.mark_attendance.enqueue_update_att_with_department",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"department": frm.doc.department
				},
				freeze: true,
				freeze_message: 'Processing Attendance....',
				callback(r){
				
					if(r.message == "OK"){
						frappe.msgprint("Attendance are created Successfully")
					}
				}
			})
		}
		else if(frm.doc.department && frm.doc.employee){
			frappe.call({
				"method": "ir.mark_attendance.enqueue_update_att_with_department_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"department": frm.doc.department,
					"name":frm.doc.employee
				},
				freeze: true,
				freeze_message: 'Processing Attendance....',
				callback(r){
					
					if(r.message == "Ok"){
						frappe.msgprint("Attendance are created Successfully")
					}
				}
			})
		}
		else{
			
			frappe.call({
				"method": "ir.mark_attendance.update_att_without_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date 
				},
				freeze: true,
				freeze_message: 'Processing Attendance....',
				callback(r){
					
					if(r.message == "ok"){
						frappe.msgprint("Attendance are created Successfully")
					}
				}
			})
		}
	}
});

