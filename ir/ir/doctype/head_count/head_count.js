// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt
frappe.ui.form.on('Head Count', {
	download: function (frm) {
		   var path = "ir.ir.doctype.head_count.head_count.download"
		   var args = 'from_date=%(from_date)s&to_date=%(to_date)s'
        if (path) {
            window.location.href = repl(frappe.request.url +
				'?cmd=%(cmd)s&%(args)s', {
				cmd: path,
				args: args,
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date
            });
        }
    },
});
