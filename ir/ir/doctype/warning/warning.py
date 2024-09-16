# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Warning(Document):
	pass

@frappe.whitelist()
def new_occurrence_count(type,emp):
    frappe.errprint("hi")
    if frappe.db.exists("Warning", {"employee":emp,"issue_type":type}):
        count = frappe.db.sql("""SELECT count(*) as count FROM `tabWarning` WHERE employee = %s AND issue_type=%s ORDER BY creation DESC LIMIT 1""",(emp,type), as_dict=True)
        frappe.errprint(count[0]['count'])
        count = count[0]['count'] + 1
    else:
        count = 1
    return count