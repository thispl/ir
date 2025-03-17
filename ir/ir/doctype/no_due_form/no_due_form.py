# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class NoDueForm(Document):
	def validate(self):
		# self.no_due_clearance
		for n in self.no_due_clearance:
			if n.due_status =='':
				frappe.sendmail(
					recipients = ['jagadeesan.a@groupteampro.com'],
					subject = ('No Due Pending'),
                	header=('No Due Pending'),
					message=""" 
                        Dear Sir ,<br>
                        Kindly find the No Due Form Employee List<br>
                        <table class='table table-bordered'>
                        <tr>
                        <th>Employee ID</th><th>Employee Name</th><th>Department</th>
                        </tr>
                        <tr>
                        <th>%s</th><th>%s</th><th>%s</th>
                        </tr>
                        
                        """%(doc.employee,doc.employee_name,doc.department)
				)
	def on_submit(self):
		frappe.db.set_value("Employee",self.employee,"custom_no_due_clearance",1)
