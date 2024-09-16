// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Process Tool", {
	refresh(frm) {
        frm.disable_save()
        frm.add_custom_button(__('Submit'),
			function () {
				frappe.confirm('Are you sure you want to Submit the Attendance?',
                    () => {
                        // action to perform if Yes is selected
                        if(frm.doc.to_date<frm.doc.from_date){
                            frappe.msgprint("Enter Valid To Date")
                        }
                        frappe.call({
                            method: 'ir.ir.doctype.attendance_process_tool.attendance_process_tool.enqueue_create_attendance',
                            args: {
                              'from_date':frm.doc.from_date,
                              'to_date':frm.doc.to_date
                            },
                            freeze: true,
                            freeze_message: 'Submitting Attendance....',
                            callback: function (r) {
                                if (r.message == "OK") {
                                    frappe.msgprint("Attendance Submitted Successfully,Kindly check after sometime")
                                }
                            }
                          });
                          
                    }, () => {
                        // action to perform if No is selected
                    })
    })


	}
});
