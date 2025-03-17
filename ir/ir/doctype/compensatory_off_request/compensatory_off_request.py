# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from datetime import datetime, timedelta
from datetime import datetime
from frappe.utils import date_diff, add_months, today,nowtime,nowdate,format_date
from frappe.utils.data import date_diff, now_datetime, nowdate, today, add_days
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
from frappe.utils import (
    add_days,
    cint,
    cstr,
    date_diff,
    flt,
    formatdate,
    get_fullname,
    get_link_to_form,
    getdate,
    nowdate,
)

class CompensatoryOffRequest(Document):
	pass
	
#Cancel the comp off , leave ledger entry has been expired
@frappe.whitelist()	
def comp_off_revert(doc,method):
	value = frappe.db.get_value("Leave Ledger Entry",{"employee":doc.employee,"leave_type":"Compensatory Off"},["name","creation"])
	creation_date = getdate(value[1])
	submitted_date = getdate(doc.submitted_date)
	if creation_date ==  submitted_date:
		frappe.db.set_value("Leave Ledger Entry",value[0],"is_expired",1)

#set the document submitted date
@frappe.whitelist()
def submitted_date(doc,method):
    frappe.db.set_value("Compensatory Off Request",doc.name,"submitted_date",nowdate())

import datetime as dt
#Give the allocation of comp off if all conditions has been matched
@frappe.whitelist()
def comp_off_allocation(doc,method):
    if doc.employee_category == 'White Collar':
        attendance=frappe.get_all("Attendance",{'employee':doc.employee,'attendance_date':('between',(doc.from_date,doc.to_date)),"docstatus":("!=",2)},["*"])
        for att in attendance:
            holiday_list = frappe.get_value('Employee',{'name':doc.employee},['holiday_list'])
            holiday = frappe.db.get_value('Holiday',{'parent': holiday_list, 'holiday_date':('between',(doc.from_date,doc.to_date))},['weekly_off'])
            if holiday==1 or holiday == 0:
                if att.status == "Present":
                    year = att.attendance_date.year
                    year_start = dt.datetime(year, 1, 1)
                    year_end = dt.datetime(year, 12, 31)
                    
                    leave = frappe.db.exists("Leave Allocation", {'employee': doc.employee,
                                                                'docstatus': 1,
                                                                'leave_type': "Compensatory Off",
                                                                'from_date': ('>=', year_start),
                                                                'to_date': ('<=', year_end)})
                    if leave:
                        leave_doc = frappe.get_doc("Leave Allocation", leave)
                        leave_doc.new_leaves_allocated += 1
                        leave_doc.save(ignore_permissions=True)
                    else:
                        leave_doc = frappe.new_doc("Leave Allocation")
                        leave_doc.employee = doc.employee
                        leave_doc.leave_type = "Compensatory Off"
                        leave_doc.from_date = year_start
                        leave_doc.to_date = year_end
                        leave_doc.new_leaves_allocated = 1
                        leave_doc.save(ignore_permissions=True)
                        leave_doc.submit()
                elif att.status =="Half Day" and doc.half_day==1:
                    year = att.attendance_date.year
                    year_start = dt.datetime(year, 1, 1)
                    year_end = dt.datetime(year, 12, 31)
                    
                    leave = frappe.db.exists("Leave Allocation", {'employee': doc.employee,
                                                                'docstatus': 1,
                                                                'leave_type': "Compensatory Off",
                                                                'from_date': ('>=', year_start),
                                                                'to_date': ('<=', year_end)})
                    if leave:
                        leave_doc = frappe.get_doc("Leave Allocation", leave)
                        leave_doc.new_leaves_allocated += 0.5
                        leave_doc.save(ignore_permissions=True)
                    else:
                        leave_doc = frappe.new_doc("Leave Allocation")
                        leave_doc.employee = doc.employee
                        leave_doc.leave_type = "Compensatory Off"
                        leave_doc.from_date = year_start
                        leave_doc.to_date = year_end
                        leave_doc.new_leaves_allocated = 0.5
                        leave_doc.save(ignore_permissions=True)
                        leave_doc.submit()
                else:
                    frappe.throw("You are not eligible for Comp Off because you are not Present this date")
                
            else:
                five_hours = timedelta(hours=5)
                if att.custom_ot_hours >= five_hours:
                    attendance_date = att.attendance_date
                    year = attendance_date.year
                    year_start = datetime(year, 1, 1)
                    year_end = datetime(year, 12, 31)
                    
                    leave = frappe.db.exists("Leave Allocation", {
                        'employee': doc.employee,
                        'docstatus': 1,
                        'leave_type': "Compensatory Off",
                        'from_date': ('<=', year_end),
                        'to_date': ('>=', year_start)
                    })
                    
                    if leave:
                        leave_doc = frappe.get_doc("Leave Allocation", leave)
                        leave_doc.new_leaves_allocated += 0.5
                        leave_doc.save(ignore_permissions=True)
                    else:
                        leave_doc = frappe.new_doc("Leave Allocation")
                        leave_doc.employee = doc.employee
                        leave_doc.leave_type = "Compensatory Off"
                        leave_doc.from_date = year_start
                        leave_doc.to_date = year_end
                        leave_doc.new_leaves_allocated = 0.5
                        leave_doc.save(ignore_permissions=True)
                        leave_doc.submit()
                else:
                    frappe.throw("You are not eligible for Comp Off because you not working more than 5 hours")
    else:
        frappe.throw("You are not eligible for Comp Off you are not white collar")

#Check the comp off is applicable or not based on category
@frappe.whitelist()
def comp_off_applicable(doc,method):
    if doc.employee_category == 'White Collar':
        ot_applicable = frappe.db.get_value("Employee", {"employee": doc.employee}, ['custom_ot_applicable'])
        if ot_applicable==0:
            attendance=frappe.get_all("Attendance",{'employee':doc.employee,'attendance_date':('between',(doc.from_date,doc.to_date)),"docstatus":("!=",2)},["*"])
            if attendance:
                for att in attendance:
                    holiday_list = frappe.get_value('Employee',{'name':doc.employee},['holiday_list'])
                    holiday = frappe.db.get_value('Holiday',{'parent': holiday_list, 'holiday_date':("between",(doc.from_date,doc.to_date))},['weekly_off'])
                    if holiday==1:  
                        if not att.status =="Present" and not att.status == "Half Day":
                            frappe.throw("You are not eligible for Comp Off because you not present in this date")
                        
                    else:
                        five_hours = timedelta(hours=5)
                        if not att.custom_ot_hours >= five_hours:
                            frappe.throw("You are not eligible for Comp Off because you not working more than 5 hours ot")
            else:
                frappe.throw("No attendance for this date") 
        else:
            frappe.throw("You are not eligible for Comp Off, Only eligible for OT")               
    else:
        frappe.throw("You are not eligible for Comp Off because you are not White Collar Category") 
        

#Comp off application allowed to applied within 3 days
@frappe.whitelist()
def comp_off_req(doc,method):
    if doc.employee_category != "White Collar":
        frappe.throw("You are not eliglible to apply")
    diff = date_diff(doc.posting_date, doc.from_date)
    role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":"HR User"})
    if not role:
        if diff > 3:
            frappe.throw("The Comp Off request must be apply within 3 days from the Worked day")
        if diff < 0:
            frappe.throw("Posting Date Must be greater than the working date")

#Avoid duplicate entry
@frappe.whitelist()
def validate_comp_off_app(doc, method):
    if doc.is_new():
        if frappe.db.exists("Compensatory Off Request", {"employee": doc.employee, "from_date": doc.from_date, "workflow_state": ("Not In", ("Cancelled","Rejected"))}):
            frappe.throw("A Compensatory Off Request for this employee and date already exists.")


from typing import Dict, Optional, Tuple, Union
@frappe.whitelist()
def get_number_of_leave_days(
    from_date: datetime.date,
    to_date: datetime.date,
    half_day: Union[int, str, None] = None,
    half_day_date: Union[datetime.date, str, None] = None,
) -> float:
    
    number_of_days = 0
    if cint(half_day) == 1:
        if getdate(from_date) == getdate(to_date):
            number_of_days = 0.5
        elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
            number_of_days = date_diff(to_date, from_date) + 0.5
        else:
            number_of_days = date_diff(to_date, from_date) + 1
    else:
        number_of_days = date_diff(to_date, from_date) + 1

    return number_of_days


@frappe.whitelist()
def comp_off_applicable_employee(doc,method):
    if doc.employee_category == 'White Collar':
        attendance=frappe.get_all("Attendance",{'employee':doc.employee,'attendance_date':('between',(doc.from_date,doc.to_date)),"docstatus":("!=",2)},["*"])
        for att in attendance:
            holiday_list = frappe.get_value('Employee',{'name':doc.employee},['holiday_list'])
            holiday = frappe.db.get_value('Holiday',{'parent': holiday_list, 'holiday_date':('between',(doc.from_date,doc.to_date))},['weekly_off'])
            if holiday==1 or holiday == 0:
                if att.status == "Present":
                    pass
                elif att.status =="Half Day" and doc.half_day==1:
                    pass
                elif att.status == "Absent" or att.status == "On Leave":
                    frappe.throw("You are not eligible for Comp Off because you are not Present this date")
                
                elif att.status =="Half Day" and not doc.half_day==1:
                    frappe.throw("You are not eligible to claim full day , Eligible for half day only.")
            else:
                five_hours = timedelta(hours=5)
                if att.custom_ot_hours >= five_hours:
                    pass
                else:
                    frappe.throw("You are not eligible for Comp Off because you not working more than 5 hours")
    else:
        frappe.throw("You are not eligible for Comp Off you are not white collar")