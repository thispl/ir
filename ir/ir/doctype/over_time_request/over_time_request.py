# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import frappe

class OverTimeRequest(Document):
	pass
@frappe.whitelist()
def overtime_(employee, from_date):
    result = frappe.db.sql("""
        SELECT workflow_state, from_time, to_time, name,employee
        FROM `tabOn Duty Application`
        WHERE employee = %s AND from_date = %s
        LIMIT 1
    """, (employee, from_date), as_dict=True)
    
    if result:
        return result[0]
    else:
        result=0
        return result
    
