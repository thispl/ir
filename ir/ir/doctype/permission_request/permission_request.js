// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Permission Request", {
	permission_request_hours(frm){
		if(frm.doc.shift){
			frm.trigger("shift")
		}
	},
	shift(frm) {
		if (frm.doc.shift) {
			frappe.call({
				"method": "frappe.client.get",
				"args": {
					doctype: "Shift Type",
					filters: {
						name: frm.doc.shift
					},
					fieldname: ["name", "start_time", "end_time"]
				},
				callback(r) {
					frm.set_value("session", 'First Half');
					frm.set_value("from_time", r.message.start_time);
					frm.call('get_endtime1', {
						start_time: r.message.start_time
					}).then((d) => {
						if ((frm.doc.permission_request_hours == '1') && 
							(frm.doc.employee_category == "White Collar" || frm.doc.employee_category == "Grey Collar")) {
							frm.set_value("to_time", moment(d.message, 'HH:mm').subtract(1, 'hour').format('HH:mm'));
						} 
						else if (frm.doc.employee_category == "Blue Collar") {
							frm.set_value("to_time", moment(d.message, 'HH:mm').subtract(1, 'hour').format('HH:mm'));
						} 
						else {
							frm.set_value("to_time", d.message);
						}
					});
				}
			});
		}
	},
	
	session(frm) {
		if (frm.doc.shift) {
			if (frm.doc.session == 'Second Half') {
				frappe.call({
					"method": "frappe.client.get",
					"args": {
						doctype: "Shift Type",
						filters: {
							name: frm.doc.shift
						},
						fieldname: ["name", "start_time", "end_time"],
					},
					callback(r) {
						let currentDay = moment(frm.doc.attendance_date).format('dddd');
						if ((currentDay === 'Saturday' || currentDay === 'Sunday') && frm.doc.shift === 'G'){
							frm.set_value("to_time", moment(r.message.end_time, 'HH:mm').subtract(30, 'minute').format('HH:mm'))
							frm.call('get_endtime2', {
								end_time: moment(r.message.end_time, 'HH:mm:ss').subtract(30, 'minute').format('HH:mm:ss')
							}).then((d) => {
								if ((frm.doc.permission_request_hours == '1') && 
								(frm.doc.employee_category == "White Collar" || frm.doc.employee_category == "Grey Collar")) {
								frm.set_value("from_time", moment(d.message, 'HH:mm').add(1, 'hour').format('HH:mm'));
							} 
							else if(frm.doc.employee_category=="Blue Collar")
									frm.set_value("from_time", moment(d.message, 'HH:mm').add(1, 'hour').format('HH:mm'));
							else{
									frm.set_value("from_time", d.message)
								}
							})
						}
						else{
						frm.set_value("to_time", r.message.end_time)
						frm.call('get_endtime2', {
							end_time: r.message.end_time
						}).then((d) => {
							if ((frm.doc.permission_request_hours == '1') && 
							(frm.doc.employee_category == "White Collar" || frm.doc.employee_category == "Grey Collar")) {
							frm.set_value("from_time", moment(d.message, 'HH:mm').add(1, 'hour').format('HH:mm'));
						} 
						else if(frm.doc.employee_category=="Blue Collar")
								frm.set_value("from_time", moment(d.message, 'HH:mm').add(1, 'hour').format('HH:mm'));
						else{
								frm.set_value("from_time", d.message)
							}
						})
						}
					}
				})
			}
			else {
				frm.trigger('shift')
			}
		}
	}
});