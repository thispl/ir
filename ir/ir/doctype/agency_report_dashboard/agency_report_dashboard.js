// Copyright (c) 2025, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Agency Report Dashboard", {
	download(frm) {
        if (frm.doc.select == 'Salary Register') {
			var path = "ir.ir.doctype.agency_report_dashboard.salary_register.download"
			var args = 'from_date=%(from_date)s&to_date=%(to_date)s&agency=%(agency)s'
		}
        if (path) {
			
			window.location.href = repl(frappe.request.url +
				'?cmd=%(cmd)s&%(args)s', {
				cmd: path,
				args: args,
				
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date,	
				agency: frm.doc.agency
			});
		}
	},
});
