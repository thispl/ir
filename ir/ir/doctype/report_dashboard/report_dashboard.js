// Copyright (c) 2024, TEAMPROO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Report Dashboard", {
// 	refresh(frm) {

// 	},
download(frm){
    if (frm.doc.reports == 'Sales Register') {
=
        var path = "ir.ir.doctype.report_dashboard.report_dashboard.download_sales_register_report"
        var args = 'from_date=%(from_date)s&to_date=%(to_date)s'
    }
    if (path) {
        window.location.href = repl(frappe.request.url +
            '?cmd=%(cmd)s&%(args)s', {
            cmd: path_for_todo,
            args: args,
            from_date : frm.doc.from_date,
            to_date:frm.doc.to_date,

        });
    }
}
});
