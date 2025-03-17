// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Regularize", {
	validate(frm){
		if (frm.doc.corrected_in && frm.doc.in_time==1){
			const inTime = new Date(frm.doc.corrected_in);
  			const attendanceDate = new Date(frm.doc.attendance_date);
			const inTimeDate = new Date(inTime.toDateString());
			const timeDifference = inTimeDate - attendanceDate;
			const daysDifference = timeDifference / (1000 * 60 * 60 * 24);
			if (daysDifference >= 1){
				frappe.msgprint(__("Kindly check the corrected in time"));
            	frappe.validated = false;
					
			}
			
		}
		if (frm.doc.corrected_out && frm.doc.out_time==1){
			const outTime = new Date(frm.doc.corrected_out);
  			const attendanceDate = new Date(frm.doc.attendance_date);
			const outTimeDate = new Date(outTime.toDateString());
			const timeDifference = outTimeDate - attendanceDate;
			const daysDifference = timeDifference / (1000 * 60 * 60 * 24);
			if (daysDifference >= 1){
				frappe.msgprint(__("Kindly check the corrected out time"));
            	frappe.validated = false;
				
			}
			
			
		}
	},
	attendance_date(frm){
		frappe.call({
			method: 'ir.ir.doctype.regularize.regularize.validate_regularize_duplication',
			args:{
				'employee':frm.doc.employee,
				'att_date':frm.doc.attendance_date,
				'name':frm.doc.name
			},
			callback(r){
				if(r.message=='Already Applied'){
				frappe.validated=false;
				frappe.msgprint(`The Attendance Regularize document already exists for this employee <b>${frm.doc.employee}</b> for the date  <b>${frappe.datetime.str_to_user(frm.doc.attendance_date)}</b>`);
			}
		}

		})
		if(frm.doc.employment_type =="Agency"){
			frappe.call({
				method:'ir.ir.doctype.regularize.regularize.get_assigned_shift_details',
				args:{
					emp:frm.doc.employee,
					att_date:frm.doc.attendance_date
				},
				callback(r){
					$.each(r.message,function(i,v){
						frm.set_value('attendance_shift',v.attendance_shift)
						if (v.first_in_time){
							frm.set_value('first_in_time',v.first_in_time)
						}
						if (v.last_out_time){
							frm.set_value('last_out_time',v.last_out_time)
						}
						if (v.attendance_shift) {
							frm.set_value('corrected_shift',v.attendance_shift)
						}
						if (v.ot_hrs){
							frm.set_value('extra_time',v.ot_hrs)
						}
						else{
							frm.set_value('corrected_shift', '')
						}
						const date = new Date();
						const year = date.getFullYear();
						const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based, so add 1
						const day = String(date.getDate()).padStart(2, '0');
						const hours = String(date.getHours()).padStart(2, '0');
						const minutes = String(date.getMinutes()).padStart(2, '0');
						const seconds = String(date.getSeconds()).padStart(2, '0');
						const formattedDateTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
						if (v.first_in_time != ' ') {
							frm.set_value('corrected_in',v.first_in_time)
						}
						else{
							frm.set_value('corrected_in', formattedDateTime)
						}
						if (v.last_out_time != ' ') {
							frm.set_value('corrected_out',v.last_out_time)
						}
						else{

							frm.set_value('corrected_out', formattedDateTime)
						}
						frm.set_value('attendance_marked', v.attendance_marked);
					})
				},
				
			})
		}
	},
	
});
