import frappe
from datetime import datetime
from datetime import datetime
from datetime import datetime, timedelta
from frappe.utils.data import nowdate, date_diff
from frappe.utils import date_diff, add_months, today,nowtime,nowdate
from frappe.utils import money_in_words
from ir.mark_attendance import check_holiday
import frappe
from frappe import _
from frappe.model.document import Document
import datetime
from frappe.utils import (
    add_days,
    cstr,
    flt,
    format_datetime,
    formatdate,
    get_datetime,
    get_first_day,
    get_last_day,
    get_link_to_form,
    get_number_format_info,
    getdate,
    nowdate,
)

#Check the	date is future date of the present date	
@frappe.whitelist()
def shift_request_check(employee, from_date):
    today = nowdate()
    # f_date = datetime.strptime(from_date, "%Y-%m-%d").date()
    diff = date_diff(today, from_date)
    if diff > -1:
        frappe.msgprint("Shift Request needs to be taken before the from date")
        return "False"
    else:
        return "True"


#if Permission there in attendance , shift has been changed as 3 to 2 
@frappe.whitelist()
def update_shift(doc, method):
    if doc.custom_attendance_permission:
        if doc.shift=='3':
            if frappe.db.exists("Shift Assignment",{'employee':doc.employee,'start_date':doc.attendance_date,'docstatus':['!=',2]}):
                act_shift=frappe.db.get_value("Shift Assignment",{'employee':doc.employee,'start_date':doc.attendance_date,'docstatus':['!=',2]},['shift_type'])
                if act_shift=='2' or act_shift=='3':
                    frappe.db.set_value("Attendance",doc.name,'shift',act_shift)
                

#Get the total value of Salary Slip
@frappe.whitelist()
def get_mandays_amount(agency,designation):
    man_days_amount = frappe.db.sql("""select sum(rounded_total) from `tabSalary Slip` where docstatus != 2  and custom_agency='%s' and designation = '%s' """%(custom_agency,designation),as_dict = 1)[0]
    return[man_days_amount['sum(rounded_total)']]


#Update the Shift assignment is on submission of Shift Request
@frappe.whitelist()
def shift_change_req(doc, method):
    assignment = frappe.db.sql("""
        SELECT name FROM `tabShift Assignment`
        WHERE employee = %s AND start_date = %s
    """, (doc.employee, doc.from_date), as_dict=True)
    if assignment:
        for record in assignment:
            frappe.db.sql("""UPDATE `tabShift Assignment` SET docstatus = 0 WHERE name = %s""", (record['name'],))
            frappe.db.sql("""DELETE FROM `tabShift Assignment` WHERE name = %s""", (record['name'],))
    return "Ok"


from frappe.utils import  formatdate,get_last_day, get_first_day, add_days
#Set default to date is based on given from date(Report filters)
@frappe.whitelist()
def get_to_date(from_date):
    return get_last_day(from_date)

# @frappe.whitelist()
# def validate_od_date(doc,method):
# 	mesg=frappe.db.exists("On Duty Application",{"docstatus":("!=",'2'),'from_date':doc.from_date,'custom_employe':doc.custom_employe})
# 	if mesg:
# 		frappe.throw("Not valid")


#Create Comp off document based on below conditions - On submission of Attendance
@frappe.whitelist()
def compoff_for_ot(doc,method):
    ot_applicable = frappe.db.get_value("Employee", {"employee": doc.employee}, ['custom_ot_applicable'])
    holiday = check_holiday(doc.attendance_date, doc.employee)    
    if holiday:
        if doc.custom_employee_category == 'White Collar' and ot_applicable == 0:
            if not frappe.db.exists("Compensatory Off Request", {"employee": doc.employee, "from_date": doc.attendance_date, "docstatus": ['!=', 2]}):
                if doc.working_hours is not None:
                    if 4 <= float(doc.working_hours) < 8:
                        new_allocation = frappe.new_doc("Compensatory Off Request")
                        new_allocation.employee = doc.employee
                        new_allocation.from_date = doc.attendance_date
                        new_allocation.to_date = doc.attendance_date
                        new_allocation.half_day = 1
                        new_allocation.half_day_date = doc.attendance_date
                        new_allocation.reason = "Automatically created"  
                        new_allocation.insert(ignore_permissions=True)
                    elif float(doc.working_hours) > 8:
                        new_allocation = frappe.new_doc("Compensatory Off Request")
                        new_allocation.employee = doc.employee
                        new_allocation.from_date = doc.attendance_date
                        new_allocation.to_date = doc.attendance_date
                        new_allocation.reason = "Automatically created"  
                        new_allocation.insert(ignore_permissions=True)
                    

# Manually update the status
@frappe.whitelist()
def attendance_correction():
	checkin = frappe.db.sql("""
    UPDATE `tabAttendance`
    SET late_entry = 0,custom_late_entry_time=Null
    WHERE name = 'HR-ATT-2025-15086'
""", as_dict=True)
    # value=frappe.db.get_value("Salary Slip",{"name":"Sal Slip/S1476/00008"},["gross_pay"])
    # print(value * 0.0075)