# Copyright (c) 2023, Abdulla and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.utils import flt
import erpnext

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = []
	columns += [
		_("Agency Name") + ":Link/Agency:110",
		_("Cost Center") + ":Data/:200",
		_("Total Man-days") + ":Data/ :200",
		_("Amount") + ":Currency/:100",
		_("Service Charge") + ":Float/:100",
	]
	return columns


def get_data(filters):
	data = []
	if filters.agency:
		agency = frappe.get_list("Agency Invoice",{"docstatus": ["!=", 2],"agency_name": filters.agency,"payroll_date": ["between", [filters.from_date, filters.to_date]]},["*"])
		for i in agency:
			child = frappe.get_doc("Agency Invoice",i.name)
			for j in child.details:
				row=[i.agency_name,i.cost_center,i.total_man_days,i.total_amount,j.service_charges]
				data.append(row)
	else:
		agency = frappe.get_list("Agency Invoice",{"docstatus": ["!=", 2],"payroll_date": ["between", [filters.from_date, filters.to_date]]},["*"])
		for i in agency:
			child = frappe.get_doc("Agency Invoice",i.name)
			for j in child.details:
				row=[i.agency_name,i.cost_center,i.total_man_days,i.total_amount,j.service_charges]
				data.append(row)
	return data
