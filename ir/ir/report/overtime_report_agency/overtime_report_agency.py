# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe import permissions
from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days,date_diff
from math import floor
from frappe import msgprint, _
from calendar import month, monthrange
from datetime import date, timedelta, datetime,time

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = []
    columns += [
        _("Employee ID") + ":Data/:100",_("Employee Name") +':Data:150',_("Designation")+':Data:170',_("Department") + ":Data/:150",_("Cost Center") + ":Data/:100",_("Agency") + ":Data/:150",
    ]
    dates = get_dates(filters.from_date,filters.to_date)
    for date in dates:
        date = datetime.strptime(date,'%Y-%m-%d')
        day = datetime.date(date).strftime('%d')
        month = datetime.date(date).strftime('%b')
        columns.append(_(day + '/' + month) + ":Int/:90")
    columns.append(("Total")+":Int/:100")
    return columns

def get_data(filters):
    data = []
    emp_status_map = []
    employees = get_employees(filters)
    
    for emp in employees:
        row1 = [emp.name, emp.employee_name, emp.designation, emp.department, emp.payroll_cost_center, emp.custom_agency_name or '-']
        dates = get_dates(filters.from_date, filters.to_date)
        tot_ot = 0 
        for date in dates:
            ot_float = 0  
            if frappe.db.exists('Over Time Request', {'employee': emp.name, 'ot_date': date, 'docstatus': ['!=', 2]}):
                ot = frappe.db.get_value('Over Time Request', {'employee': emp.name, 'ot_date': date, 'docstatus': ['!=', 2]}, ['ot_hour'])
                if ot:
                    ot_float = convert_hhmmss_to_hours(ot)
            row1.append(ot_float) 
            tot_ot += ot_float 
        row1.append(tot_ot) 
        data.append(row1)  
    return data

def get_dates(from_date,to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    return dates

def get_employees(filters):
    conditions = ''
    left_employees = []
    if filters.employee:
        conditions += "and employee = '%s' " % (filters.employee)
    if filters.agency_name:
        conditions += "and custom_agency_name = '%s' " % (filters.agency_name)
    employees = frappe.db.sql("""select name, employee_name, department,designation,payroll_cost_center,custom_agency_name from `tabEmployee` where employment_type ='Agency' AND  status = 'Active' %s """ % (conditions), as_dict=True)
    left_employees = frappe.db.sql("""select name, employee_name, department,designation,payroll_cost_center,custom_agency_name from `tabEmployee` where employment_type ='Agency' AND status = 'Left' and relieving_date >= '%s' %s """ %(filters.from_date,conditions),as_dict=True)
    employees.extend(left_employees)
    return employees

@frappe.whitelist()
def convert_hhmmss_to_hours(time_str):
    total_seconds = time_str.total_seconds()    
    total_hours = total_seconds / 3600  
    return total_hours
