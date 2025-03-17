import frappe
from frappe import get_doc
from frappe.utils import getdate
from datetime import datetime
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form
from frappe.utils.data import date_diff, now_datetime, nowdate, today, add_days,comma_sep
from frappe.model.naming import parse_naming_series
import re
from frappe.utils import get_url_to_form,money_in_words
from frappe.utils import money_in_words
from frappe.utils import date_diff, add_months, today,nowtime,nowdate,format_date
from datetime import date, datetime,timedelta
import math
from frappe import _
from time import strptime
from datetime import datetime,time
from typing import Dict, Optional, Tuple, Union
from erpnext.setup.doctype.employee.employee import get_all_employee_emails, get_employee_email
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

# Get the designation value from Agency to match with employee agency
@frappe.whitelist()
def get_designation(name):
    doc = frappe.get_doc("Agency", name)
    states = [state.designation for state in doc.agency_wages]
    return states

# Update all values for employee like basic,special allowance from Agency
@frappe.whitelist()	
def update_agency_wages(doc,method):
    ss=frappe.get_doc("Employee",doc.name)
    if ss.employment_type == "Agency" and ss.designation:
            basic = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['basic'])
            frappe.db.set_value("Employee",doc.employee_number,"custom_basic",basic)
            ss.custom_basic=basic
            # ss.save(ignore_permissions=True)
            # frappe.db.commit()
            dearness_allowance = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['dearness_allowance'])
            frappe.db.set_value("Employee", doc.name, "custom_dearness_allowance", dearness_allowance)
            ss.custom_dearness_allowance=dearness_allowance
            special_allowance_ = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['special_allowance'])
            frappe.db.set_value("Employee",doc.name,"custom_special_allowance_",special_allowance_)
            earning_provident_fund_13 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['earning_provident_fund_13'])
            frappe.db.set_value("Employee",doc.name,"custom_pf",earning_provident_fund_13)
            earning_esi_325 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['earning_esi_325'])
            frappe.db.set_value("Employee",doc.name,"custom_esi",earning_esi_325)
            service_charges_8 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['service_charge'])
            frappe.db.set_value("Employee",doc.name,"custom_service_chrages",service_charges_8)
            deduction_pf_12 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['deduction_pf_12'])
            frappe.db.commit()
    


#Set the employee id based on Category

@frappe.whitelist()
def set_naming(employee_category):
    if frappe.db.exists("Employee", {'custom_employee_category': employee_category}):
        if employee_category in ('Blue Collar'):
            query = frappe.db.sql("""
                    SELECT name FROM `tabEmployee`
                    WHERE custom_employee_category = '%s'
                    ORDER BY name DESC
                    """ % (employee_category), as_dict=1)[0]
            input_string = query['name']
            match = re.search(r'(\d+)$', input_string)
            if match:
                number = match.group(1)
                leng = int(number) + 1
                str_len = str(leng)
                lengt = len(str_len)
                ty = str(lengt)

                if ty == "3":
                    code = "W" + "0" + str(leng)
                elif ty == "2":
                    code = "W" + "00" + str(leng)
                elif ty == "1":
                    code = "W" + "000" + str(leng)
                else:
                    code = "W" + str(leng)
        
        else:
            query = frappe.db.sql("""
                SELECT name FROM `tabEmployee`
                WHERE custom_employee_category in ('White Collar','Grey Collar')
                ORDER BY name DESC
                """, as_dict=1)[0]

            input_string = query['name']
            match = re.search(r'(\d+)$', input_string)

            if match:
                number = match.group(1)
                leng = int(number) + 1
                str_len = str(leng)
                lengt = len(str_len)
                ty = str(lengt)

                if ty == "3":
                    code = "S" + "0" + str(leng)
                elif ty == "2":
                    code = "S" + "00" + str(leng)
                elif ty == "1":
                    code = "S" + "000" + str(leng)
                else:
                    code = "S" + str(leng)

        return code

#Get the sum of payment days to match with agency and designation and set in to agency invoice
@frappe.whitelist()
def get_md(agency_name,branch,employee_category,start_date,end_date,designation):
    mdr = frappe.get_value('Agency Wages',{'designation':designation,'parent':agency_name},['total'])
    tar = frappe.get_value('Agency Wages',{'designation':designation,'parent':agency_name},['travel_allowance_rate'])
    man_days = frappe.db.sql("""select designation,sum(payment_days) from `tabSalary Slip` where docstatus != 2 and agency_name ='%s' and employee_category='%s' and branch = '%s' and start_date = '%s' and end_date = '%s' and designation = '%s' """%(agency_name,employee_category,start_date,end_date,designation),as_dict = 1)[0]
    # ot = frappe.db.sql("""select (sum(overtime_hours))  as ot_hrs from `tabSalary Slip` where docstatus != 2  and agency_name ='%s' and employee_category='%s' and branch ='%s' and start_date = '%s' and end_date = '%s' and designation = '%s' """%(agency_name,employee_category,start_date,end_date,designation),as_dict = 1)[0]
    return man_days['sum(payment_days)'] or 0 , mdr or 0 ,tar or 0


#Check the below condition and allocate the earned leave for every employees
@frappe.whitelist()
def update_earned_leave():
    start_date = date.today() - timedelta(days=30)
    end_date = date.today()
    next_year = date.today().year + 1
    start = date(next_year, 1, 1)
    end = date(next_year, 12, 31)
    employees = frappe.get_all("Employee", {"status": "Active"}, ["name", "company"])
    for emp in employees:
        present = frappe.db.sql("""SELECT COUNT(*)
                FROM `tabAttendance`
                WHERE `employee` = '%s'
                AND `status` = 'Present'
                AND `attendance_date` BETWEEN '%s' AND '%s'""" % (emp.name, start_date, end_date), as_dict=True)
                
        half_day = frappe.db.sql("""SELECT COUNT(*)
                FROM `tabAttendance`
                WHERE `employee` = '%s'
                AND `status` = 'Half Day'
                AND `attendance_date` BETWEEN '%s' AND '%s'""" % (emp.name, start_date, end_date), as_dict=True)
                
        half = half_day[0]['COUNT(*)'] / 2
        attendance = present[0]['COUNT(*)'] + half
        earned_leave=attendance/20
        rounded_earned_leave = math.floor(earned_leave)
        if rounded_earned_leave:
            existing_allocation = frappe.db.exists("Leave Allocation", {"employee": emp.name, "docstatus": ("!=", 2), "leave_type": "Earned Leave", "from_date": start})
            if not existing_allocation:
                new_allocation = frappe.new_doc("Leave Allocation")
                new_allocation.employee = emp.name
                new_allocation.company = emp.company
                new_allocation.leave_type = "Earned Leave"
                new_allocation.from_date = start
                new_allocation.to_date = end
                new_allocation.new_leaves_allocated = rounded_earned_leave
                new_allocation.total_leaves_allocated = rounded_earned_leave
                new_allocation.save(ignore_permissions=True)
                new_allocation.submit()
            else:
                leave_allocation = frappe.get_doc("Leave Allocation", existing_allocation)
                leave_allocation.new_leaves_allocated += rounded_earned_leave
                leave_allocation.total_leaves_allocated += rounded_earned_leave
                leave_allocation.save(ignore_permissions=True)			
    frappe.db.commit()



#Check the holiday list for employee
from datetime import timedelta, time
@frappe.whitelist()
def check_holiday(date, emp):
    holiday_list = frappe.db.get_value('Employee', {'name': emp}, 'holiday_list')
    holiday = frappe.db.sql("""SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off
                             FROM `tabHoliday List`
                             LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name
                             WHERE `tabHoliday List`.name = %s AND holiday_date = %s""",
                            (holiday_list, date), as_dict=True)
    doj = frappe.db.get_value("Employee", {'name': emp}, "date_of_joining")
    status = ''
    if holiday:
        return holiday

#Create OT Request check with below conditions
@frappe.whitelist()
def update_ot_request(from_date,to_date):
    attendance = frappe.get_all("Attendance", {"attendance_date":("between",(from_date,to_date))}, ["*"])
    for i in attendance:
        doc = frappe.get_doc("Attendance",i.name)
        date = doc.attendance_date
        hh= check_holiday(date,doc.employee)
        # shift = attendance.get("shift")
        employement_type = frappe.db.get_value("Employee",{"name":doc.employee},["employment_type"])
        if not employement_type =="Agency":
            if not hh:
                if doc.custom_employee_category =="White Collar":
                    applicable = frappe.db.get_value("Employee",{"name":doc.employee},["custom_ot_applicable"])
                    if applicable ==1:
                        if doc.shift and doc.in_time and doc.out_time:
                            if doc.status == "Half Day" or doc.status == "Present":
                                if isinstance(doc.custom_ot_hours, str):
                                    custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                                    ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                                else:
                                    ot_timedelta = doc.custom_ot_hours
                                if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                                    
                                    if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                                        req = frappe.new_doc("Over Time Request")
                                        req.employee = doc.employee
                                        req.normal_employee = 1
                                        req.ot_date = date
                                        req.ot_hour = doc.custom_ot_hours
                                        req.planned_hour = time(0, 0, 0)
                                        req.shift = doc.shift
                                        req.save(ignore_permissions=True)
                                        frappe.db.commit()
                                        print(req.name)
                                            
                                    else:
                                        value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                                        document = frappe.get_doc("Over Time Request",value)
                                        document.ot_hour = doc.custom_ot_hours
                                        document.save(ignore_permissions=True)
                                        frappe.db.commit()

                elif not doc.custom_employee_category =="White Collar":
                    if doc.shift and doc.in_time and doc.out_time:
                        if doc.status == "Half Day" or doc.status == "Present":
                            if isinstance(doc.custom_ot_hours, str):
                                custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                                ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                            else:
                                ot_timedelta = doc.custom_ot_hours
                            if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):                            
                                if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.normal_employee = 1
                                    req.ot_date = date
                                    req.ot_hour = doc.custom_ot_hours
                                    req.planned_hour = time(0, 0, 0)
                                    req.shift = doc.shift
                                    req.save(ignore_permissions=True)
                                    frappe.db.commit()
                                    print(req.name)
                                
                                else:
                                    value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                                    document = frappe.get_doc("Over Time Request",value)
                                    document.ot_hour = doc.custom_ot_hours
                                    document.save(ignore_permissions=True)
                                    frappe.db.commit()    
            else:
                if doc.custom_employee_category =="White Collar":
                    applicable = frappe.db.get_value("Employee",{"name":doc.employee},["custom_ot_applicable"])
                    if applicable ==1:
                        if doc.shift and doc.in_time and doc.out_time:
                            if isinstance(doc.custom_ot_hours, str):
                                custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                                ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                            else:
                                ot_timedelta = doc.custom_ot_hours
                            if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                                
                                if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.normal_employee = 1
                                    req.ot_date = date
                                    req.ot_hour = doc.custom_ot_hours
                                    req.planned_hour = time(0, 0, 0)
                                    req.shift = doc.shift
                                    req.save(ignore_permissions=True)
                                    frappe.db.commit()
                                    print(req.name)
                                else:
                                    value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                                    document = frappe.get_doc("Over Time Request",value)
                                    document.ot_hour = doc.custom_ot_hours
                                    document.save(ignore_permissions=True)
                                    frappe.db.commit()
                elif not doc.custom_employee_category =="White Collar":
                    if doc.shift and doc.in_time and doc.out_time:
                        if isinstance(doc.custom_ot_hours, str):
                            custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                            ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                        else:
                            ot_timedelta = doc.custom_ot_hours
                        if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                            if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                                req = frappe.new_doc("Over Time Request")
                                req.employee = doc.employee
                                req.normal_employee = 1
                                req.ot_date = date
                                req.ot_hour = doc.custom_ot_hours
                                req.planned_hour = time(0, 0, 0)
                                req.shift = doc.shift
                                req.save(ignore_permissions=True)
                                frappe.db.commit()
                                print(req.name)    

                            else:
                                value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                                document = frappe.get_doc("Over Time Request",value)
                                document.ot_hour = doc.custom_ot_hours
                                document.save(ignore_permissions=True)
                                frappe.db.commit()
                                
        elif employement_type =="Agency":
            if hh:
                if doc.shift and doc.in_time and doc.out_time:
                    if doc.status == "Half Day" or doc.status == "Present":
                        if isinstance(doc.custom_ot_hours, str):
                            custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                            ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                        else:
                            ot_timedelta = doc.custom_ot_hours
                        if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):                            
                            if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                                req = frappe.new_doc("Over Time Request")
                                req.employee = doc.employee
                                req.agency_employee =1
                                req.ot_date = date
                                req.ot_hour = doc.custom_ot_hours
                                req.planned_hour = time(0, 0, 0)
                                req.shift = doc.shift
                                req.save(ignore_permissions=True)
                                frappe.db.commit()
                                print(req.name)
                            
                            else:
                                value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                                document = frappe.get_doc("Over Time Request",value)
                                document.ot_hour = doc.custom_ot_hours
                                document.save(ignore_permissions=True)
                                frappe.db.commit()    
            else:
                if doc.shift and doc.in_time and doc.out_time:
                    if isinstance(doc.custom_ot_hours, str):
                        custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                        ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                    else:
                        ot_timedelta = doc.custom_ot_hours
                    if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                        if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                            req = frappe.new_doc("Over Time Request")
                            req.employee = doc.employee
                            req.agency_employee = 1
                            req.ot_date = date
                            req.ot_hour = doc.custom_ot_hours
                            req.planned_hour = time(0, 0, 0)
                            req.shift = doc.shift
                            req.save(ignore_permissions=True)
                            frappe.db.commit()
                            print(req.name)    

                        else:
                            value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                            document = frappe.get_doc("Over Time Request",value)
                            document.ot_hour = doc.custom_ot_hours
                            document.save(ignore_permissions=True)
                            frappe.db.commit()
#Expire the Comp off leave if not used within 60 days      
@frappe.whitelist()
def comp_req():
    todays= datetime.strptime(nowdate(), '%Y-%m-%d').date()
    comp=frappe.db.get_all("Compensatory Off Request",{"docstatus":1},['from_date','employee'])
    for i in comp:
        diff = date_diff(todays,i.from_date)
        if diff ==60:
            leave_app= frappe.db.sql("select * from `tabLeave Application` where employee = '%s' and from_date between '%s' and '%s' and workflow_state != 'Rejected' and docstatus!=2 "%(i.employee,i.from_date,todays),as_dict=True)
            if not leave_app:
                leaves=frappe.db.get_all("Leave Ledger Entry",{"leave_type":'Compensatory Off','employee':i.employee},['creation','name'])
                for j in leaves:
                    diff = date_diff(todays,j.creation)
                    if diff<=60:
                        frappe.db.set_value("Leave Ledger Entry",j.name,'is_expired',1)   
   
def time_diff_in_timedelta_1(time1, time2):
    datetime1 = datetime.combine(datetime.min, time1)
    datetime2 = datetime.combine(datetime.min, time2)
    timedelta_seconds = (datetime2 - datetime1).total_seconds()
    diff_timedelta = timedelta(seconds=timedelta_seconds)
    return diff_timedelta



@frappe.whitelist()
def absent_mail_alert():
    yesterday = add_days(frappe.utils.today(),-1)
    attendance = frappe.db.sql("""
        SELECT * FROM `tabAttendance` left join `tabEmployee` ON `tabAttendance`.employee = `tabEmployee`.name
        WHERE `tabAttendance`.attendance_date = %s AND `tabAttendance`.status = "Absent" AND `tabAttendance`.docstatus != "2" AND `tabEmployee`.employment_type != 'Agency'
        ORDER BY `tabAttendance`.employee
    """, (yesterday), as_dict=True)
    
    
    
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">Absent Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.NO</th>
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Department</th>
                <th style="padding: 4px; border: 1px solid black;">Attendance</th>
                <th style="padding: 4px; border: 1px solid black;">Reason</th>
            </tr>
    """

    idx = 1  
    reason=''
    for att in attendance:
        shift=frappe.db.get_value("Shift Assignment",att.shift,"name")
        
        if not att.in_time or not att.out_time:
            reason = "Absent"
        elif att.shift:
            if att.shift !=shift:
                reason = "Wrong Shift" 
            else:
                reason = "Absent"      
        staff += """
        <tr style="border: 1px solid black;">
            <td style="padding: 4px; border: 1px solid black;">{0}</td>
            <td style="padding: 4px; border: 1px solid black;">{1}</td>
            <td style="padding: 4px; border: 1px solid black;">{2}</td>
            <td style="padding: 4px; border: 1px solid black;">{3}</td>
            <td style="padding: 4px; border: 1px solid black;">{4}</td>
            <td style="padding: 4px; border: 1px solid black;">{5}</td>
        </tr>
        """.format(idx, att.employee, att.employee_name, att.department, att.name or ' ',reason)
        idx += 1  

    staff += "</table>"
    
    user = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name 
        WHERE `tabHas Role`.Role = "HR User" AND `tabUser`.enabled = 1
    """, as_dict=True)
    
    if attendance:
        for i in user:
            frappe.sendmail(
                recipients=[i.name],
                subject='Absent Report',
                message="""Dear Sir/Mam,<br><br>
                    Kindly Check the Absent Employee List for yesterday ({1}):<br>{0}
                    """.format(staff, format_date(yesterday))
            )
        
        frappe.sendmail(
            # recipients=['siva.m@groupteampro.com','hr@irecambioindia.com'],
            recipients=[ 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com','jenisha.p@groupteampro.com','sarath.v@groupteampro.com'],
            subject='Absent Report',
            message="""Dear Sir,<br><br>
                Kindly find the attached Employee Absent Employee List for yesterday({1}):<br>{0}
                """.format(staff,format_date(yesterday))
        )

@frappe.whitelist()
def od_report():
    yesterday = add_days(frappe.utils.today(), -1)
    employee = frappe.db.sql("""
        SELECT * FROM `tabOn Duty Application` left join `tabEmployee` ON `tabOn Duty Application`.employee = `tabEmployee`.name
        WHERE `tabOn Duty Application`.from_date = %s  AND `tabOn Duty Application`.docstatus = "1" AND `tabEmployee`.employment_type != 'Agency'
        ORDER BY `tabOn Duty Application`.employee
    """, (yesterday), as_dict=True)
    
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">On Duty Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.No</th>
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Department</th>
                <th style="padding: 4px; border: 1px solid black;">On Duty</th>
                <th style="padding: 4px; border: 1px solid black;">Session</th>
            </tr>
    """
    
    idx = 1  # Initialize the serial number
    
    for i in employee:
        staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black;">{3}</td>
                <td style="padding: 4px; border: 1px solid black;">{4}</td>
                <td style="padding: 4px; border: 1px solid black;">{5}</td>
            </tr>
        """.format(idx, i.employee, i.employee_name, i.department, i.name or ' ', i.from_date_session or '')
        
        idx += 1  # Increment the serial number
    
    staff += "</table>"
    
    user = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.Role = "HR User" AND `tabUser`.enabled = 1
        """, as_dict=True)
    
    if employee:
        for i in user:
            frappe.sendmail(
                recipients=[i.name],
                subject='On Duty Application Report',
                message="""Dear Sir/Madam,<br><br>
                        Kindly check the On Duty Employee List for yesterday ({1}):<br>{0}
                        """.format(staff, format_date(yesterday))
            )
        frappe.sendmail(
            recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='On Duty Application Report',
            message="""Dear Sir,<br><br>
                    Kindly find the attached Employee On Duty Application List for yesterday:<br>{0}
                    """.format(staff)
        )


@frappe.whitelist()
def permission_request_report():
    yesterday = add_days(frappe.utils.today(), -1)
    permission = frappe.db.sql("""
        SELECT * FROM `tabPermission Request` left join `tabEmployee` ON `tabPermission Request`.employee = `tabEmployee`.name
        WHERE `tabPermission Request`.attendance_date = %s AND `tabPermission Request`.docstatus = 1 and `tabEmployee`.employment_type != 'Agency'
        ORDER BY `tabPermission Request`.employee
    """, (yesterday,), as_dict=True)

    if not permission:
        return "No permission requests found for yesterday."

    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">Permission Request Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.No</th>
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Permission Request</th>
                <th style="padding: 4px; border: 1px solid black;">Session</th>
            </tr>
    """
    
    idx = 1  # Initialize the serial number

    for per in permission:
        staff += """
        <tr style="border: 1px solid black;">
            <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
            <td style="padding: 4px; border: 1px solid black;">{1}</td>
            <td style="padding: 4px; border: 1px solid black;">{2}</td>
            <td style="padding: 4px; border: 1px solid black;">{3}</td>
            <td style="padding: 4px; border: 1px solid black;">{4}</td>
        </tr>
        """.format(idx, per.employee, per.employee_name, per.name or ' ', per.session or '')

        idx += 1  # Increment the serial number

    staff += "</table>"

    users = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.Role = "HR User" AND `tabUser`.enabled = 1
    """, as_dict=True)

    if permission:
        for user in users:
            frappe.sendmail(
                recipients=[user.name],
                subject='Permission Request Report',
                message="""Dear Sir/Madam,<br><br>
                    Kindly check the permission request employee list for yesterday ({1}):<br>{0}
                    """.format(staff, format_date(yesterday))
            ) 
        frappe.sendmail(
            recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='Permission Request Report',
            message="""Dear Sir,<br><br>
                Kindly find the attached employee permission request list for yesterday:<br>{0}
                """.format(staff)
        )


@frappe.whitelist()
def permission_request_firstmanager():
    
    permission_requests = frappe.db.sql("""
        SELECT `tabPermission Request`.name, `tabPermission Request`.employee, 
        `tabPermission Request`.employee_name, `tabPermission Request`.session, `tabPermission Request`.custom_first_manager
        FROM `tabPermission Request`
        LEFT JOIN `tabEmployee`
        ON `tabPermission Request`.employee = `tabEmployee`.name
        WHERE `tabPermission Request`.workflow_state="FM Pending" and `tabEmployee`.employment_type != 'Agency'
        ORDER BY `tabPermission Request`.employee
    """, as_dict=True)

    if not permission_requests:
        return "No permission requests found in 'FM Pending' state."

    managers_permissions = {}
    for per in permission_requests:
        if per.custom_first_manager in managers_permissions:
            managers_permissions[per.custom_first_manager].append(per)
        else:
            managers_permissions[per.custom_first_manager] = [per]

    for manager, requests in managers_permissions.items():
        if manager:  
            staff = """
            <div style="text-align: center;">
                <h2 style="font-size: 16px;">Permission Request Report</h2>
            </div>
            <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                <tr style="border: 1px solid black;">
                    <th style="padding: 4px; border: 1px solid black;">S.No</th>
                    <th style="padding: 4px; border: 1px solid black;">Employee</th>
                    <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                    <th style="padding: 4px; border: 1px solid black;">Permission Request</th>
                    <th style="padding: 4px; border: 1px solid black;">Session</th>
                </tr>
            """

            idx = 1  # Initialize the serial number

            for per in requests:
                staff += """
                <tr style="border: 1px solid black;">
                    <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
                    <td style="padding: 4px; border: 1px solid black;">{1}</td>
                    <td style="padding: 4px; border: 1px solid black;">{2}</td>
                    <td style="padding: 4px; border: 1px solid black;">{3}</td>
                    <td style="padding: 4px; border: 1px solid black;">{4}</td>
                </tr>
                """.format(idx, per.employee, per.employee_name, per.name or ' ', per.session or '')

                idx += 1  # Increment the serial number

            staff += "</table>"

            frappe.sendmail(
                recipients=[manager],
                subject='Permission Request Report',
                message="""Dear Sir/Madam,<br><br>
                Kindly find the list of Permission Requests waiting for your approval:<br>{0}
                """.format(staff)
            )

    # Send report to additional recipients
    frappe.sendmail(
        recipients=['sarath.v@groupteampro.com','siva.m@groupteampro.com', 'arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
        subject='Permission Request Report',
        message="""Dear Sir,<br><br>
        Kindly find the list of Permission Requests waiting for approval:<br>{0}
        """.format(staff)
    )
    

@frappe.whitelist()
def permission_request_secondmanager():
    
    permission_requests = frappe.db.sql("""
        SELECT `tabPermission Request`.name, `tabPermission Request`.employee, 
        `tabPermission Request`.employee_name, `tabPermission Request`.session, `tabPermission Request`.custom_second_manager
        FROM `tabPermission Request` LEFT JOIN `tabEmployee`
        ON `tabPermission Request`.employee = `tabEmployee`.name
        WHERE `tabPermission Request`.workflow_state="SM Pending" and `tabEmployee`.employment_type != 'Agency'
        ORDER BY `tabPermission Request`.employee
    """, as_dict=True)

    if not permission_requests:
        return "No permission requests found in 'SM Pending' state."

    managers_permissions = {}
    for per in permission_requests:
        if per.custom_second_manager in managers_permissions:
            managers_permissions[per.custom_second_manager].append(per)
        else:
            managers_permissions[per.custom_second_manager] = [per]

    for manager, requests in managers_permissions.items():
        if manager:  
            staff = """
            <div style="text-align: center;">
                <h2 style="font-size: 16px;">Permission Request Report</h2>
            </div>
            <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                <tr style="border: 1px solid black;">
                    <th style="padding: 4px; border: 1px solid black;">S.No</th>
                    <th style="padding: 4px; border: 1px solid black;">Employee</th>
                    <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                    <th style="padding: 4px; border: 1px solid black;">Permission Request</th>
                    <th style="padding: 4px; border: 1px solid black;">Session</th>
                </tr>
            """

            idx = 1  # Initialize the serial number

            for per in requests:
                staff += """
                <tr style="border: 1px solid black;">
                    <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
                    <td style="padding: 4px; border: 1px solid black;">{1}</td>
                    <td style="padding: 4px; border: 1px solid black;">{2}</td>
                    <td style="padding: 4px; border: 1px solid black;">{3}</td>
                    <td style="padding: 4px; border: 1px solid black;">{4}</td>
                </tr>
                """.format(idx, per.employee, per.employee_name, per.name or ' ', per.session or '')

                idx += 1  # Increment the serial number

            staff += "</table>"

            frappe.sendmail(
                recipients=[manager],
                subject='Permission Request Report',
                message="""Dear Sir/Madam,<br><br>
                Kindly find the list of Permission Requests waiting for your approval:<br>{0}
                """.format(staff)
            )

    # Send report to additional recipients
    frappe.sendmail(
        recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'siva.m@groupteampro.com', 'jenisha.p@groupteampro.com'],
        subject='Permission Request Report',
        message="""Dear Sir,<br><br>
        Kindly find the list of Permission Requests waiting for your approval:<br>{0}
        """.format(staff)
    )


@frappe.whitelist()
def leave_application_secondmanager_test():
    
    leave_applications = frappe.db.sql("""
        SELECT `tabLeave Application`.name, `tabLeave Application`.employee, `tabLeave Application`.employee_name, `tabLeave Application`.leave_type, `tabLeave Application`.custom_second_manager
        FROM `tabLeave Application` LEFT JOIN  `tabEmployee`
        ON `tabLeave Application`.employee = `tabEmployee`.name
        WHERE `tabLeave Application`.workflow_state="SM Pending" and `tabEmployee`.employment_type != 'Agency'
        ORDER BY `tabLeave Application`.employee
    """, as_dict=True)

    if leave_applications:
        managers_leaves = {}
        for lve in leave_applications:
            if lve.custom_second_manager in managers_leaves:
                managers_leaves[lve.custom_second_manager].append(lve)
            else:
                managers_leaves[lve.custom_second_manager] = [lve]

        for manager, applications in managers_leaves.items():
            if manager:
                idx = 1  # Initialize the serial number before the loop
                staff = """
                <div style="text-align: center;">
                    <h2 style="font-size: 16px;">Leave Application Report</h2>
                </div>
                <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                    <tr style="border: 1px solid black;">
                        <th style="padding: 4px; border: 1px solid black;">S.No</th>
                        <th style="padding: 4px; border: 1px solid black;">Employee</th>
                        <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                        <th style="padding: 4px; border: 1px solid black;">Leave</th>
                        <th style="padding: 4px; border: 1px solid black;">Leave Type</th>
                    </tr>
                """

                for lve in applications:
                    staff += """
                    <tr style="border: 1px solid black;">
                        <td style="padding: 4px; border: 1px solid black;">{0}</td>
                        <td style="padding: 4px; border: 1px solid black;">{1}</td>
                        <td style="padding: 4px; border: 1px solid black;">{2}</td>
                        <td style="padding: 4px; border: 1px solid black;">{3}</td>
                        <td style="padding: 4px; border: 1px solid black;">{4}</td>
                    </tr>
                    """.format(idx, lve.employee, lve.employee_name, lve.name or ' ', lve.leave_type or '')
                    idx += 1  # Increment the serial number after each iteration

                staff += "</table>"

                frappe.sendmail(
                    recipients=[manager],
                    subject='Leave Application Report',
                    message="""Dear Sir/Madam,<br><br>
                    Kindly find the list of Leave Applications waiting for your approval:<br>{0}
                    """.format(staff)
                )

        frappe.sendmail(
            recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='Leave Application Report',
            message="""Dear Sir,<br><br>
            Kindly find the list of Leave Applications waiting for your approval:<br>{0}
            """.format(staff)
        )


@frappe.whitelist()
def leave_application_firstmanager_test():
    
    leave_applications = frappe.db.sql("""
        SELECT `tabLeave Application`.name, `tabLeave Application`.employee, `tabLeave Application`.employee_name, `tabLeave Application`.leave_type, `tabLeave Application`.custom_first_manager
        FROM `tabLeave Application` LEFT JOIN `tabEmployee`
        ON `tabLeave Application`.employee = `tabEmployee`.name
        WHERE `tabLeave Application`.workflow_state="FM Pending" and `tabEmployee`.employment_type !='Agency'
        ORDER BY `tabLeave Application`.employee
    """, as_dict=True)

    if leave_applications:
        managers_leaves = {}
        for lve in leave_applications:
            if lve.custom_first_manager in managers_leaves:
                managers_leaves[lve.custom_first_manager].append(lve)
            else:
                managers_leaves[lve.custom_first_manager] = [lve]

        idx = 1  # Initialize the serial number before the loop
        for manager, applications in managers_leaves.items():
            if manager:
                staff = """
                <div style="text-align: center;">
                    <h2 style="font-size: 16px;">Leave Application Report</h2>
                </div>
                <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                    <tr style="border: 1px solid black;">
                        <th style="padding: 4px; border: 1px solid black;">S.No</th>
                        <th style="padding: 4px; border: 1px solid black;">Employee</th>
                        <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                        <th style="padding: 4px; border: 1px solid black;">Leave</th>
                        <th style="padding: 4px; border: 1px solid black;">Leave Type</th>
                    </tr>
                """

                for lve in applications:
                    staff += """
                    <tr style="border: 1px solid black;">
                        <td style="padding: 4px; border: 1px solid black;">{0}</td>
                        <td style="padding: 4px; border: 1px solid black;">{1}</td>
                        <td style="padding: 4px; border: 1px solid black;">{2}</td>
                        <td style="padding: 4px; border: 1px solid black;">{3}</td>
                        <td style="padding: 4px; border: 1px solid black;">{4}</td>
                    </tr>
                    """.format(idx, lve.employee, lve.employee_name, lve.name or ' ', lve.leave_type or '')
                    idx += 1  # Increment the serial number after each iteration

                staff += "</table>"

                frappe.sendmail(
                    recipients=[manager],
                    subject='Leave Application Report',
                    message="""Dear Sir/Madam,<br><br>
                    Kindly find the list of Leave Applications waiting for your approval:<br>{0}
                    """.format(staff)
                )

        frappe.sendmail(
            recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='Leave Application Report',
            message="""Dear Sir,<br><br>
            Kindly find the list of Leave Applications waiting for your approval:<br>{0}
            """.format(staff)
        )


@frappe.whitelist()
def leave_application_hod_format():
    
    leave = frappe.db.sql("""
        SELECT `tabLeave Application`.name, `tabLeave Application`.employee, `tabLeave Application`.employee_name, `tabLeave Application`.department, `tabLeave Application`.leave_type, `tabLeave Application`.from_date, `tabLeave Application`.to_date
        FROM `tabLeave Application` LEFT JOIN `tabEmployee`
        ON `tabLeave Application`.employee = `tabEmployee`.name
        WHERE workflow_state = 'HR Pending' and `tabEmployee`.employment_type !='Agency'
        ORDER BY name
    """, as_dict=True)
    
    if not leave:
        return "No leave applications are currently pending approval."

    # Initialize idx manually
    idx = 1
    
    # HTML template for the report
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">Leave Application Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.No</th>
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Department</th>
                <th style="padding: 4px; border: 1px solid black;">Document ID</th>
                <th style="padding: 4px; border: 1px solid black;">From date</th>
                <th style="padding: 4px; border: 1px solid black;">To Date</th>
                <th style="padding: 4px; border: 1px solid black;">Leave Type</th>
            </tr>
    """

    # Loop through the leave applications and add them to the table
    for lve in leave:
        staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black;">{3}</td>
                <td style="padding: 4px; border: 1px solid black;">{4}</td>
                <td style="padding: 4px; border: 1px solid black;">{5}</td>
                <td style="padding: 4px; border: 1px solid black;">{6}</td>
                <td style="padding: 4px; border: 1px solid black;">{7}</td>
            </tr>
        """.format(idx, lve.employee, lve.employee_name, lve.department, lve.name or ' ',format_date(lve.from_date),format_date(lve.to_date), lve.leave_type or '')
        
        # Increment idx after adding each row
        idx += 1

    staff += "</table>"

    # Get HR users
    hr_users = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.role = 'HR User' AND `tabUser`.enabled = 1
    """, as_dict=True)

    # Send emails to HR users
    for user in hr_users:
        frappe.sendmail(
            recipients=[user.name],
            subject='Leave Application Report - HR Pending',
            message="""Dear Sir/Madam,<br><br>
                Kindly find the list of leave applications waiting for your approval:<br>{0}
            """.format(staff)
        )
    
    # Send a copy of the report to specific recipients
    frappe.sendmail(
        recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com','siva.m@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'jenisha.p@groupteampro.com'],
        # recipients=['arockia.k@groupteampro.com', 'jenisha.p@groupteampro.com'],
        subject='Leave Application Report - HR Pending',
        message="""Dear Sir,<br><br>
            Kindly find the list of leave applications waiting for your approval:<br>{0}
        """.format(staff)
    )


@frappe.whitelist()
def od_hod():
    employee = frappe.db.sql("""
        SELECT `tabOn Duty Application`.employee, `tabOn Duty Application`.employee_name ,
        `tabOn Duty Application`.name,`tabOn Duty Application`.from_date_session,
        `tabOn Duty Application`.workflow_state
        FROM `tabOn Duty Application` 
        JOIN `tabEmployee`
        ON `tabOn Duty Application`.employee = `tabEmployee`.name 
        where `tabOn Duty Application`.Workflow_state="HR Pending" and `tabEmployee`.employment_type !='Agency'
        """,as_dict=True)
    
    staff = """
        <div style="text-align: center;">
                <h2 style="font-size: 16px;">On Duty Report</h2>
            </div>
            <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                <tr style="border: 1px solid black;">
                    <th style="padding: 4px; border: 1px solid black;">Employee</th>
                    <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                    <th style="padding: 4px; border: 1px solid black;">On Duty</th>
                    <th style="padding: 4px; border: 1px solid black;">Session</th>

                </tr>
    """	
    
    for i in employee:
            
        staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black;">{3}</td>
                
            </tr>
            """.format(i.employee, i.employee_name,
                    i.name or ' ',i.from_date_session or '')
    staff += "</table>"
    user = frappe.db.sql("""
                    SELECT `tabUser`.name as name
                    FROM `tabUser`
                    LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name where `tabHas Role`.Role="HOD" and `tabUser`.enabled=1
                    """,as_dict=True)
    if employee:
        for j in user:
            frappe.sendmail(
                recipients=[j.name],
                subject='On Duty Application Report',
                message="""Dear Sir/Mam,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )
        frappe.sendmail(
                recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='On Duty Application Report',
                message="""Dear Sir,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )


@frappe.whitelist()
def od_firstmanager_format():
    try:
        # Fetch On Duty applications pending for the first manager's approval
        employees = frappe.db.sql("""
        SELECT `tabOn Duty Application`.employee, `tabOn Duty Application`.employee_name , `tabOn Duty Application`.name,`tabOn Duty Application`.from_date_session,`tabOn Duty Application`.workflow_state
        FROM `tabOn Duty Application` 
        RIGHT JOIN `tabEmployee`
        ON `tabOn Duty Application`.employee = `tabEmployee`.name where `tabOn Duty Application`.Workflow_state="FM Pending" and `tabEmployee`.employment_type !='Agency'
        """,as_dict=True)


        if employees:
            # Organize On Duty applications by manager
            managers_reports = {}
            for emp in employees:
                if emp.custom_first_manager:
                    if emp.custom_first_manager not in managers_reports:
                        managers_reports[emp.custom_first_manager] = []
                    managers_reports[emp.custom_first_manager].append(emp)

            # Send emails to each manager
            for manager, reports in managers_reports.items():
                staff_report = """
                <div style="text-align: center;">
                    <h2 style="font-size: 16px;">On Duty Report</h2>
                </div>
                <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                    <tr>
                        <th style="padding: 4px; border: 1px solid black;">Employee</th>
                        <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                        <th style="padding: 4px; border: 1px solid black;">On Duty</th>
                        <th style="padding: 4px; border: 1px solid black;">Session</th>
                    </tr>
                """
                
                for report in reports:
                    staff_report += """
                    <tr>
                        <td style="padding: 4px; border: 1px solid black;">{0}</td>
                        <td style="padding: 4px; border: 1px solid black;">{1}</td>
                        <td style="padding: 4px; border: 1px solid black;">{2}</td>
                        <td style="padding: 4px; border: 1px solid black;">{3}</td>
                    </tr>
                    """.format(report.employee, report.employee_name, report.name or ' ', report.from_date_session or '')

                staff_report += "</table>"

                frappe.sendmail(
                    recipients=[manager],
                    subject='On Duty Application Report',
                    message="""Dear Sir/Madam,<br><br>
                    Kindly find the list of On Duty Applications waiting for your approval:<br>{0}
                    """.format(staff_report)
                )

            # Send a general report to predefined email addresses
                general_report = staff_report  # Use the same report as it's the consolidated view
                frappe.sendmail(
                    recipients=['jenisha.p@groupteampro.com'],
                    subject='On Duty Application Report',
                    message="""Dear Sir,<br><br>
                    Kindly find the list of On Duty Applications waiting for your approval:<br>{0}
                    """.format(general_report)
                )

    except Exception as e:
        # Log any exceptions that occur
        frappe.log_error(f"Error in od_firstmanager: {str(e)}", "On Duty Application Report Error")

@frappe.whitelist()
def od_secondmanager():
    employee = frappe.db.sql("""
        SELECT `tabOn Duty Application`.employee, `tabOn Duty Application`.employee_name , `tabOn Duty Application`.name,`tabOn Duty Application`.from_date_session,`tabOn Duty Application`.workflow_state
        FROM `tabOn Duty Application` 
        RIGHT JOIN `tabEmployee`
        ON `tabOn Duty Application`.employee = `tabEmployee`.name where `tabOn Duty Application`.Workflow_state="Pending for Second Manager" and `tabEmployee`.employment_type !='Agency'
        """,as_dict=True)
    staff = """
        <div style="text-align: center;">
                <h2 style="font-size: 16px;">On Duty Report</h2>
            </div>
            <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
                <tr style="border: 1px solid black;">
                    <th style="padding: 4px; border: 1px solid black;">Employee</th>
                    <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                    <th style="padding: 4px; border: 1px solid black;">On Duty</th>
                    <th style="padding: 4px; border: 1px solid black;">Session</th>

                </tr>
    """	
    
    for i in employee:
            
        staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black;">{3}</td>
                
            </tr>
            """.format(i.employee_id, i.employee_name,
                    i.name or ' ',i.from_date_session or '')
    staff += "</table>"
    
    if employee:
        for i in employee:
            frappe.sendmail(
                recipients=[i.second_manager],
                subject='On Duty Application Report',
                message="""Dear Sir/Mam,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )
        frappe.sendmail(
                recipients=['sarath.v@groupteampro.com','arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='On Duty Application Report',
                message="""Dear Sir,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )


@frappe.whitelist()
def ot_hours_mail_alert():
    yesterday = frappe.utils.add_days(frappe.utils.today(), -1)

    # Initialize the HTML content for the OT report
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">OT Hours Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.No</th>
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Department</th>
                <th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
                <th style="padding: 4px; border: 1px solid black;">OT Hours</th>
                <th style="padding: 4px; border: 1px solid black;">Shift</th>
            </tr>
    """
    
    idx = 1
    no_ot = True

    # Fetching attendance records for yesterday
    attendance = frappe.get_all(
    "Attendance",
        filters={
            "attendance_date": yesterday,
            "docstatus": ("!=", 2),
            "custom_ot_hours": ("!=", "00:00:00"),
            "custom_employee_category": ["is", "set"]
        },
        fields=[
            "name", "employee", "employee_name", "department", 
            "custom_ot_hours", "status", "custom_employee_category", 
            "attendance_date", "shift"
        ]
    )


    for att in attendance:
        ot_applicable = frappe.db.get_value("Employee", {"name": att.employee}, "custom_ot_applicable")       
        if att.custom_employee_category == "White Collar" and ot_applicable == 1:
            no_ot = False
            staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black;">{3}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{4}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{5}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{6}</td>
            </tr>
            """.format(idx, att.employee, att.employee_name, att.department,
                        format_date(att.attendance_date) or ' ', att.custom_ot_hours or ' ',
                        att.shift or ' ')
            idx += 1
        elif not att.custom_employee_category == "White Collar":
            no_ot = False
            staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black;">{3}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{4}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{5}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{6}</td>
            </tr>
            """.format(idx, att.employee, att.employee_name, att.department,
                        format_date(att.attendance_date) or ' ', att.custom_ot_hours or ' ',
                        att.shift or ' ')
            idx += 1
    if no_ot:
        staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">No OT hours for yesterday.</h2>
        </div>
        """
    else:
        staff += "</table>"

    # Fetching HOD users to send the email to
    users = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.role = "HOD" AND `tabUser`.enabled = 1
    """, as_dict=True)

    # if not no_ot:
    for user in users:
        frappe.sendmail(
            recipients=[user.name],
            subject='OT Hours Report',
            message="""Dear Sir,<br><br>
                Kindly find the attached Employee OT Hours List for yesterday:<br>{0}
            """.format(staff)
        )
        
    # Send email to the predefined recipients
    frappe.sendmail(
        recipients=['sarath.v@groupteampro.com','orkun.ulu@teknorot.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
        subject='OT Hours Report',
        message="""Dear Sir,<br><br>
            Kindly find the attached Employee OT Hours List for yesterday:<br>{0}
        """.format(staff)
    )




import frappe

@frappe.whitelist()
def check_fixed_salary_visibility(employee_name):
    current_user = frappe.session.user
    hr_role = 'HR User'

    # Fetch the employee record for the current user
    employee_user = frappe.db.get_value('Employee', {'user_id': current_user}, 'name')

    # Check if the current user is the employee or has HR Manager role
    if employee_user == employee_name or frappe.has_role(current_user, hr_role):
        return True
    else:
        return False

@frappe.whitelist()
def restrict_for_zero_balance(doc, method):
    if doc.is_new(): 
        if not doc.leave_type == 'Leave Without Pay':
            total_leave_days_present=0
            total_lbalance=doc.leave_balance
            draft_leave_applications = frappe.get_all("Leave Application", {"employee": doc.employee,"docstatus":0 ,"leave_type": doc.leave_type,"workflow_state":("!=","Rejected")},["*"])
            for i in draft_leave_applications:
                total_leave_days_present+=i.total_leave_days
            total_leave_days_present += doc.total_leave_days
            available=total_lbalance-total_leave_days_present
            if available < 0 :
                frappe.throw("Insufficient leave balance for this leave type")

@frappe.whitelist()
def first_manager_name():
    otm_fm =frappe.db.get_all("Over Time Request",["*"])
    for d in otm_fm:
        first = frappe.db.get_value("Employee",{"name":d.employee},["custom_first_manager"])
        name= frappe.db.get_value("Employee",{"name":d.employee},["custom_first_manager_name_"])
        frappe.db.set_value('Over Time Request',d.name,'custom_first_manager',first)
        frappe.db.set_value('Over Time Request',d.name,'custom_first_manager_name',name)

@frappe.whitelist()
def update_ot_request_setting():
    from_date = "2024-07-01"
    to_date = "2024-07-31"
    attendance = frappe.get_all("Attendance", filters={"attendance_date":("between",(from_date,to_date)), "docstatus": ("!=", 2)}, fields=["*"])
    for att in attendance:
        if att.shift and att.in_time and att.out_time:
            if att.custom_ot_hours and att.custom_ot_hours > timedelta(hours=0, minutes=0, seconds=0):
                if att.status !="Absent":
                    ot_plan = frappe.db.sql("""SELECT t1.planned_ot_hrs
                                            FROM `tabOT Employee` AS t1 
                                            LEFT JOIN `tabOver Time Plan` AS t2 
                                            ON t2.name = t1.parent 
                                            WHERE t1.employee_id = %s AND t2.ot_date = %s AND t2.docstatus = 1""", (att.employee, date))
                    if not frappe.db.exists("Over Time Request", {'employee': att.employee, 'ot_date':att.attendance_date}):
                        if ot_plan:
                            req = frappe.new_doc("Over Time Request")
                            req.employee = att.employee
                            req.ot_date = att.attendance_date
                            req.ot_hour = att.custom_ot_hours
                            req.planned_hour = ot_plan[0][0]
                            req.save(ignore_permissions=True)
                            req.submit()
                        else:
                            req = frappe.new_doc("Over Time Request")
                            req.employee = att.employee
                            req.ot_date = att.attendance_date
                            req.ot_hour = att.custom_ot_hours
                            req.planned_hour = time(0, 0, 0)
                            req.save(ignore_permissions=True)
                            frappe.db.commit()
                            print(req.name)
                    else:
                        continue
                else:
                    continue
            else:
                continue
        else:
            continue


# Mail Trigger		 

import frappe
from frappe.utils import flt, add_days

@frappe.whitelist()
def head_count_mail_alert():
    args = frappe.local.form_dict
    yesterday = add_days(frappe.utils.today(), -1)
    data = get_data(yesterday)
    html_report = generate_html_report(data)

    recipients = ['sarath.v@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com',
    'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com']
    
    frappe.sendmail(
        recipients=recipients,
        subject='Head Count Report',
        message=f"""Dear Sir,<br><br>
                    Kindly find the attached Employee's Head Count List for yesterday :<br>{html_report}
                """
    )

def generate_html_report(data):
    html = """
    <div style="text-align: center;">
        <h2 style="font-size: 16px;">Head Count Report</h2>
    </div>
    <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
        <tr style="border: 1px solid black;">
            <th style="padding: 4px; border: 1px solid black;">S.NO</th>
            <th style="padding: 4px; border: 1px solid black;">DEPARTMENT</th>
            <th style="padding: 4px; border: 1px solid black;">SHIFT 1 HEAD COUNT</th>
            <th style="padding: 4px; border: 1px solid black;">SHIFT 2 HEAD COUNT</th>
            <th style="padding: 4px; border: 1px solid black;">SHIFT G HEAD COUNT</th>
            <th style="padding: 4px; border: 1px solid black;">TOTAL</th>
            <th style="padding: 4px; border: 1px solid black;">SHIFT 1 OVERTIME HRS</th>
            <th style="padding: 4px; border: 1px solid black;">SHIFT 2 OVERTIME HRS</th>
            <th style="padding: 4px; border: 1px solid black;">SHIFT G OVERTIME HRS</th>
            <th style="padding: 4px; border: 1px solid black;">TOTAL</th>
        </tr>
    """
    for row in data:
        html += "<tr>"
        for cell in row:
            html += f"<td style='padding: 4px; border: 1px solid black;'>{cell}</td>"
        html += "</tr>"

    html += "</table>"
    return html

def get_data(yesterday):
    data = []
    row = []
    tot1 = tot2 = tot3 = tot4 = tot5 = tot6 = tot7 = tot8 = 0
    s_no = 1
    departments = frappe.db.sql("""
        SELECT DISTINCT department
        FROM `tabAttendance`
        WHERE attendance_date = %s
        AND docstatus != 2
    """, (yesterday), as_dict=True)

    for dept in departments:
        department = dept.department

        shift1_data = frappe.db.sql("""
			SELECT COUNT(`tabAttendance`.status) AS shift1_count, SUM(`tabAttendance`.custom_ot_hours) AS shift1_overtime
			FROM `tabAttendance` LEFT JOIN `tabEmployee` ON `tabAttendance`.employee = `tabEmployee`.name
			WHERE `tabAttendance`.attendance_date = %s
			AND `tabAttendance`.docstatus != 2
			AND `tabAttendance`.in_time IS NOT NULL
			AND `tabAttendance`.department = %s 
			AND `tabAttendance`.shift = '1' AND `tabEmployee`.employment_type !='Agency'
		""", (yesterday, department), as_dict=True)

        shift1_count = shift1_data[0].shift1_count if shift1_data and shift1_data[0].shift1_count is not None else 0
        shift1_overtime = shift1_data[0].shift1_overtime if shift1_data and shift1_data[0].shift1_overtime is not None else 0.0
        shift1_overtime_hours = flt(shift1_overtime) / 10000

        shift2_data = frappe.db.sql("""
			SELECT COUNT(`tabAttendance`.status) AS shift2_count, SUM(`tabAttendance`.custom_ot_hours) AS shift2_overtime
			FROM `tabAttendance` LEFT JOIN `tabEmployee` ON `tabAttendance`.employee = `tabEmployee`.name
			WHERE `tabAttendance`.attendance_date =%s
			AND `tabAttendance`.docstatus != 2
			AND `tabAttendance`.in_time IS NOT NULL
			AND `tabAttendance`.department = %s 
			AND `tabAttendance`.shift = '2' AND `tabEmployee`.employment_type !='Agency'
		""", (yesterday, department), as_dict=True)


        shift2_count = shift2_data[0].shift2_count if shift2_data and shift2_data[0].shift2_count is not None else 0
        shift2_overtime = shift2_data[0].shift2_overtime if shift2_data and shift2_data[0].shift2_overtime is not None else 0.0
        shift2_overtime_hours = flt(shift2_overtime) / 10000
        
        shiftg_data = frappe.db.sql("""
			SELECT COUNT(`tabAttendance`.status) AS shiftg_count, SUM(`tabAttendance`.custom_ot_hours) AS shiftg_overtime
			FROM `tabAttendance` LEFT JOIN `tabEmployee` ON `tabAttendance`.employee = `tabEmployee`.name
			WHERE `tabAttendance`.attendance_date = %s
			AND `tabAttendance`.docstatus != 2
			AND `tabAttendance`.in_time IS NOT NULL
			AND `tabAttendance`.department = %s 
			AND `tabAttendance`.shift = 'G' AND `tabEmployee`.employment_type !='Agency'
		""", (yesterday, department), as_dict=True)


        shiftg_count = shiftg_data[0].shiftg_count if shiftg_data and shiftg_data[0].shiftg_count is not None else 0
        shiftg_overtime = shiftg_data[0].shiftg_overtime if shiftg_data and shiftg_data[0].shiftg_overtime is not None else 0.0
        shiftg_overtime_hours = flt(shiftg_overtime) / 10000

        shift3_data = frappe.db.sql("""
			SELECT COUNT(`tabAttendance`.status) AS shift3_count, SUM(`tabAttendance`.custom_ot_hours) AS shift3_overtime
			FROM `tabAttendance` LEFT JOIN `tabEmployee` ON `tabAttendance`.employee = `tabEmployee`.name
			WHERE `tabAttendance`.attendance_date = %s
			AND `tabAttendance`.docstatus != 2
			AND `tabAttendance`.in_time IS NOT NULL
			AND `tabAttendance`.department = %s 
			AND `tabAttendance`.shift = '3' AND `tabEmployee`.employment_type !='Agency'
		""", (yesterday, department), as_dict=True)

        shift3_count = shift3_data[0].shift3_count if shift3_data and shift3_data[0].shift3_count is not None else 0
        shift3_overtime = shift3_data[0].shift3_overtime if shift3_data and shift3_data[0].shift3_overtime is not None else 0.0
        shift3_overtime_hours = flt(shift3_overtime) / 10000
        
        total_over_time = flt(shift1_overtime_hours) + flt(shift2_overtime_hours)+flt(shiftg_overtime_hours)+flt(shift3_overtime_hours)
        total_count = shift1_count + shift2_count +shiftg_count+shift3_count
        
        if flt(shift1_count) or flt(shift2_count) or flt(shiftg_count) or flt(shift3_count):
            data.append([
                s_no,
                department,
                flt(shift1_count),
                flt(shift2_count),
                flt(shiftg_count),
                total_count,
                flt(shift1_overtime_hours),
                flt(shift2_overtime_hours),
                flt(shiftg_overtime_hours),
                total_over_time
            ])
            s_no += 1

        tot1 += shift1_count
        tot2 += shift2_count
        tot3 += shiftg_count
        tot4 += total_count
        tot5 += shift1_overtime_hours
        tot6 += shift2_overtime_hours
        tot7 += shiftg_overtime_hours
        tot8 += total_over_time

    row += ['Total', '', tot1, tot2, tot3, tot4, tot5, tot6, tot7, tot8]
    data.append(row)
    return data


@frappe.whitelist()
def late_entry_mail_alert_for_G_shift():
    today = frappe.utils.today()
    attendance = frappe.db.sql("""
        SELECT * FROM `tabAttendance` LEFT JOIN `tabEmployee` 
        ON `tabAttendance`.employee = `tabEmployee`.name
        WHERE `tabAttendance`.attendance_date = %s AND `tabAttendance`.docstatus != 2 and `tabEmployee`.employment_type!='Agency'
        order by `tabAttendance`.employee
    """, (today,), as_dict=True)
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">Late Entry Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Department</th>
                <th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
                <th style="padding: 4px; border: 1px solid black;">Late Entry Time</th>
                <th style="padding: 4px; border: 1px solid black;">Shift</th>
            </tr>
    """
    no_ot = True
    for att in attendance:
        if att.late_entry and att.shift == 'G':
            if att.custom_late_entry_time:
                dt = datetime.strptime(str(att.custom_late_entry_time), "%H:%M:%S.%f")
                time_string_no_ms = dt.strftime("%H:%M:%S")
                no_ot = False
                staff += """
                <tr style="border: 1px solid black;">
                    <td style="padding: 4px; border: 1px solid black;">{0}</td>
                    <td style="padding: 4px; border: 1px solid black;">{1}</td>
                    <td style="padding: 4px; border: 1px solid black;">{2}</td>
                    <td style="padding: 4px; border: 1px solid black;text-align: center;">{3}</td>
                    <td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
                    <td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
                </tr>
                """.format(att.employee, att.employee_name, att.department,
                        format_date(att.attendance_date) or ' ',time_string_no_ms or ' ',
                            att.shift or ' ')
    if no_ot:
        staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">No Late Entry for today.</h2>
        </div>
        """
    else:
        staff += "</table>"
    if attendance:	
        frappe.sendmail(
                recipients=['sarath.v@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com', 'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com', 'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='Late Entry Report',
                message="""Dear Sir,<br><br>
                        Kindly find the attached Employee Late Entry List for today:<br>{0}
                        """.format(staff)
            )
  
@frappe.whitelist()
def late_entry_mail_alert_for_2_shift():
    today = frappe.utils.today()
    attendance = frappe.db.sql("""
        SELECT * FROM `tabAttendance` LEFT JOIN `tabEmployee` 
        ON `tabAttendance`.employee = `tabEmployee`.name
        WHERE `tabAttendance`.attendance_date = %s AND `tabAttendance`.docstatus != 2 and `tabEmployee`.employment_type!='Agency'
        order by `tabAttendance`.employee
    """, (today,), as_dict=True)
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">Late Entry Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Department</th>
                <th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
                <th style="padding: 4px; border: 1px solid black;">Late Entry Time</th>
                <th style="padding: 4px; border: 1px solid black;">Shift</th>
            </tr>
    """
    no_ot = True
    for att in attendance:
        if att.late_entry and att.shift == '2':
            if att.custom_late_entry_time:
                dt = datetime.strptime(str(att.custom_late_entry_time), "%H:%M:%S.%f")
                time_string_no_ms = dt.strftime("%H:%M:%S")
                no_ot = False
                staff += """
                <tr style="border: 1px solid black;">
                    <td style="padding: 4px; border: 1px solid black;">{0}</td>
                    <td style="padding: 4px; border: 1px solid black;">{1}</td>
                    <td style="padding: 4px; border: 1px solid black;">{2}</td>
                    <td style="padding: 4px; border: 1px solid black;text-align: center;">{3}</td>
                    <td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
                    <td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
                </tr>
                """.format(att.employee, att.employee_name, att.department,
                        format_date(att.attendance_date) or ' ',time_string_no_ms or ' ',
                            att.shift or ' ')
    if no_ot:
        staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">No Late Entry for today.</h2>
        </div>
        """
    else:
        staff += "</table>"
    if attendance:	
        frappe.sendmail(
                recipients=['sarath.v@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com', 'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com', 'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='Late Entry Report',
                message="""Dear Sir,<br><br>
                        Kindly find the attached Employee Late Entry List for today:<br>{0}
                        """.format(staff)
            )

@frappe.whitelist()
def check_on_duty(doc, method):
    value = frappe.db.sql("""
        SELECT `tabOn Duty Application`.name FROM `tabOn Duty Application` 
        LEFT JOIN `tabEmployee`
        ON `tabOn Duty Application` .employee = `tabEmployee`.name
        WHERE `tabOn Duty Application`.employee = %s 
        AND `tabOn Duty Application` .docstatus != 2 
        AND (`tabOn Duty Application`.from_date BETWEEN %s AND %s OR `tabOn Duty Application` .from_date BETWEEN %s AND %s 
             OR (`tabOn Duty Application` .from_date <= %s AND `tabOn Duty Application` .from_date >= %s))
        AND `tabOn Duty Application` .from_date_session = 'Full Day' and `tabEmployee`.employment_type!='Agency'
    """, (doc.employee, doc.from_date, doc.to_date, doc.from_date, doc.to_date, doc.from_date, doc.to_date))

    if value:
        frappe.throw("You have already applied for an On Duty Application for the same or overlapping date range.")
        
#Get the salary slip total
@frappe.whitelist()
def get_mandays_amount(contractor):
	man_days_amount = frappe.db.sql("""select sum(rounded_total) from `tabSalary Slip` where docstatus != 2  and custom_agency='%s' """%(contractor),as_dict = 1)[0]
	return man_days_amount['sum(rounded_total)'] 


from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
#Warning mail for late entry      
@frappe.whitelist()
def update_late_deduction():
    month_start = get_first_day(today()) 
    today_date = today() 
    
    attendance = frappe.db.sql("""
        SELECT * FROM `tabAttendance` LEFT JOIN `tabEmployee` 
        ON `tabAttendance`.employee = `tabEmployee`.name
        WHERE `tabAttendance`.attendance_date >= %s AND `tabAttendance`.attendance_date <= %s AND `tabAttendance`.docstatus != 2 and `tabEmployee`.employment_type!='Agency'
        order by `tabAttendance`.employee
    """, (month_start, today_date), as_dict=True)

    late = 0  # Counter for late entries
    late_min = 0  # Total late minutes across all late entries

    for att in attendance:
        if att.in_time and att.shift:
            # Get shift start time
            shift_st = frappe.db.get_value("Shift Type", {'name': att.shift}, ['start_time'])

            # Convert times to datetime objects for comparison
            in_time = datetime.strptime(str(att.in_time), '%Y-%m-%d %H:%M:%S').time()
            shift_st = datetime.strptime(str(shift_st), '%H:%M:%S').time()

            # Check if the employee is late
            if shift_st < in_time:
                difference = time_diff_in_timedelta_1(shift_st, in_time)  # Calculate time difference
                diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()

                late_min += diff_time.minute  # Add to total late minutes
                frappe.db.set_value("Attendance", att.name, 'custom_late', difference)  # Set custom late field

                if diff_time.minute > 0:
                    late += 1
                    if late == 1 and diff_time.minute >= 15:
                        pass
                    elif late == 2 and diff_time.minute >= 15:
                        if late_min >= 30:
                            send_late_warning_email(att.employee)
                            frappe.db.set_value("Attendance", att.name, 'late_entry', 1)
                    elif late > 2 and late < 5:
                        if not att.custom_late:
                            send_late_warning_email(att.employee)

def send_late_warning_email(employee):
    emp_email = frappe.get_value("Employee", {"name": employee}, ['user_id'])
    if emp_email:
        frappe.sendmail(
                recipients=[emp_email],
                subject=_("Warning - Late Entry"),
                message="""
                    Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
                    """%(employee)
            )

    
def create_hooks_mark_late():
    job = frappe.db.exists('Scheduled Job Type', 'attendance_for_one_month')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method": 'ir.mark_attendance.mark_att_process_manual_for_one_month',
            "frequency": 'Cron',
            "cron_format": "0 0 28-31 * *"
        })
        sjt.save(ignore_permissions=True)
    

@frappe.whitelist()
#send a mail alert if any scheduled job failed
def schedule_log_fail(doc,method):
    if doc.status=='Failed':
        message = """
        The schedule Job type <b>{}</b> is failed.<br> Kindly check the log <b>{}</b>""".format(doc.scheduled_job_type,doc.name)
        frappe.sendmail(
                recipients=["erp@groupteampro.com"],
                subject='Scheduled Job type failed(IR)',
                message=message
            )
        
@frappe.whitelist()
def update_employee_number(doc, new_name, old_name, merge, method):
    frappe.db.set_value("Employee",doc.name,"employee_number",doc.name)
    
    
@frappe.whitelist()
def diff_emp_no():
    employee = frappe.get_all("Employee",["name","employee_number"])
    for i in employee:
        if not i.name == i.employee_number:
            print(i.name)
            
@frappe.whitelist()
#send a mail alert if any scheduled job failed
def schedule_log_failed(name,schedule):
    # if doc.status=='Failed':
    message = """
    The schedule Job type <b>{}</b> is failed.<br> Kindly check the log <b>{}</b>
    """.format(schedule,name)
    frappe.sendmail(
            recipients=["erp@groupteampro.com"],
            subject='Scheduled Job type failed(IR)',
            message=message
        )
    
    
# import frappe
# import random
# from frappe.utils import today

# def send_birthday_wishes_for_employee():
#     current_month_day = today()[5:] 
#     employees = frappe.get_all(
#     "Employee",
#     filters={"status": "Active", "employment_type": ["!=", "Agency"]},
#     fields=["name", "employee_name", "user_id", "date_of_birth"]
# )

#     matching_employees = []
#     for emp in employees:
#         if emp["date_of_birth"]:  
#             emp_month_day = emp["date_of_birth"].strftime("%m-%d")
#             if emp_month_day == current_month_day:
#                 matching_employees.append(emp)

#     if not matching_employees:
#         return

#     for employee in matching_employees:
#     # selected_message = random.choice(greeting_messages)
#         email_content = f"""
#         <p>Birthday Reminder 🎂</p>
#         <p>Today is {employee['employee_name']} birthday 🎉</p>
#         <p>A friendly reminder of an important date for our team.</p>
#         <p>Everyone, let’s congratulate {employee['employee_name']} on their birthday.</p>
#         <p>Best Regards,<br>Industrias Del Recambio India Pvt Ltd</p>
#         """

#         frappe.sendmail(
#             # recipients=[employee["user_id"]],
#             recipients="divya.p@groupteampro.com",
#             subject="Birthday Reminder",
#             message=email_content
#         )


        
# ------------------
# BIRTHDAY REMINDERS
# ------------------
def send_birthday_reminders():
	"""Send Employee birthday reminders if no 'Stop Birthday Reminders' is not set."""

	# to_send = int(frappe.db.get_single_value("HR Settings", "send_birthday_reminders"))
	# if not to_send:
	# 	return

	sender = get_sender_email()
	employees_born_today = get_employees_who_are_born_today()

	for company, birthday_persons in employees_born_today.items():
		employee_emails = get_all_employee_emails(company)
		birthday_person_emails = [get_employee_email(doc) for doc in birthday_persons]
		recipients = list(set(employee_emails) - set(birthday_person_emails))

		reminder_text, message = get_birthday_reminder_text_and_message(birthday_persons)
		send_birthday_reminder(recipients, reminder_text, birthday_persons, message, sender)

		if len(birthday_persons) > 1:
			# special email for people sharing birthdays
			for person in birthday_persons:
				person_email = person["user_id"] or person["personal_email"] or person["company_email"]
				others = [d for d in birthday_persons if d != person]
				reminder_text, message = get_birthday_reminder_text_and_message(others)
				send_birthday_reminder(person_email, reminder_text, others, message, sender)


def get_birthday_reminder_text_and_message(birthday_persons):
	if len(birthday_persons) == 1:
		birthday_person_text = birthday_persons[0]["name"]
	else:
		# converts ["Jim", "Rim", "Dim"] to Jim, Rim & Dim
		person_names = [d["name"] for d in birthday_persons]
		birthday_person_text = comma_sep(person_names, frappe._("{0} & {1}"), False)

	reminder_text = _("Today is {0}'s birthday 🎉").format(birthday_person_text)
	message = _("A friendly reminder of an important date for our team.")
	message += "<br>"
	message += _("Everyone, let’s congratulate {0} on their birthday.").format(birthday_person_text)

	return reminder_text, message


def send_birthday_reminder(recipients, reminder_text, birthday_persons, message, sender=None):
	frappe.sendmail(
		sender=sender,
		recipients=recipients,
		subject=_("Birthday Reminder"),
        # recipients='divya.p@groupteampro.com',
		template="birthday_reminder",
		args=dict(
			reminder_text=reminder_text,
			birthday_persons=birthday_persons,
			message=message,
		),
		header=_("Birthday Reminder 🎂"),
	)


def get_employees_who_are_born_today():
	"""Get all employee born today & group them based on their company"""
	return get_employees_having_an_event_today("birthday")


def get_employees_having_an_event_today(event_type):
	"""Get all employee who have `event_type` today
	& group them based on their company. `event_type`
	can be `birthday` or `work_anniversary`"""

	from collections import defaultdict

	# Set column based on event type
	if event_type == "birthday":
		condition_column = "date_of_birth"

	employees_born_today = frappe.db.multisql(
		{
			"mariadb": f"""
			SELECT `personal_email`, `company`, `company_email`, `user_id`, `employee_name` AS 'name', `image`, `date_of_joining`
			FROM `tabEmployee`
			WHERE
				DAY({condition_column}) = DAY(%(today)s)
			AND
				MONTH({condition_column}) = MONTH(%(today)s)
			AND
				YEAR({condition_column}) < YEAR(%(today)s)
			AND
				`status` = 'Active'
            AND 
                `employment_type`!='Agency'
		""",
			"postgres": f"""
			SELECT "personal_email", "company", "company_email", "user_id", "employee_name" AS 'name', "image"
			FROM "tabEmployee"
			WHERE
				DATE_PART('day', {condition_column}) = date_part('day', %(today)s)
			AND
				DATE_PART('month', {condition_column}) = date_part('month', %(today)s)
			AND
				DATE_PART('year', {condition_column}) < date_part('year', %(today)s)
			AND
				"status" = 'Active'
            AND 
                "employment_type"!='Agency'
		""",
		},
		dict(today=today(), condition_column=condition_column),
		as_dict=1,
	)

	grouped_employees = defaultdict(lambda: [])

	for employee_doc in employees_born_today:
		grouped_employees[employee_doc.get("company")].append(employee_doc)

	return grouped_employees

def get_sender_email() -> str | None:
	return frappe.db.get_single_value("HR Settings", "sender_email")

# @frappe.whitelist()
# def task_mail_notification_status ():
#     job = frappe.db.exists('Scheduled Job Type','send_birthday_reminders')
#     if not job:
#         task = frappe.new_doc("Scheduled Job Type")
#         task.update({
#             "method": 'ir.custom.send_birthday_reminders',
#             "frequency": 'Cron',
#             "cron_format" : '00 00 * * *'
#         })
#         task.save(ignore_permissions=True)

@frappe.whitelist()
def create_job_fail():
    job = frappe.db.exists('Scheduled Job Type', 'cron_failed')
    if not job:
        emc = frappe.new_doc("Scheduled Job Type")
        emc.update({
            "method": 'ir.custom.cron_failed_method',
            "frequency": 'Cron',
            "cron_format": '*/5 * * * *'
        })
        emc.save(ignore_permissions=True)


@frappe.whitelist()
def cron_failed_method():
    cutoff_time = datetime.now() - timedelta(minutes=5)
    failed_jobs = frappe.get_all(
        "Scheduled Job Log",
        filters={
            "status": "Failed",
            "creation": [">=", cutoff_time]
        },
        fields=["scheduled_job_type"]
    )
    unique_job_types = set()
    for job in failed_jobs:
        unique_job_types.add(job['scheduled_job_type'])

    for job_type in unique_job_types:
        frappe.sendmail(
            recipients = ["erp@groupteampro.com","jenisha.p@groupteampro.com","pavithra.s@groupteampro.com","gifty.p@groupteampro.com"],
            subject = 'Failed Cron List - IR',
            message = 'Dear Sir / Mam <br> Kindly find the below failed Scheduled Job  %s'%(job_type)
        )
    
@frappe.whitelist()
def total_fixed_value(employee, name):
    fixed_value = 0
    slip = frappe.get_doc("Salary Slip", name)
    for i in slip.earnings:
        component = frappe.db.get_value('Salary Component', {"name": i.salary_component}, 'custom_field_in_employee_mis')
        if component:
            value = frappe.db.get_value('Employee', {"name": employee}, component)
            if value:
                fixed_value += value
    return fixed_value 


@frappe.whitelist()
def update_salary_category():
    employee = frappe.get_all("Employee",["*"])
    for emp in employee:
        if emp.custom_agency_name:
            frappe.db.set_value("Employee",emp.name,"custom_salary_category",emp.designation)


        
@frappe.whitelist()
def find_ot_document():
    ot = frappe.get_all("Employee",{"employee":"S1682"},["employment_type",])
    for i in ot:
        print(i.employment_type)  
        
def validate_bank_ac_no(doc, method):
    if doc.bank_ac_no and len(str(doc.bank_ac_no)) != 15:
        frappe.throw("Only input 15 digits; less than or greater than 15 is not allowed.")
        
# @frappe.whitelist()
# def update_query():
#     frappe.db.sql("""
#         UPDATE `tabEmployee`
#         SET 
#             custom_pf = '0.00', 
#             custom_gratuity = '0.00', 
#             custom_bonus = '0.00', 
#             ctc = '0.00', 
#             custom_conveyance = '0.00',
#             custom_cca='0.00',
#             custom_hra='0.00'
#         WHERE name = 'S1636'
#     """)
#     frappe.db.commit()
