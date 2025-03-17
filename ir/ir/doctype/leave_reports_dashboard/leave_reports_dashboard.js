// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Reports Dashboard", {
	to_date(frm){
		if (frm.doc.to_date < frm.doc.from_date) {
            frappe.throw(__('The "From Date" cannot be greater than the "To Date"'));
            return; 
        }
	},
	validate(frm){
		if (frm.doc.to_date < frm.doc.from_date) {
            frappe.throw(__('The "From Date" cannot be greater than the "To Date"'));
            frappe.validate = True 
        }
	},
    download(frm){
		if (frm.doc.to_date < frm.doc.from_date) {
            frappe.throw(__('The "From Date" cannot be greater than the "To Date"'));
            return; 
        }
        if (frm.doc.report=='Leave Report'){
            var path="ir.ir.doctype.leave_reports_dashboard.leave_report.download"
            var args='employee=%(employee)s&from_date=%(from_date)s&to_date=%(to_date)s'
        }
        if(path) {
			window.location.href = repl(frappe.request.url +
				'?cmd=%(cmd)s&%(args)s',{
				cmd: path,
				args: args,
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date,
			});
		}
		if (frm.doc.report == 'Bank Statement') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.bank_statement.download_hr_to_accounts";
                var args = "from_date=" + encodeURIComponent(frm.doc.from_date) +
                           "&to_date=" + encodeURIComponent(frm.doc.to_date) +
                           "&employee_category=" + encodeURIComponent(frm.doc.employee_category) +
                           "&bank=" + encodeURIComponent(frm.doc.bank) 
                
                if (path) {
                    window.location.href = frappe.request.url +
                        '?cmd=' + encodeURIComponent(path) +
                        '&' + args;
                }
            }
        }
        if (frm.doc.report == 'PF Report') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.esi_pf.download_esi";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }
        if (frm.doc.report == 'PF Monthly') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.pf_monthly.download_pf_monthly";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }
        if (frm.doc.report == 'ESI Monthly') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.esi_monthly.download_esi_monthly";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }
        if (frm.doc.report == 'Production Incentive') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.production_incentive.download_production_incentive";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }
        if (frm.doc.report == 'Attendance Bonus') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.attendance_bonus.download_attendance_bonus";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }
        if (frm.doc.report == 'Attendance Register') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.attendance_register.download_attendance_register";
                var args = "from_date=" + encodeURIComponent(frm.doc.from_date) +
                           "&to_date=" + encodeURIComponent(frm.doc.to_date) +
                           "&employee=" + encodeURIComponent(frm.doc.employee)
                
                if (path) {
                    window.location.href = frappe.request.url +
                        '?cmd=' + encodeURIComponent(path) +
                        '&' + args;
                }
            }
        }
        if (frm.doc.report == 'Salary Register') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.salary_register.download_salary_register";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }
		
    },
    converted_to_text_file(frm){
        if (frm.doc.report == 'PF Text File') {
            if (frm.doc.from_date && frm.doc.to_date) {
                var path = "ir.ir.doctype.leave_reports_dashboard.esi_pf_text.download_esi_txt";
                var args='from_date=%(from_date)s&to_date=%(to_date)s'
                if(path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s',{
                        cmd: path,
                        args: args,
                        from_date : frm.doc.from_date,
                        to_date : frm.doc.to_date,
                    });
                }
            }
        }

    }
    
});
