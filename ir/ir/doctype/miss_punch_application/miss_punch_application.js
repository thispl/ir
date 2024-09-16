// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Miss Punch Application", {
    attendance_date:function(frm) {
		if (frm.doc.__islocal){
			frappe.call({
				'method':'frappe.client.get_value',
				'args':{
					'doctype':'Attendance',
					'filters':{
						'employee':frm.doc.employee,
						'attendance_date':frm.doc.attendance_date,
						'docstatus':['!=', 2]
					},
					'fieldname':['name','in_time','out_time','shift']
				},
				callback(r){
					if(r.message){
						if(r.message.in_time && r.message.out_time){
							frappe.validated=false
                    		frappe.msgprint("Already Available checkins are against this date")
						}
						if(!r.message.in_time && !r.message.out_time){
							frappe.validated=false
                    		frappe.msgprint("There is no checkin or checkout present for this date")
						}
						if(r.message.in_time){
							frm.set_value('in_time',r.message.in_time)
							frm.set_df_property('in_time', 'read_only', 1);
						}
						if(r.message.out_time){
							frm.set_value('out_time',r.message.out_time)
							frm.set_df_property('out_time', 'read_only', 1);
						}
						if(r.message.shift){
							frm.set_value('shift',r.message.shift)
							frm.set_df_property('shift', 'read_only', 1);
						}
						if (!r.message.in_time ) {
							let attendance_date = frm.doc.attendance_date;
							let in_time = `${attendance_date} 00:00:00`;
							frm.set_value('in_time', in_time);
						}
						
						if (!r.message.out_time) {
							let attendance_date = frm.doc.attendance_date;
							let out_time = `${attendance_date} 00:00:00`;
							frm.set_value('out_time', out_time);
						}
						// console.log(r.message)
						
						// 	frm.set_value('in_time',r.message.in_time)
						// 	frm.set_value('out_time',r.message.out_time)
						// 	frm.set_value('shift',r.message.shift)
						
					}
                    if(!r.message.name){
                        frappe.msgprint("There is no attendance for this employee")
                    }
				}
			})
		}
    },
	validate(frm) {

        frappe.call({
            'method':'frappe.client.get_value',
            'args':{
                'doctype':'Attendance',
                'filters':{
                    'employee':frm.doc.employee,
                    'attendance_date':frm.doc.attendance_date
                },
                'fieldname':['name','in_time','out_time','shift']
            },
            callback(r){
                if(!r.message.name){
                    frappe.validated=false
                    frappe.msgprint("There is no attendance for this employee")
                }
				if(r.message.in_time && r.message.out_time){
					frappe.validated=false
					frappe.msgprint("Already Available checkins are against this date")
				}
				if(!r.message.in_time && !r.message.out_time){
					frappe.validated=false
					frappe.msgprint("There is no checkin or checkout present for this date")
				}
            }
        })
	},
});
