# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class OverTimePlan(Document):
	pass

@frappe.whitelist()
def ot_plan(department):
    employees = frappe.get_all("Employee", filters={"status": "Active", "department": department}, fields=["name", "employee_name"])
    employee_info = [(emp.name, emp.employee_name) for emp in employees]
    return employee_info