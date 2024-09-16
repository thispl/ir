# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe import _
from frappe.utils import flt
import erpnext


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
    columns=[]
    columns += [
        _("Employee ID") + ":Link/Employee:130",
        _("Employee Name") + ":Link/Department:200",
        _("Department") + ":Data/:150",
        _("Designation") + ":Data/:150",
        _("Basic") + ":Currency/:150",
        _("HRA")+":Currency/:120",
        _("CCA")+":Currency/:120",
        _("Travelling Allowance")+":Currency/:120",
        _("Special Allowance")+":Currency/:120",
        _("Gross")+":Currency/:120",
        _("PF Employer Contribution")+":Currency/:120",
        _("ESI Employer Contribution")+":Currency/:120",
        _("Gratuity")+":Currency/:120",
        _("Bonus")+":Currency/:120",
        _("Service Charges")+":Currency/:120",
        _("Canteen")+":Currency/:120",
        _("CTC")+":Currency/:120",

    ]
    
    return columns

def get_data(filters):
    data = []
    if filters.employee_number and filters.department:
        salary = frappe.get_list("Employee",{"status":"Active","employee_number": filters.employee_number,"department":  filters.department},["*"])
        
        for i in salary:
            if i.status == 'Active':
                row = [
                    i.name,
                    i.employee_name,
                    i.department,
                    i.designation,
                    i.custom_basic,
                    i.custom_hra,
                    i.custom_cca,
                    i.custom_conveyance,
                    i.custom_special_allowance,
                    i.custom_gross,
                    i.custom_pf,
                    i.custom_esi,
                    i.custom_gratuity,
                    i.custom_bonus,
                    i.custom_service_charges,
                    i.custom_canteen,
                    i.ctc
                ]
                data.append(row)
    elif filters.employee_number:
        salary = frappe.get_list("Employee",{"status":"Active","employee_number": filters.employee_number},["*"])
        
        for i in salary:
            if i.status == 'Active':
                row = [
                    i.name,
                    i.employee_name,
                    i.department,
                    i.designation,
                    i.custom_basic,
                    i.custom_hra,
                    i.custom_cca,
                    i.custom_conveyance,
                    i.custom_special_allowance,
                    i.custom_gross,
                    i.custom_pf,
                    i.custom_esi,
                    i.custom_gratuity,
                    i.custom_bonus,
                    i.custom_service_charges,
                    i.custom_canteen,
                    i.ctc
                ]
                data.append(row)
    elif filters.department:
        salary = frappe.get_list("Employee",{"status":"Active","department": filters.department},["*"])
        
        for i in salary:
            if i.status == 'Active':
                row = [
                    i.name,
                    i.employee_name,
                    i.department,
                    i.designation,
                    i.custom_basic,
                    i.custom_hra,
                    i.custom_cca,
                    i.custom_conveyance,
                    i.custom_special_allowance,
                    i.custom_gross,
                    i.custom_pf,
                    i.custom_esi,
                    i.custom_gratuity,
                    i.custom_bonus,
                    i.custom_service_charges,
                    i.custom_canteen,
                    i.ctc
                ]
                data.append(row)
    else:
        salary = frappe.get_list("Employee",{"status":"Active"},["*"])
        for i in salary:
            if i.status == 'Active':
                row = [
                    i.name,
                    i.employee_name,
                    i.department,
                    i.designation,
                    i.custom_basic,
                    i.custom_hra,
                    i.custom_cca,
                    i.custom_conveyance,
                    i.custom_special_allowance,
                    i.custom_gross,
                    i.custom_pf,
                    i.custom_esi,
                    i.custom_gratuity,
                    i.custom_bonus,
                    i.custom_service_charges,
                    i.custom_canteen,
                    i.ctc
                ]
                data.append(row)
    
    return data

