# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendanceProcessTool(Document):
	pass


@frappe.whitelist()    
def enqueue_create_attendance(from_date,to_date):
	frappe.enqueue(
		get_attendance, # python function or a module path as string
		queue="long", # one of short, default, long
		timeout=80000, # pass timeout manually
		is_async=True, # if this is True, method is run in worker
		now=False, # if this is True, method is run directly (not in a worker) 
		job_name='Attendance',
		from_date=from_date,
		to_date=to_date
	) 
	return 'OK'

@frappe.whitelist()
def get_attendance(from_date,to_date):
	draft_doc = frappe.get_all("Attendance", {'attendance_date': ('between', (from_date,to_date)),'docstatus':0},"name")
	for i in draft_doc:
		frappe.db.set_value("Attendance",i.name,"docstatus",1)
