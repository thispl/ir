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

        
@frappe.whitelist()
def shift_request_check(employee, from_date):
    today = nowdate()
    # f_date = datetime.strptime(from_date, "%Y-%m-%d").date()
    diff = date_diff(today, from_date)
    frappe.errprint(diff)
    if diff > -1:
        frappe.msgprint("Shift Request needs to be taken before the from date")
        return "False"
    else:
        return "True"


@frappe.whitelist()
def update_shift(doc, method):
    if doc.custom_attendance_permission:
        frappe.errprint("self.from_date_session")
        if doc.custom_late_entry_time != "00:00:00":
            time_string=doc.custom_late_entry_time
            time_parts = [int(part) for part in time_string.split(':')]
            delta = timedelta(hours=time_parts[0], minutes=time_parts[1], seconds=time_parts[2])            
            total_seconds = delta.total_seconds()            
            hr = int(total_seconds // 3600)    
            frappe.errprint(hr)
            if int(doc.custom_permission_hour) >= hr:
                frappe.errprint("test")
                if doc.shift == '3':
                    frappe.db.set_value("Attendance",doc.name,'shift','2')


@frappe.whitelist()
def get_mandays_amount(agency,designation):
    man_days_amount = frappe.db.sql("""select sum(rounded_total) from `tabSalary Slip` where docstatus != 2  and custom_agency='%s' and designation = '%s' """%(custom_agency,designation),as_dict = 1)[0]
    return[man_days_amount['sum(rounded_total)']]


@frappe.whitelist()
def shift_change_req(doc, method):
    frappe.errprint("HII")
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
@frappe.whitelist()
def get_to_date(from_date):
    return get_last_day(from_date)

# @frappe.whitelist()
# def validate_od_date(doc,method):
# 	frappe.errprint(doc.custom_employe)
# 	frappe.errprint(doc.from_date)
# 	mesg=frappe.db.exists("On Duty Application",{"docstatus":("!=",'2'),'from_date':doc.from_date,'custom_employe':doc.custom_employe})
# 	frappe.errprint(mesg)
# 	if mesg:
# 		frappe.throw("Not valid")

# from ir.mark_attendance import mark_wh

# @frappe.whitelist()
# def update_query():
#     count=0
#     value = frappe.get_all("Miss Punch Application",{"workflow_state":"Approved","attendance_date":("between",("2024-07-01","2024-07-31"))},["*"])
#     for i in value:
#         att=frappe.db.get_value("Attendance",{"docstatus":("!=",2),"attendance_date":i.attendance_date,"employee":i.employee},["name"])
#         frappe.db.set_value("Attendance",att,"custom_miss_punch_application",i.name)
#         frappe.db.set_value("Attendance",att,"shift",i.shift)
#         frappe.db.set_value("Attendance",att,"in_time",i.in_time)
#         frappe.db.set_value("Attendance",att,"out_time",i.out_time)
#         mark_wh(i.attendance_date,i.attendance_date)

# @frappe.whitelist()
# def validate_miss_punch(doc,method):
# 	if not doc.in_time and not doc.out_time:
# 		frappe.throw("There is no checkin or checkout present for this date")
# 	if doc.in_time and doc.out_time:
# 		frappe.throw("Already Available checkins are against this date")

@frappe.whitelist()
def update_hours(doc,method):
    if doc.status == "On Leave" or doc.status=="Absent":
        frappe.db.sql("""
            UPDATE `tabAttendance`
                SET custom_early_out_time = "00:00:00" , custom_total_working_hours = "00:00:00" , custom_ot_hours = "00:00:00" 
                WHERE name = %s
            """,(doc.name))
    if doc.late_entry==0:
        frappe.db.sql("""update `tabAttendance` set custom_late_entry_time = "00:00:00" """,as_dict = True)
    
    frappe.db.sql("""
        UPDATE `tabAttendance`
        SET custom_ot_hours = "00:00:00"
        WHERE (status = 'Half Day' AND late_entry = 0)
           OR (late_entry = 1 AND custom_late_entry_time < '03:00:00')
    """)
    # if doc.late_entry ==1 and doc.status == "Half Day":
    #     if doc.custom_late_entry_time < timedelta(hours=3):
    #         frappe.db.sql("""update `tabAttendance` set custom_ot_hours = "00:00:00" """,as_dict = True)
    
# @frappe.whitelist()
# def update_hours_alternate(doc,method):
#     if doc.status == "On Leave" or doc.status=="Absent":
#         frappe.db.sql("""
#             UPDATE `tabAttendance`
#                 SET custom_early_out_time = "00:00:00" , custom_total_working_hours = "00:00:00" , custom_ot_hours = "00:00:00" 
#                 WHERE name = ''
#             """,(doc.name))
#     if doc.late_entry==0:
#         frappe.db.sql("""update `tabAttendance` set custom_late_entry_time = "00:00:00" """,as_dict = True)

import frappe

# @frappe.whitelist()
# def update_hours_alternate():
#     value = frappe.get_all("Attendance",{"docstatus":("!=",2)},["*"])
#     for i in value:
#         if i.status == "On Leave" or i.status == "Absent":
#             frappe.db.sql("""
#                 UPDATE `tabAttendance`
#                 SET custom_early_out_time = "00:00:00",
#                     custom_total_working_hours = "00:00:00",
#                     custom_ot_hours = "00:00:00"
#                 WHERE name = %s
#             """, (i.name))
#             frappe.db.commit()

@frappe.whitelist()
def update_od_ot():
    frappe.db.sql("""
        UPDATE `tabOver Time Request`
        SET ot_date = "2024-08-21"
        WHERE name = 'OT Req-609732'
    """)


@frappe.whitelist()
def compoff_for_ot(doc,method):
    frappe.errprint("Method")
    ot_applicable = frappe.db.get_value("Employee", {"employee": doc.employee}, ['custom_ot_applicable'])
    holiday = check_holiday(doc.attendance_date, doc.employee)    
    if holiday:
        frappe.errprint("Holiday check passed")
        if doc.custom_employee_category == 'White Collar' and ot_applicable == 0:
            frappe.errprint("Employee category and OT applicable condition met")
            if not frappe.db.exists("Compensatory Off Request", {"employee": doc.employee, "from_date": doc.attendance_date, "docstatus": ['!=', 2]}):
                if doc.working_hours >= 4 and doc.working_hours < 8:
                    frappe.errprint("Comp Off Request not present, creating new one")
                    new_allocation = frappe.new_doc("Compensatory Off Request")
                    new_allocation.employee = doc.employee
                    new_allocation.from_date = doc.attendance_date
                    new_allocation.to_date = doc.attendance_date
                    new_allocation.half_day = 1
                    new_allocation.half_day_date = doc.attendance_date
                    new_allocation.reason = "Automatically created"  
                    new_allocation.insert(ignore_permissions=True)
                    frappe.errprint("Comp Off Request created successfully")
                elif doc.working_hours > 8:
                    frappe.errprint("Comp Off Request not present, creating new one")
                    new_allocation = frappe.new_doc("Compensatory Off Request")
                    new_allocation.employee = doc.employee
                    new_allocation.from_date = doc.attendance_date
                    new_allocation.to_date = doc.attendance_date
                    new_allocation.reason = "Automatically created"  
                    new_allocation.insert(ignore_permissions=True)
                    frappe.errprint("Comp Off Request created successfully")
                else:
                    frappe.errprint("Not eligible")
@frappe.whitelist()
def attendance_correction():
	checkin = frappe.db.sql("""update `tabLeave Allocation` set from_date = "2024-01-01" where name="HR-LAL-2024-00770" """,as_dict = True)
    # value=frappe.db.get_value("Attendance",{"name":"HR-ATT-2024-54624"},["docstatus"])
    # print(value)