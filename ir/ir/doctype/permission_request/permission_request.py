# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime,timedelta,date,time
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
from ir.mark_attendance import update_att_with_employee
from frappe.utils.data import date_diff, now_datetime, nowdate, today, add_days

class PermissionRequest(Document):
    @frappe.whitelist()
    def on_submit(self):
        att = frappe.db.get_value("Attendance",{"attendance_date":self.attendance_date,"employee":self.employee},["name"])
        if att:
            frappe.errprint(att)
            att_doc = frappe.get_doc("Attendance",att)
            frappe.errprint(self.permission_request_hours)
            if self.employee_category == "Blue Collar":
                frappe.db.set_value("Attendance",att,"custom_permission_hour",1)
            else:
                frappe.db.set_value("Attendance",att,"custom_permission_hour",self.permission_request_hours)
            frappe.db.set_value("Attendance",att,"custom_attendance_permission",self.name)
            if self.permission_request_hours:
                    frappe.errprint("self.from_date_session")
                    if att_doc.custom_late_entry_time != "00:00:00":
                        value = att_doc.custom_late_entry_time
                        total_seconds = value.total_seconds()
                        hr = int(total_seconds // 3600)    
                        frappe.errprint(hr)
                        if int(self.permission_request_hours) >= hr:
                            frappe.errprint("test")
                            if att_doc.shift == '3':
                                frappe.errprint("3")
                                att_doc.shift = '2'
                                frappe.db.set_value("Attendance",att,"shift",'2')
            if att_doc.in_time and att_doc.out_time:
                diff=0
                wh = att_doc.working_hours
                frappe.errprint(wh)
                if self.employee_category == "Blue Collar":
                    diff=1
                else:
                    diff=self.permission_request_hours
                    frappe.errprint(diff)
                totwh=float(wh)+float(diff)
                if totwh>=8:
                    frappe.db.set_value("Attendance",att,"status","Present")
                else:
                    frappe.db.set_value("Attendance",att,"status","Half Day")

    
    
    
    def on_cancel(self):
        # Fetch the attendance document linked with the custom on duty application
        attendance_list = frappe.get_value("Attendance", {
            'employee': self.employee,
            'custom_attendance_permission': self.name,
            "attendance_date": self.attendance_date
        }, ['name'])

        # If attendance exists, cancel it
        if attendance_list:
            attendance_obj = frappe.get_doc("Attendance", attendance_list)
            if attendance_obj.docstatus ==1:
                attendance_obj.cancel()
            if attendance_obj.docstatus ==0:
                frappe.db.sql("""DELETE FROM `tabAttendance` WHERE name = %s""", (attendance_obj.name,), as_dict=True)
            to_date = add_days(self.attendance_date,1)
            update_att_with_employee(self.attendance_date, to_date, self.employee)
            
    @frappe.whitelist()
    def get_endtime1(Self,start_time):
        time = datetime.strptime(start_time, "%H:%M:%S")
        end_time = timedelta(hours=2) + time
        return str(end_time.time())
    
    @frappe.whitelist()
    def get_endtime2(Self,end_time):
        time = datetime.strptime(end_time, "%H:%M:%S")
        start_time = time - timedelta(hours=2)
        return str(start_time.time())
    
    def validate(self):
        # self.hours = "1"
        if hasattr(self, '__islocal'):
            month_start = get_first_day(self.attendance_date)
            month_end = get_last_day(self.attendance_date)
            today = frappe.db.sql("select count(*) as count from `tabPermission Request` where employee = '%s' and attendance_date between '%s' and '%s' AND workflow_state NOT IN ('Rejected', 'Cancelled') "%(self.employee,month_start,month_end),as_dict=True)
            if today[0].count > 0:
                if self.employee_category=="Blue Collar":
                    frappe.throw("Only 1 permission are allowed for a day")
    # 	self.permission_request_hours=frappe.db.exists("Permission Request",{"employee",doc.employee})
    # 	if not self.permission_request_hours:
    # 		count = frappe.db.sql("select count(permission_request_hours) as count from `tabPermission Request` where employee = '%s' and attendance_date between '%s' and '%s' and name != '%s' and workflow_state != 'Rejected' "%(self.employee,month_start,month_end,self.name),as_dict=True)
    # 	if count[0].count >= 2:
    # 		if self.employee_category=="White Collar":
    # 			frappe.throw("Only 2 permissions are allowed for a month")
        # if count[0].count >= 1:
        # 	if self.employee_category=="Blue Collar":
        # 		frappe.throw("Only 1 permissions are allowed for a month")

def after_insert(self):
        if self.workflow_state == 'Pending for HOD':
            link = get_url_to_form("Permission Request", self.name)
            content="""<p>Dear Sir,</p>
            Kindly find the below Permission Request from %s (%s).<br>"""%(self.employee,self.employee_name)
            table = """<table class=table table-bordered><tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center>PERMISSION REQUEST</center></th><tr>
            <tr><th style = 'border: 1px solid black'>Employee ID</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Department</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>Employee Name</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Designation</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>Permission Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Session</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>Shift</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>From Time</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th rowspan='2' style = 'border: 1px solid black'>Reason</th><td rowspan='2' style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Time</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>Hours</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
            </table><br>"""%(self.employee,self.department,self.employee_name,self.designation,format_datetime(self.attendance_date),self.session,self.shift,self.from_time,self.reason,self.to_time,self.hours,link)
            regards = "Thanks & Regards,<br>hrPRO"
            frappe.sendmail(
            recipients=[self.permission_approver],
            subject='Reg.Permission Request Approval' ,
            message = content+table+regards)


@frappe.whitelist()
def permission_request(employee,attendance):
    sum=0
    month_start = get_first_day(attendance)
    month_end = get_last_day(attendance)
    total= frappe.db.sql("select * from `tabPermission Request` where employee = '%s' and attendance_date between '%s' and '%s' and workflow_state != 'Rejected' and workflow_state != 'Cancelled' "%(employee,month_start,month_end),as_dict=True)
    for i in total:
        sum+=int(i.permission_request_hours)
    return sum