# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import money_in_words

class AgencyInvoice(Document):
	pass

@frappe.whitelist()
def get_total_amount_in_words(total_amount):
    try:
        total_amt = float(total_amount)
        tot = money_in_words(total_amt)
        return tot  
    except ValueError:
        frappe.errprint(total_amount)
        return "Invalid amount"
    
@frappe.whitelist()
def get_md(agency,start_date,end_date,designation):
    mdr = frappe.get_value('Agency Wages',{'designation':designation,'parent':agency},['total'])
    tar = frappe.get_value('Agency Wages',{'designation':designation,'parent':agency},['travel_allowance_rate'])
    man_days = frappe.db.sql("""select sum(payment_days) from `tabSalary Slip` where docstatus != '2' and custom_agency = '%s' and start_date = '%s' and end_date = '%s' and designation = '%s' """%(agency,start_date,end_date,designation),as_dict = 1)[0]
    # ot = frappe.db.sql("""select (sum(overtime_hours))  as ot_hrs from `tabSalary Slip` where docstatus != 2  and agency_name ='%s' and employee_category='%s' and branch ='%s' and start_date = '%s' and end_date = '%s' and designation = '%s' """%(agency_name,employee_category,start_date,end_date,designation),as_dict = 1)[0]
    return man_days['sum(payment_days)'] or 0 , mdr or 0 ,tar or 0