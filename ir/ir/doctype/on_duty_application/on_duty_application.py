# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime,timedelta,date
from frappe import _
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours

from frappe.utils import today,flt,add_days,date_diff,getdate,cint,formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form
from frappe import enqueue
from ir.mark_attendance import update_on_duty

class LeaveApproverIdentityError(frappe.ValidationError): pass
class OverlapError(frappe.ValidationError): pass
class InvalidApproverError(frappe.ValidationError): pass
class AttendanceAlreadyMarkedError(frappe.ValidationError): pass    

class OnDutyApplication(Document):
    def validate(self):
        if self.is_new():
            if frappe.db.exists("On Duty Application",{"employee":self.employee,"from_date":self.from_date,"workflow_state":("!=","Rejected"),"docstatus":("!=",2)}):
                frappe.throw("You are Already Applied for this date")
        diff = date_diff(self.from_date,self.posting_date)
        if diff>4:
            frappe.throw("Only Allow to Apply for future 3 days")
        # if self.employee_category != "White Collar":
        #     frappe.throw("You are not eliglible to apply")
        diff = date_diff(self.posting_date, self.from_date)
        role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":"HR User"})
        if not role:
            if diff > 4:
                frappe.throw("The On Duty Application must be apply within 3 days from the worked day")
            # if diff < 0:
            #     frappe.throw("Posting Date Must be greater than the working date")
                
                
        value = frappe.db.exists("Leave Application", {
            "employee": self.employee,
            "docstatus":("!=,2"),
            "from_date": ["<=", self.from_date],
            "to_date": [">=",self. from_date],
            "half_day":0
            })
        if value:
            frappe.throw("You Already Applied the Leave Application for Same Date")
        no_of_days = date_diff(add_days(self.to_date, 1),self.from_date )
        dates = [add_days(self.from_date, i) for i in range(0, no_of_days)]
        for date in dates:
            att = frappe.db.exists("Attendance",{"attendance_date":date,"employee":self.employee,"docstatus":1})
            if att:
                doc = frappe.get_doc("Attendance",att)
                if doc.custom_on_duty_application:
                    duty = frappe.get_doc("On Duty Application",doc.custom_on_duty_application)
                    if duty.workflow_state == "Rejected":
                        doc.cancel()
                    else:
                        frappe.throw(_('Attendance Closed for this %s day %s'%(self.employee,date)))      	


    def on_submit(self):
        if self.workflow_state=="Approved":
            if self.status == "Applied":
                frappe.throw(_("Only Applications with status 'Approved' and 'Rejected' can be submitted"))
            # if self.workflow_state == "Approved":
            no_of_days = date_diff(add_days(self.to_date, 1),self.from_date )
            dates = [add_days(self.from_date, i) for i in range(0, no_of_days)]
            att = frappe.db.exists("Attendance",{"attendance_date":self.from_date,"employee":self.employee,"docstatus":["!=","2"]})
            if att:
                doc = frappe.get_doc("Attendance",att)
                if doc.docstatus == 0:
                    if self.from_date_session=="Full Day":
                        if doc.in_time and doc.out_time:
                            wh = time_diff_in_hours(doc.out_time,doc.in_time)
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(wh)+float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                        else:
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                    else:
                        if doc.in_time and doc.out_time:
                            wh = time_diff_in_hours(doc.out_time,doc.in_time)
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(wh)+float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                        else:
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                    hh = check_holiday(self.employee,self.from_date)
                    if hh:
                        if hh == 'WW':
                            doc.shift_status = "ODW"
                        else:
                            doc.shift_status = "ODH"
                    else:
                        doc.shift_status = "OD"
                    doc.custom_on_duty_application= self.name
                    if self.from_date_session == "First Half":
                        if doc.custom_late_entry_time != "00:00:00":
                            value = doc.custom_ot_hours
                            total_seconds = value.total_seconds()
                            hr = int(total_seconds // 3600)    
                            if int(self.od_time) >= hr:
                                if doc.shift == '3':
                                    doc.shift = '2'
                    doc.save(ignore_permissions=True)
                    if doc.status =="Present":
                        doc.submit()
                        frappe.db.commit()
                elif doc.docstatus == 1:
                    # doc.cancel()
                    # doc = frappe.new_doc("Attendance")
                    # doc.employee = self.employee
                    # doc.attendance_date = date
                    if self.from_date_session=="Full Day":
                        if doc.in_time and doc.out_time:
                            wh = time_diff_in_hours(doc.out_time,doc.in_time)
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(wh)+float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                        else:
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                    else:
                        if doc.in_time and doc.out_time:
                            wh = time_diff_in_hours(doc.out_time,doc.in_time)
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(wh)+float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                        else:
                            diff=time_diff_in_hours(self.to_time,self.from_time)
                            totwh=float(diff)
                            if totwh>=8:
                                doc.status = 'Present'
                            elif 8<totwh>=4:
                                doc.status = 'Half Day'
                            else:
                                doc.status ="Absent"
                    hh = check_holiday(self.employee,date)
                    if hh:
                        if hh == 'WW':
                            doc.shift_status = "ODW"
                        else:
                            doc.shift_status = "ODH"
                    else:
                        doc.shift_status = "OD"
                    doc.custom_on_duty_application = self.name
                    if self.from_date_session == "First Half":
                        if doc.custom_late_entry_time != "00:00:00":
                            value = doc.custom_ot_hours
                            total_seconds = value.total_seconds()
                            hr = int(total_seconds // 3600)    
                            if int(self.od_time) >= hr:
                                if doc.shift == '3':
                                    doc.shift = '2'
                    doc.save(ignore_permissions=True)
                    if doc.status =="Present":
                        doc.submit()
                        frappe.db.commit()
            else:
                doc=frappe.new_doc('Attendance')
                doc.employee=self.employee
                doc.attendance_date=self.from_date
                if self.from_date_session=="Full Day":
                    if doc.in_time and doc.out_time:
                        wh = time_diff_in_hours(doc.out_time,doc.in_time)
                        diff=time_diff_in_hours(self.to_time,self.from_time)
                        totwh=float(wh)+float(diff)
                        if totwh>=8:
                            doc.status = 'Present'
                        elif 8<totwh>=4:
                            doc.status = 'Half Day'
                        else:
                            doc.status ="Absent"
                    else:
                        diff=time_diff_in_hours(self.to_time,self.from_time)
                        totwh=float(diff)
                        if totwh>=8:
                            doc.status = 'Present'
                        elif 8<totwh>=4:
                            doc.status = 'Half Day'
                        else:
                            doc.status ="Absent" 
                else:
                    if doc.in_time and doc.out_time:
                        wh = time_diff_in_hours(doc.out_time,doc.in_time)
                        diff=time_diff_in_hours(self.to_time,self.from_time)
                        totwh=float(wh)+float(diff)
                        if totwh>=8:
                            doc.status = 'Present'
                        elif 8<totwh>=4:
                            doc.status = 'Half Day'
                        else:
                            doc.status ="Absent"
                    else:
                        diff=time_diff_in_hours(self.to_time,self.from_time)
                        totwh=float(diff)
                        if totwh>=8:
                            doc.status = 'Present'
                        elif 4 <= totwh <= 8:
                            doc.status = 'Half Day'
                        else:
                            doc.status ="Absent" 
                hh = check_holiday(self.employee, date)
                if hh:
                    if hh=='WW':
                        doc.shift_status="ODW"
                    else:
                        doc.shift_status="ODH"
                else:
                    doc.shift_status="OD"
                doc.custom_on_duty_application=self.name
                doc.custom_total_working_hours = "00:00:00"
                doc.custom_ot_hours = "00:00:00"
                if self.from_date_session == "First Half" and doc.name:
                    if doc.custom_late_entry_time != "00:00:00":
                        value = doc.custom_ot_hours
                        total_seconds = value.total_seconds()
                        hr = int(total_seconds // 3600)    
                        if int(self.od_time) >= hr:
                            if doc.shift == '3':
                                doc.shift = '2'
                doc.save(ignore_permissions=True)
                if doc.status =="Present":
                    doc.submit()
                    frappe.db.commit()            
                            


    # def on_cancel(self):
    #     attendance_list =frappe.get_doc("On Duty Application",self.name)
    #     for i in self.multi_employee:
    #         att = frappe.get_doc("Attendance",self.name)
    #         if att:
    #             for attendance in att:
    #                 attendance_obj = frappe.get_doc("Attendance", attendance['name'])
    #                 attendance_obj.cancel()
  # Ensure this is the correct import
    from frappe.utils.data import date_diff, now_datetime, nowdate, today, add_days
    def on_cancel(self):
        # Fetch the attendance document linked with the custom on duty application
        attendance_list = frappe.get_value("Attendance", {
            'employee': self.employee,
            'custom_on_duty_application': self.name,
            "attendance_date": self.from_date
        }, ['name'])

        # If attendance exists, cancel it
        if attendance_list:
            attendance_obj = frappe.get_doc("Attendance", attendance_list)
            if attendance_obj.docstatus ==1:
                attendance_obj.cancel()
            if attendance_obj.docstatus ==0:
                frappe.db.sql("""DELETE FROM `tabAttendance` WHERE custom_on_duty_application = %s""", (self.name))
                to_date = add_days(self.from_date,1)
                update_on_duty(self.from_date, to_date, self.employee)
                

    def after_insert(self):
        if self.workflow_state == 'Pending for HOD':
            table = ''
            link = get_url_to_form("On Duty Application", self.name)
            content="""<p>Dear Sir,<br>Kindly find the below On Duty Application from %s (%s).</p><br>"""%(self.employee,self.employee_name)
            for idx,emp in enumerate(self.multi_employee):
                header = """<table class=table table-bordered><tr><td style = 'border: 1px solid black'>Serial No</td><th colspan='7' style = 'border: 1px solid black;background-color:#ffedcc;'><center>On Duty Application</center></th><tr>"""
                table += """<tr><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Employee ID</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Employee Name</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Department</th><td style = 'border: 1px solid black'>%s</td></tr>
                """%(idx+1,emp.employee_id,emp.employee_name,emp.department)
            data = """ </table><br><table class=table table-bordered><th colspan='6' style = 'border: 1px solid black;background-color:#ffedcc;'><center>On Duty Application Details</center></th><tr>
            <tr><th style = 'border: 1px solid black'>From Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Date</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>From Time</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Time</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>Total Number of Days</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Session</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
            </table><br>"""%(format_datetime(self.from_date),format_datetime(self.to_date),format_datetime(self.from_time),format_datetime(self.to_time),self.total_number_of_days,self.from_date_session,link)
            regards = "Thanks & Regards,<br>ir"
            frappe.sendmail(
            recipients=[self.approver],
            subject='Reg.On Duty Application Approval' ,
            message = content+header+table+data+regards)

    @frappe.whitelist()
    def show_html(self):
        if self.vehicle_request:
            html = "<h2><center>ON DUTY APPLICATION WITH VEHICLE</center></h2><table class='table table-bordered'><tr><th>From Date</th><th>To Date</th></tr><tr><td><h2>%s</h2></td><td><h2>%s</h2></td></tr><tr><th>From Time</th><th>To Time</th></tr><tr><td><h2>%s</h2></td><td><h2>%s</h2></td></tr></table>"%(frappe.utils.format_date(self.from_date),frappe.utils.format_date(self.to_date),self.from_time,self.to_time)
        else:
            html = "<h2><center>ON DUTY APPLICATION</center></h2><table class='table table-bordered'><tr><th>From Date</th><th>To Date</th></tr><tr><td><h2>%s</h2></td><td><h2>%s</h2></td></tr><tr><th>From Time</th><th>To Time</th></tr><tr><td><h2>%s</h2></td><td><h2>%s</h2></td></tr></table>"%(frappe.utils.format_date(self.from_date),frappe.utils.format_date(self.to_date),self.from_time,self.to_time)
        return html


    @frappe.whitelist()
    def throw_overlap_error(self, d):
        msg = _("Employee {0} has already applied for {1} between {2} and {3}").format(self.employee,
            d['on_duty_type'], formatdate(d['from_date']), formatdate(d['to_date'])) \
            + """ <br><b><a href="#Form/On Duty Application/{0}">{0}</a></b>""".format(d["name"])
        leave_count_on_half_day_date = frappe.db.sql("""select count(name) from `tabOn Duty Application`
            where employee = %(employee)s
            and docstatus < 2
            and status in ("Open","Applied", "Approved")
            and half_day = 1
            and half_day_date = %(half_day_date)s
            and name != %(name)s""", {
                "employee": self.employee,
                "half_day_date": self.half_day_date,
                "name": self.name
            })[0][0]

        return leave_count_on_half_day_date * 0.5


    @frappe.whitelist()
    def get_hod(self,department):
        hod = frappe.db.get_value('Department',department,"hod")
        return hod

    def validate_if_attendance_not_applicable(employee, attendance_date):
    # Check if attendance_date is a Holiday
        if is_holiday(employee, attendance_date):
            frappe.msgprint(_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date), alert=1)
            return True
        # Check if employee on Leave
        leave_record = frappe.db.sql("""select half_day from `tabLeave Application`
                where employee = %s and %s between from_date and to_date
                and docstatus = 1""", (employee, attendance_date), as_dict=True)
        if leave_record:
            frappe.msgprint(_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, employee), alert=1)
            return True

        return False

def get_holiday_list_for_employee(employee, raise_exception=True):
    if employee:
        holiday_list, company = frappe.db.get_value("Employee", employee, ["holiday_list", "company"])
    else:
        holiday_list=''
        company=frappe.db.get_value("Global Defaults", None, "default_company")

    if not holiday_list:
        holiday_list = frappe.get_cached_value('Company',  company,  "default_holiday_list")

    if not holiday_list and raise_exception:
        frappe.throw(_('Please set a default Holiday List for Employee {0} or Company {1}').format(employee, company))

    return holiday_list

def is_holiday(employee, date=None):
    '''Returns True if given Employee has an holiday on the given date
    :param employee: Employee `name`
    :param date: Date to check. Will check for today if None'''

    holiday_list = get_holiday_list_for_employee(employee)
    if not date:
        date = today()

    if holiday_list:
        return frappe.get_all('Holiday List', dict(name=holiday_list, holiday_date=date)) and True or False


@frappe.whitelist()
def get_number_of_leave_days(employee, from_date, to_date,from_date_session=None,  to_date_session=None, date_dif=None):
    number_of_days = 0
    if from_date == to_date:
        if from_date_session != 'Full Day':
            number_of_days = 0.5
        else:
            number_of_days = 1
    else:
        if from_date_session == "Full Day" and to_date_session == "Full Day":
            number_of_days = flt(date_dif)
        if from_date_session == "Full Day" and to_date_session == "First Half":
            number_of_days = flt(date_dif) - 0.5
        if from_date_session == "Second Half" and to_date_session == "Full Day":
            number_of_days = flt(date_dif) - 0.5
        if from_date_session == "Second Half" and to_date_session == "First Half":
            number_of_days = flt(date_dif) - 1
    return number_of_days

@frappe.whitelist()
def get_time_diff(from_time,to_time):
    total_hours = time_diff_in_hours(to_time,from_time)
    return total_hours

@frappe.whitelist()
def get_time_diff_2(from_time, to_time):
    from datetime import datetime, timedelta

    def parse_time(time_str):
        try:
            return datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return datetime.strptime(time_str, "%H:%M:%S")

    from_time = parse_time(from_time)
    to_time = parse_time(to_time)

    if to_time < from_time:
        to_time += timedelta(days=1)

    total_hours = (to_time - from_time).seconds / 3600
    return total_hours


@frappe.whitelist()
def check_attendance(employee, from_date, to_date):
    if employee:
        attendance = frappe.db.sql("""select status,attendance_date from `tabAttendance`
                    where employee = %s and attendance_date between %s and %s
                    and docstatus = 1""", (employee, from_date, to_date), as_dict=True)
        return attendance

@frappe.whitelist()
def validate_cutoff(from_date):
    cur_mon = datetime.strptime(today(), "%Y-%m-%d").strftime("%B")
    c = frappe.get_value("Application Cut Off Date",{'month':cur_mon},['cut_off_date','from_date','to_date'])
    curday = date.today()
    fromdate = datetime.strptime(str(from_date),"%Y-%m-%d").date()
    if fromdate < c[1]:
        return 'Expired'
    

@frappe.whitelist()
def get_employees():
    data = []
    employee = frappe.db.get_value('Employee',{'status':'Active','user_id':frappe.session.user},["name", "employee_name", "department", "designation"])
    data.append(employee[0])
    data.append(employee[1])
    data.append(employee[2])
    data.append(employee[3])
    return data

def check_holiday(employee, date):
    holiday_list = frappe.db.get_value('Employee', {'name': employee}, 'holiday_list')
    
    holiday = frappe.db.sql("""
        SELECT h.holiday_date, h.weekly_off 
        FROM `tabHoliday List` hl 
        LEFT JOIN `tabHoliday` h ON h.parent = hl.name 
        WHERE hl.name = %s AND h.holiday_date = %s
    """, (holiday_list, date), as_dict=True)
    
    if holiday:
        if holiday[0].weekly_off:
            return "WW"  
        else:
            return "HH"  
    
    return None  


        
