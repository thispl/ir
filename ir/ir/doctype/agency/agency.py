# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Agency(Document):
	pass


#Update the below components value in Employee for validate of Agency
@frappe.whitelist()
def salary_comp(doc, method):
    details = frappe.get_all("Agency Wages", {'parent': doc.name},["*"])
    for wage_detail in details:
        employee_list = frappe.get_all("Employee",{'employment_type':'Agency','custom_agency_name':doc.name,'custom_salary_category': wage_detail['designation'],"status":"Active"},['name'])
        for emp in employee_list:
            employee = frappe.get_doc("Employee", emp['name'])            
            employee.custom_basic = wage_detail['basic']
            employee.custom_dearness_allowance = wage_detail['dearness_allowance']
            employee.custom_conveyance = wage_detail['travel_allowance_rate']
            employee.custom_special_allowance = wage_detail['special_allowance']
            employee.custom_service_charges = wage_detail['service_charge']
            employee.custom_canteen= wage_detail['canteen']
            employee.custom_gross=  wage_detail['gross'] 
            employee.custom_other_allowance=wage_detail['other_allowance']
            employee.custom_esi = wage_detail['earning_esi_325']
            employee.custom_pf = wage_detail['earning_provident_fund_13']
            employee.custom_service_chrages = wage_detail['service_charge']
            employee.ctc = wage_detail['ctc']  
            employee.custom_overtime_amount = wage_detail['overtime'] 
            employee.save()    
    frappe.db.commit()  