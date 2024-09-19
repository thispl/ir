import frappe
from frappe import get_doc
from frappe.utils import getdate
from datetime import datetime
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form
from frappe.utils.data import date_diff, now_datetime, nowdate, today, add_days
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

@frappe.whitelist()
def get_designation(name):
    doc = frappe.get_doc("Agency", name)
    states = [state.designation for state in doc.designation]
    return states

@frappe.whitelist()	
def update_agency_wages(doc,method):
    ss=frappe.get_doc("Employee",doc.name)
    if ss.employment_type == "Agency" and ss.designation:
            basic = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['basic'])
            frappe.db.set_value("Employee",doc.employee_number,"custom_basic",basic)
            ss.custom_basic=basic
            frappe.errprint(ss.custom_basic)
            # ss.save(ignore_permissions=True)
            # frappe.db.commit()
            dearness_allowance = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['dearness_allowance'])
            frappe.db.set_value("Employee", doc.name, "custom_dearness_allowance", dearness_allowance)
            ss.custom_dearness_allowance=dearness_allowance
            frappe.errprint(ss.custom_dearness_allowance)
            special_allowance_ = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['special_allowance'])
            frappe.db.set_value("Employee",doc.name,"custom_special_allowance_",special_allowance_)
            earning_provident_fund_13 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['earning_provident_fund_13'])
            frappe.db.set_value("Employee",doc.name,"custom_pf",earning_provident_fund_13)
            earning_esi_325 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['earning_esi_325'])
            frappe.db.set_value("Employee",doc.name,"custom_esi",earning_esi_325)
            service_charges_8 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['service_charge'])
            frappe.db.set_value("Employee",doc.name,"custom_service_chrages",service_charges_8)
            deduction_pf_12 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['deduction_pf_12'])
            # frappe.db.set_value("Employee",doc.name,"custom_deduction_pf_12",deduction_pf_12)
            # deduction_esi_075 = frappe.db.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['deduction_esi_075'])
            # frappe.db.set_value("Employee",doc.name,"custom_deduction_esi_075",deduction_esi_075)
            # canteen = frappe.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['canteen'])
            # frappe.db.set_value("Employee",doc.name,"custom_canteen",canteen)
            # overtime = frappe.get_value("Agency Wages",{'designation':ss.designation,'parent':ss.custom_agency_name},['overtime'])
            # frappe.db.set_value("Employee",doc.name,"custom_overtime",overtime)
            frappe.db.commit()
    

# @frappe.whitelist()
# def get_approver(department, employee):
#     user = frappe.db.get_value('Employee', employee, 'user_id')
#     roles = frappe.get_roles(user)
#     # if 'GM' in roles:
#     #     return frappe.db.get_value('Department', department, "ceo")
#     if 'HOD' in roles:
#         return frappe.db.get_value('Department', department, "hr")
#     else:
#         return frappe.db.get_value('Department', department, "hod")






# @frappe.whitelist()
# def shift_request_count(employee, from_date, to_date):
#     f_date = datetime.strptime(from_date, "%Y-%m-%d").date()
#     t_date = datetime.strptime(to_date, "%Y-%m-%d").date()
#     diff = date_diff(to_date, from_date) + 1
#     frappe.errprint(diff)
#     if diff > 1:
#         frappe.errprint("HI")
#         frappe.msgprint(
#             "Shift Request cannot be applicable for more than 1 days in a month")
#         return "ok"
#     else:
#         month_start = get_first_day(f_date)
#         month_end = get_last_day(t_date)
#         request = frappe.db.sql(""" SELECT employee,from_date,to_date FROM `tabShift Request` WHERE employee = '%s' 
#         AND status='Approved' AND from_date between '%s' AND '%s'""" % (employee, month_start, month_end), as_dict=True)
#         if request:
#             total_days = 0
#             for r in request:
#                 d = date_diff(r.to_date, r.from_date) + 1
#                 total_days += d
#                 # frappe.errprint(total_days)
#             if total_days >= 1:
#                 frappe.msgprint(
#                     "Already Shift Request count existed for this Month")
#                 return "ok"



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


@frappe.whitelist()
def get_md(agency_name,branch,employee_category,start_date,end_date,designation):
    mdr = frappe.get_value('Agency Wages',{'designation':designation,'parent':agency_name},['total'])
    tar = frappe.get_value('Agency Wages',{'designation':designation,'parent':agency_name},['travel_allowance_rate'])
    man_days = frappe.db.sql("""select sum(payment_days) from `tabSalary Slip` where docstatus != '2' and agency_name ='%s' and employee_category='%s' and branch = '%s' and start_date = '%s' and end_date = '%s' and designation = '%s' """%(agency_name,employee_category,start_date,end_date,designation),as_dict = 1)[0]
    # ot = frappe.db.sql("""select (sum(overtime_hours))  as ot_hrs from `tabSalary Slip` where docstatus != 2  and agency_name ='%s' and employee_category='%s' and branch ='%s' and start_date = '%s' and end_date = '%s' and designation = '%s' """%(agency_name,employee_category,start_date,end_date,designation),as_dict = 1)[0]
    return man_days['sum(payment_days)'] or 0 , mdr or 0 ,tar or 0

@frappe.whitelist()
def get_mandays_amount(agency_name,employee_category,branch):
    man_days_amount = frappe.db.sql("""select sum(rounded_total) from `tabSalary Slip` where docstatus != 2  and agency_name='%s' and branch = '%s' and employee_category='%s' """%(agency_name,employee_category),as_dict = 1)[0]
    return[man_days_amount['sum(rounded_total)']]

@frappe.whitelist()
def get_total_amount_in_words(total_amount):
    try:
        total_amt = float(total_amount)
        tot = money_in_words(total_amt)
        return tot
    except ValueError:
        frappe.errprint(total_amount)
        return "Invalid amount"
# if self.custom_agency and self.designation:
# 			basic = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['basic'])
# 			frappe.db.set_value("Employee",self.name,"custom_basic",basic)
# 			self.custom_basic=basic
            
# 			dearness_allowance = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['dearness_allowance'])
# 			frappe.db.set_value("Salary Slip",self.name,"custom_dearness_allowance",dearness_allowance)
# 			self.custom_dearness_allowance=dearness_allowance
            
# 			special_allowance_ = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['special_allowance'])
# 			frappe.db.set_value("Salary Slip",self.name,"custom_special_allowance_",special_allowance_)
# 			self.custom_special_allowance_=special_allowance_
            
# 			earning_provident_fund_13 = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['earning_provident_fund_13'])
# 			frappe.db.set_value("Salary Slip",self.name,"custom_earning_provident_fund_13",earning_provident_fund_13)
# 			self.custom_earning_provident_fund_13=earning_provident_fund_13
            
# 			earning_esi_325 = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['earning_esi_325'])
# 			frappe.db.set_value("Salary Slip",self.name,"custom_earning_esi_325",earning_esi_325)
# 			self.custom_earning_esi_325=earning_esi_325

            # service_charges_8 = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['service_charge'])
            # frappe.db.set_value("Salary Slip",self.name,"custom_service_charges_8",service_charges_8)
            # self.custom_service_charges_8=service_charges_8

            # deduction_pf_12 = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['deduction_pf_12'])
            # frappe.db.set_value("Salary Slip",self.name,"custom_deduction_pf_12",deduction_pf_12)
            # self.custom_deduction_pf_12=deduction_pf_12

            # deduction_esi_075 = frappe.db.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['deduction_esi_075'])
            # frappe.db.set_value("Salary Slip",self.name,"custom_deduction_esi_075",deduction_esi_075)
            # self.custom_deduction_esi_075=deduction_pf_12

            # canteen = frappe.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['canteen'])
            # frappe.db.set_value("Salary Slip",self.name,"custom_canteen",canteen)
            # self.custom_canteen=canteen

            # overtime = frappe.get_value("Agency Wages",{'designation':self.designation,'parent':self.custom_agency},['overtime'])
            # frappe.db.set_value("Salary Slip",self.name,"custom_overtime",overtime)
            # self.custom_overtime=overtime



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

@frappe.whitelist()
def update_leave_allocation():
    job = frappe.db.exists('Scheduled Job Type', 'update_earned_leave')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method": 'ir.custom.update_earned_leave',
            "frequency": 'Cron',
            "cron_format": '00 09 1 * *'
        })
        sjt.save(ignore_permissions=True)




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

@frappe.whitelist()
def update_ot_request(doc, method):
    date = doc.attendance_date
    hh= check_holiday(date,doc.employee)
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

                            ot_plan = frappe.db.sql("""SELECT t1.planned_ot_hrs
                                                    FROM `tabOT Employee` AS t1 
                                                    LEFT JOIN `tabOver Time Plan` AS t2 
                                                    ON t2.name = t1.parent 
                                                    WHERE t1.employee_id = %s AND t2.ot_date = %s AND t2.docstatus = 1""", (doc.employee, date))
                            
                            if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                                if ot_plan:
                                    if ot_plan[0][0] > doc.custom_ot_hours:
                                        req = frappe.new_doc("Over Time Request")
                                        req.employee = doc.employee
                                        req.ot_date = date
                                        req.ot_hour = doc.custom_ot_hours
                                        req.planned_hour = ot_plan[0][0]
                                        req.save(ignore_permissions=True)
                                        req.submit()
                                    else:
                                        req = frappe.new_doc("Over Time Request")
                                        req.employee = doc.employee
                                        req.ot_date = date
                                        req.ot_hour = ot_plan[0][0]
                                        req.planned_hour = ot_plan[0][0]
                                        req.save(ignore_permissions=True)
                                        req.submit()
                                else:
                                    frappe.errprint('Worked')
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.ot_date = date
                                    req.ot_hour = doc.custom_ot_hours
                                    req.planned_hour = time(0, 0, 0)
                                    req.save(ignore_permissions=True)
                                    frappe.db.commit()
                                    print(req.name)

        elif not doc.custom_employee_category =="White Collar":
            if doc.shift and doc.in_time and doc.out_time:
                if doc.status == "Half Day" or doc.status == "Present":
                    if isinstance(doc.custom_ot_hours, str):
                        custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                        ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                    else:
                        ot_timedelta = doc.custom_ot_hours
                    if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                        frappe.errprint('Working')
                        ot_plan = frappe.db.sql("""SELECT t1.planned_ot_hrs
                                                FROM `tabOT Employee` AS t1 
                                                LEFT JOIN `tabOver Time Plan` AS t2 
                                                ON t2.name = t1.parent 
                                                WHERE t1.employee_id = %s AND t2.ot_date = %s AND t2.docstatus = 1""", (doc.employee, date))
                        
                        if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                            if ot_plan:
                                if ot_plan[0][0] > doc.custom_ot_hours:
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.ot_date = date
                                    req.ot_hour = doc.custom_ot_hours
                                    req.planned_hour = ot_plan[0][0]
                                    req.save(ignore_permissions=True)
                                    req.submit()
                                else:
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.ot_date = date
                                    req.ot_hour = ot_plan[0][0]
                                    req.planned_hour = ot_plan[0][0]
                                    req.save(ignore_permissions=True)
                                    req.submit()
                            else:
                                frappe.errprint('Worked')
                                req = frappe.new_doc("Over Time Request")
                                req.employee = doc.employee
                                req.ot_date = date
                                req.ot_hour = doc.custom_ot_hours
                                req.planned_hour = time(0, 0, 0)
                                req.save(ignore_permissions=True)
                                frappe.db.commit()
                                print(req.name)
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

                        ot_plan = frappe.db.sql("""SELECT t1.planned_ot_hrs
                                                FROM `tabOT Employee` AS t1 
                                                LEFT JOIN `tabOver Time Plan` AS t2 
                                                ON t2.name = t1.parent 
                                                WHERE t1.employee_id = %s AND t2.ot_date = %s AND t2.docstatus = 1""", (doc.employee, date))
                        
                        if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                            if ot_plan:
                                if ot_plan[0][0] > doc.custom_ot_hours:
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.ot_date = date
                                    req.ot_hour = doc.custom_ot_hours
                                    req.planned_hour = ot_plan[0][0]
                                    req.save(ignore_permissions=True)
                                    req.submit()
                                else:
                                    req = frappe.new_doc("Over Time Request")
                                    req.employee = doc.employee
                                    req.ot_date = date
                                    req.ot_hour = ot_plan[0][0]
                                    req.planned_hour = ot_plan[0][0]
                                    req.save(ignore_permissions=True)
                                    req.submit()
                            else:
                                frappe.errprint('Worked')
                                req = frappe.new_doc("Over Time Request")
                                req.employee = doc.employee
                                req.ot_date = date
                                req.ot_hour = doc.custom_ot_hours
                                req.planned_hour = time(0, 0, 0)
                                req.save(ignore_permissions=True)
                                frappe.db.commit()
                                print(req.name)

        elif not doc.custom_employee_category =="White Collar":
            if doc.shift and doc.in_time and doc.out_time:
                if isinstance(doc.custom_ot_hours, str):
                    custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                    ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                else:
                    ot_timedelta = doc.custom_ot_hours
                if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                    frappe.errprint('Working')
                    ot_plan = frappe.db.sql("""SELECT t1.planned_ot_hrs
                                            FROM `tabOT Employee` AS t1 
                                            LEFT JOIN `tabOver Time Plan` AS t2 
                                            ON t2.name = t1.parent 
                                            WHERE t1.employee_id = %s AND t2.ot_date = %s AND t2.docstatus = 1""", (doc.employee, date))
                    
                    if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                        if ot_plan:
                            if ot_plan[0][0] > doc.custom_ot_hours:
                                req = frappe.new_doc("Over Time Request")
                                req.employee = doc.employee
                                req.ot_date = date
                                req.ot_hour = doc.custom_ot_hours
                                req.planned_hour = ot_plan[0][0]
                                req.save(ignore_permissions=True)
                                req.submit()
                            else:
                                req = frappe.new_doc("Over Time Request")
                                req.employee = doc.employee
                                req.ot_date = date
                                req.ot_hour = ot_plan[0][0]
                                req.planned_hour = ot_plan[0][0]
                                req.save(ignore_permissions=True)
                                req.submit()
                        else:
                            frappe.errprint('Worked')
                            req = frappe.new_doc("Over Time Request")
                            req.employee = doc.employee
                            req.ot_date = date
                            req.ot_hour = doc.custom_ot_hours
                            req.planned_hour = time(0, 0, 0)
                            req.save(ignore_permissions=True)
                            frappe.db.commit()
                            print(req.name)    
@frappe.whitelist()
def null_out_time():
    checkin = frappe.db.sql("""update `tabAttendance` set docstatus = 0  where attendance_date between "2024-06-01" and "2024-06-30" """,as_dict = True)
    print(checkin)
    # checkin = frappe.db.sql("""update `tabAttendance` set custom_total_working_hours = NULL where attendance_date between "2024-07-16" and "2024-07-23" """,as_dict = True)
    # print(checkin)
    # checkin = frappe.db.sql("""update `tabAttendance` set working_hours = 0 where attendance_date between "2024-07-16" and "2024-07-23" """,as_dict = True)
    # print(checkin)
    # checkin = frappe.db.sql("""update `tabAttendance` set custom_ot_hours = NULL where attendance_date between "2024-07-16" and "2024-07-23" """,as_dict = True)
    # print(checkin)
    # checkin = frappe.db.sql("""update `tabAttendance` set leave_application = ' ' where attendance_date between "2024-07-16" and "2024-07-23" """,as_dict = True)
    # print(checkin)
    # checkin = frappe.db.sql("""delete from `tabAttendance` where attendance_date between "2024-07-16" and "2024-07-23" """,as_dict = True)
    # print(checkin)

@frappe.whitelist()
def update_att():
    checkin = frappe.db.sql("""
        update `tabAttendance`
        set custom_ot_hours = "05:00:00"
        where name = "HR-ATT-2024-46806"
    """, as_dict=True)


@frappe.whitelist()
def update_att1():
    from_date='2024-04-16'
    to_date='2024-04-30'
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for i in attendance:
        # frappe.db.set_value("Attendance",i.name,'in_time','00:00:00')
        frappe.db.set_value("Attendance",i.name,'out_time','00:00:00')
        # frappe.db.set_value("Attendance",i.name,'custom_late','00:00:00')
        # frappe.db.set_value("Attendance",i.name,'shift','')

       
@frappe.whitelist()
def comp_req():
    todays= datetime.strptime(nowdate(), '%Y-%m-%d').date()
    comp=frappe.db.get_all("Compensatory Off Request",{"docstatus":1},['work_from_date','employee'])
    for i in comp:
        diff = date_diff(todays,i.work_from_date)
        if diff ==60:
            leave_app= frappe.db.sql("select * from `tabLeave Application` where employee = '%s' and from_date between '%s' and '%s' and workflow_state != 'Rejected' and docstatus!=2 "%(i.employee,i.work_from_date,todays),as_dict=True)
            if not leave_app:
                leaves=frappe.db.get_all("Leave Ledger Entry",{"leave_type":'Compensatory Off','employee':i.employee},['creation','name'])
                for j in leaves:
                    diff = date_diff(todays,j.creation)
                    # frappe.errprint(diff)
                    # frappe.errprint(j.name)
                    if diff<=60:
                        frappe.db.set_value("Leave Ledger Entry",j.name,'is_expired',1)   


def cron_comp_req():
    job = frappe.db.exists('Scheduled Job Type', 'comp_req')
    if not job:
        var = frappe.new_doc("Scheduled Job Type")
        var.update({
            "method": 'ir.custom.comp_req',
            "frequency": 'Cron',
            "cron_format": '00 00 * * *'
        })
        var.save(ignore_permissions=True)
       

         
        

# @frappe.whitelist()
# def update_query():
# 	frappe.db.sql("""
# 		UPDATE `tabAttendance`
# 			SET docstatus = 0
# 			WHERE 	name ='HR-ATT-2024-49588'
# 		""")
 
# @frappe.whitelist()
# def update_query():
# 	frappe.db.sql("""
# 		UPDATE `tabOver Time Request`
# 			SET workflow_state = 'Approved'
# 			WHERE 	name ='OT Req-610743'
# 		""") 

# @frappe.whitelist()
# def update_query():
#     frappe.db.sql("""
#         UPDATE `tabLeave Application`
#         SET workflow_state = %s
#         WHERE name = %s
#     """, ('FM Pending', 'HR-ATT-2024-43438'))
    

# @frappe.whitelist()
# def update_query():
#     frappe.db.sql("""
#         UPDATE `tabAttendance`
#         SET status = 'Present'
#         WHERE name IN ('HR-ATT-2024-45012','HR-ATT-2024-37118','HR-ATT-2024-37136','HR-ATT-2024-39035','HR-ATT-2024-39034')
#     """)



# @frappe.whitelist()
# def update_query():
#     frappe.db.sql("""
#         UPDATE `tabAttendance`
#             SET custom_early_out_time = "00:00:00"
#             WHERE attendance_date BETWEEN '2024-06-01' AND '2024-06-30'
#         """)		

# @frappe.whitelist()
# def update_query():
#     frappe.db.sql("""
#         DELETE from `tabOver Time Request` where ot_date BETWEEN "2024-06-01" AND "2024-06-30"
#     """)
# @frappe.whitelist()
# def update_employee():
# 	employees = frappe.get_all("Employee", {"status": "Active",}, ['*'])
# 	for i in employees:
# 		if i.custom_basic < 15000:
# 			basic=i.custom_basic * 0.13
# 			frappe.db.set_value("Employee",i.name,"custom_pf",basic)
# 		else:
# 			frappe.db.set_value("Employee",i.name,"custom_pf",1950)
            

def ot_calculation():
    from_date = "2024-07-06"
    to_date = "2024-07-06"
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for att in attendance:
        ot_hours = None
        if att.shift and att.out_time and att.in_time:
            shift_et = frappe.db.get_value("Shift Type",{'name':att.shift},['end_time'])
            out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
            shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
            if shift_et < out_time:
                difference = time_diff_in_timedelta_1(shift_et,out_time)
                diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                if diff_time.hour > 0:
                    if diff_time.minute >= 50:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 50:
                        ot_hours = time(1,0,0)
                else:
                    ot_hours = "00:00:00"			
        else:
            ot_hours = "00:00:00"
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)

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
        SELECT * FROM tabAttendance
        WHERE attendance_date = %s AND status = 'Absent' AND docstatus < 2
        ORDER BY employee
    """, (yesterday,), as_dict=True)
    
    
    
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
            recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
            subject='Absent Report',
            message="""Dear Sir,<br><br>
                Kindly find the attached Employee Absent Employee List for yesterday({1}):<br>{0}
                """.format(staff,format_date(yesterday))
        )


@frappe.whitelist()
def cron_job_absent():
    job = frappe.db.exists('Scheduled Job Type', 'absent_mail_alert')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.absent_mail_alert',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

  
@frappe.whitelist()
def cron_job_leave():
    job = frappe.db.exists('Scheduled Job Type', 'leave_report')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.leave_report',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def od_report():
    yesterday = add_days(frappe.utils.today(), -1)
    employee = frappe.db.sql("""
        SELECT `tabMulti Employee`.employee_id, `tabMulti Employee`.employee_name, `tabOn Duty Application`.department, `tabOn Duty Application`.name, `tabOn Duty Application`.from_date_session
        FROM `tabOn Duty Application`
        LEFT JOIN `tabMulti Employee` ON `tabMulti Employee`.parent = `tabOn Duty Application`.name
        WHERE `tabOn Duty Application`.from_date = %s AND `tabOn Duty Application`.docstatus = 1
        """, (yesterday,), as_dict=True)
    
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
        """.format(idx, i.employee_id, i.employee_name, i.department, i.name or ' ', i.from_date_session or '')
        
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
            recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='On Duty Application Report',
            message="""Dear Sir,<br><br>
                    Kindly find the attached Employee On Duty Application List for yesterday:<br>{0}
                    """.format(staff)
        )

@frappe.whitelist()
def cron_job_od():
    job = frappe.db.exists('Scheduled Job Type', 'od_report')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.od_report',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def permission_request_report():
    yesterday = add_days(frappe.utils.today(), -1)
    permission = frappe.db.sql("""
        SELECT * FROM `tabPermission Request`
        WHERE attendance_date = %s AND docstatus = 1
        ORDER BY employee
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
            recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='Permission Request Report',
            message="""Dear Sir,<br><br>
                Kindly find the attached employee permission request list for yesterday:<br>{0}
                """.format(staff)
        )
@frappe.whitelist()
def cron_job_permission():
    job = frappe.db.exists('Scheduled Job Type', 'permission_request_report')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.permission_request_report',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

# @frappe.whitelist()
# def permission_request_hod():
#     permission = frappe.db.sql("""
#         SELECT * FROM `tabPermission Request`
#         WHERE workflow_state="Pending for HOD"
#         order by employee
#     """, as_dict=True)
#     staff = """
#         <div style="text-align: center;">
#                 <h2 style="font-size: 16px;">Permission Request Report</h2>
#             </div>
#             <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
#                 <tr style="border: 1px solid black;">
#                     <th style="padding: 4px; border: 1px solid black;">Employee</th>
#                     <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
#                     <th style="padding: 4px; border: 1px solid black;">Permission Request</th>
#                     <th style="padding: 4px; border: 1px solid black;">Session</th>

#                 </tr>
#         """
#     for per in permission:		
#             staff += """
#             <tr style="border: 1px solid black;">
#                 <td style="padding: 4px; border: 1px solid black;">{0}</td>
#                 <td style="padding: 4px; border: 1px solid black;">{1}</td>
#                 <td style="padding: 4px; border: 1px solid black;">{2}</td>
#                 <td style="padding: 4px; border: 1px solid black;">{3}</td>
                
#             </tr>
#             """.format(per.employee, per.employee_name,
#                     per.name or ' ',per.session or '')
#     staff += "</table>"
#     user = frappe.db.sql("""
#                     SELECT `tabUser`.name as name
#                     FROM `tabUser`
#                     LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name where `tabHas Role`.Role="HOD" and `tabUser`.enabled=1
#                     """,as_dict=True)
#     if permission:
#         for i in user:
#             frappe.sendmail(
#                 recipients=[i.name],
#                 subject='Permission Request Report',
#                 message="""Dear Sir/Mam,<br><br>
#                         Kindly Find the list of Permission Request waiting for your Approval:<br>{0}
#                         """.format(staff)
#             ) 
#         frappe.sendmail(
#                 recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
#                 subject='Permission Request Report',
#                 message="""Dear Sir,<br><br>
#                         Kindly Find the list of Permission Request waiting for your Approval:<br>{0}
#                         """.format(staff)
#             )

# @frappe.whitelist()
# def cron_job_perhod():
#     job = frappe.db.exists('Scheduled Job Type', 'permission_request_hod')
#     if not job:
#         att = frappe.new_doc("Scheduled Job Type")
#         att.update({
#             "method": 'ir.custom.permission_request_hod',
#             "frequency": 'Cron',
#             "cron_format": '0 8 * * *'
#         })
#         att.save(ignore_permissions=True)

@frappe.whitelist()
def permission_request_firstmanager():
    
    permission_requests = frappe.db.sql("""
        SELECT name, employee, employee_name, session, custom_first_manager
        FROM `tabPermission Request`
        WHERE workflow_state="FM Pending"
        ORDER BY employee
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
        recipients=['siva.m@groupteampro.com', 'arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
        subject='Permission Request Report',
        message="""Dear Sir,<br><br>
        Kindly find the list of Permission Requests waiting for approval:<br>{0}
        """.format(staff)
    )
    
@frappe.whitelist()
def cron_job_perfm():
    job = frappe.db.exists('Scheduled Job Type', 'permission_request_firstmanager')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.permission_request_firstmanager',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def permission_request_secondmanager():
    
    permission_requests = frappe.db.sql("""
        SELECT name, employee, employee_name, session, custom_second_manager
        FROM `tabPermission Request`
        WHERE workflow_state="SM Pending"
        ORDER BY employee
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
        recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'siva.m@groupteampro.com', 'jenisha.p@groupteampro.com'],
        subject='Permission Request Report',
        message="""Dear Sir,<br><br>
        Kindly find the list of Permission Requests waiting for your approval:<br>{0}
        """.format(staff)
    )
    
@frappe.whitelist()
def cron_job_persm():
    job = frappe.db.exists('Scheduled Job Type', 'permission_request_secondmanager')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.permission_request_secondmanager',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def leave_application_secondmanager_test():
    
    leave_applications = frappe.db.sql("""
        SELECT name, employee, employee_name, leave_type, custom_second_manager
        FROM `tabLeave Application`
        WHERE workflow_state="SM Pending"
        ORDER BY employee
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
            recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='Leave Application Report',
            message="""Dear Sir,<br><br>
            Kindly find the list of Leave Applications waiting for your approval:<br>{0}
            """.format(staff)
        )

@frappe.whitelist()
def cron_job_leavesm():
    job = frappe.db.exists('Scheduled Job Type', 'leave_application_secondmanager_test')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.leave_application_secondmanager_test',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True) 

@frappe.whitelist()
def leave_application_firstmanager_test():
    
    leave_applications = frappe.db.sql("""
        SELECT name, employee, employee_name, leave_type, custom_first_manager
        FROM `tabLeave Application`
        WHERE workflow_state="FM Pending"
        ORDER BY employee
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
            recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
            subject='Leave Application Report',
            message="""Dear Sir,<br><br>
            Kindly find the list of Leave Applications waiting for your approval:<br>{0}
            """.format(staff)
        )



@frappe.whitelist()
def cron_job_leavehod():
    job = frappe.db.exists('Scheduled Job Type', 'leave_application_firstmanager_test')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.leave_application_firstmanager_test',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def leave_application_hod_format():
    
    leave = frappe.db.sql("""
        SELECT name, employee, employee_name, department, leave_type, from_date, to_date
        FROM `tabLeave Application`
        WHERE workflow_state = 'HR Pending'
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
        recipients=['arockia.k@groupteampro.com','siva.m@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'jenisha.p@groupteampro.com'],
        # recipients=['arockia.k@groupteampro.com', 'jenisha.p@groupteampro.com'],
        subject='Leave Application Report - HR Pending',
        message="""Dear Sir,<br><br>
            Kindly find the list of leave applications waiting for your approval:<br>{0}
        """.format(staff)
    )

@frappe.whitelist()
def cron_job_leavehod_test():
    job = frappe.db.exists('Scheduled Job Type', 'leave_application_hod_format')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.leave_application_hod_format',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)




@frappe.whitelist()
def od_hod():
    employee = frappe.db.sql("""
                    SELECT `tabMulti Employee`.employee_id, `tabMulti Employee`.employee_name , `tabOn Duty Application`.name,`tabOn Duty Application`.from_date_session,`tabOn Duty Application`.workflow_state
                    FROM `tabOn Duty Application`
                    LEFT JOIN `tabMulti Employee` ON `tabMulti Employee`.parent = `tabOn Duty Application`.name where `tabOn Duty Application`.Workflow_state="HR Pending"
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
    user = frappe.db.sql("""
                    SELECT `tabUser`.name as name
                    FROM `tabUser`
                    LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name where `tabHas Role`.Role="HOD" and `tabUser`.enabled=1
                    """,as_dict=True)
    if employee:
        for i in user:
            frappe.sendmail(
                recipients=[i.name],
                subject='On Duty Application Report',
                message="""Dear Sir/Mam,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )
        frappe.sendmail(
                recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='On Duty Application Report',
                message="""Dear Sir,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )
@frappe.whitelist()
def cron_job_odhod():
    job = frappe.db.exists('Scheduled Job Type', 'od_hod')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.od_hod',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def od_firstmanager_format():
    try:
        # Fetch On Duty applications pending for the first manager's approval
        employees = frappe.db.sql("""
            SELECT `tabMulti Employee`.employee_id, `tabMulti Employee`.employee_name,
                   `tabOn Duty Application`.name, `tabOn Duty Application`.from_date_session,
                   `tabOn Duty Application`.workflow_state, `tabMulti Employee`.custom_first_manager
            FROM `tabOn Duty Application`
            LEFT JOIN `tabMulti Employee` ON `tabMulti Employee`.employee_id = `tabOn Duty Application`.employee
            WHERE `tabOn Duty Application`.workflow_state = "FM Pending"
        """, as_dict=True)

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
                    """.format(report.employee_id, report.employee_name, report.name or ' ', report.from_date_session or '')

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
                recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
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
                    SELECT `tabMulti Employee`.employee_id, `tabMulti Employee`.employee_name , `tabOn Duty Application`.name,`tabOn Duty Application`.from_date_session,`tabOn Duty Application`.workflow_state,`tabMulti Employee`.first_manager,`tabMulti Employee`.second_manager
                    FROM `tabOn Duty Application`
                    LEFT JOIN `tabMulti Employee` ON `tabMulti Employee`.parent = `tabOn Duty Application`.name where `tabOn Duty Application`.Workflow_state="Pending for Second Manager"
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
                recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='On Duty Application Report',
                message="""Dear Sir,<br><br>
                        Kindly Find the list of On Duty Application waiting for your Approval:<br>{0}
                        """.format(staff)
            )
@frappe.whitelist()
def cron_job_odsm():
    job = frappe.db.exists('Scheduled Job Type', 'od_secondmanager')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.od_secondmanager',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

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
        filters={"attendance_date": yesterday, "docstatus": ("!=", 2)},
        fields=["name", "employee", "employee_name", "department", "custom_ot_hours", "status", "custom_employee_category", "attendance_date", "shift"]
    )

    for att in attendance:
        # Check if OT hours are applicable and the employee is not absent
        if att.custom_ot_hours and att.status != "Absent":
            ot_applicable = frappe.db.get_value("Employee", {"name": att.employee}, "custom_ot_applicable")

            # Only include "White Collar" employees with OT applicable
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

    if attendance:
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
        recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com'],
        subject='OT Hours Report',
        message="""Dear Sir,<br><br>
            Kindly find the attached Employee OT Hours List for yesterday:<br>{0}
        """.format(staff)
    )



@frappe.whitelist()
def cron_job_ot_mail_alert():
    job = frappe.db.exists('Scheduled Job Type', 'ot_hours_mail_alert')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.ot_hours_mail_alert',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

# @frappe.whitelist()
# def late_entry_mail_alert():
#     yesterday = add_days(frappe.utils.today(), -1)
#     attendance = frappe.db.sql("""
#         SELECT * FROM tabAttendance
#         WHERE attendance_date = %s AND docstatus != 2
#         order by employee
#     """, (yesterday,), as_dict=True)
#     staff = """
#         <div style="text-align: center;">
#             <h2 style="font-size: 16px;">Late Entry Report</h2>
#         </div>
#         <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
#             <tr style="border: 1px solid black;">
#                 <th style="padding: 4px; border: 1px solid black;">Employee</th>
#                 <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
#                 <th style="padding: 4px; border: 1px solid black;">Department</th>
#                 <th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
#                 <th style="padding: 4px; border: 1px solid black;">Late Entry Time</th>
#                 <th style="padding: 4px; border: 1px solid black;">Shift</th>
#             </tr>
#     """
#     no_ot = True
#     for att in attendance:
#         if att.late_entry:
#             if att.custom_late_entry_time:
#                 dt = datetime.strptime(str(att.custom_late_entry_time), "%H:%M:%S.%f")
#                 time_string_no_ms = dt.strftime("%H:%M:%S")
#                 no_ot = False
#                 staff += """
#                 <tr style="border: 1px solid black;">
#                     <td style="padding: 4px; border: 1px solid black;">{0}</td>
#                     <td style="padding: 4px; border: 1px solid black;">{1}</td>
#                     <td style="padding: 4px; border: 1px solid black;">{2}</td>
#                     <td style="padding: 4px; border: 1px solid black;text-align: center;">{3}</td>
#                     <td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
#                     <td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
#                 </tr>
#                 """.format(att.employee, att.employee_name, att.department,
#                         format_date(att.attendance_date) or ' ',time_string_no_ms or ' ',
#                             att.shift or ' ')
#     if no_ot:
#         staff = """
#         <div style="text-align: center;">
#             <h2 style="font-size: 16px;">No Late Entry for yesterday.</h2>
#         </div>
#         """
#     else:
#         staff += "</table>"
#     if attendance:	
#         frappe.sendmail(
#                 recipients=['arockia.k@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com', 'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com', 'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'],
#                 subject='Late Entry Report',
#                 message="""Dear Sir,<br><br>
#                         Kindly find the attached Employee Late Entry List for yesterday:<br>{0}
#                         """.format(staff)
#             )

@frappe.whitelist()
def cron_late_entry():
    job = frappe.db.exists('Scheduled Job Type', 'late_entry_mail_alert')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.late_entry_mail_alert',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)



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
            draft_leave_applications = frappe.get_all("Leave Application", {"employee": doc.employee,"docstatus":0 ,"leave_type": doc.leave_type},["*"])
            for i in draft_leave_applications:
                frappe.errprint(i.name)
                total_leave_days_present+=i.total_leave_days
            total_leave_days_present += doc.total_leave_days
            available=total_lbalance-total_leave_days_present
            frappe.errprint(total_lbalance)
            frappe.errprint(total_leave_days_present)
            frappe.errprint(available)
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
    frappe.errprint('Hello')
    attendance = frappe.get_all("Attendance", filters={"attendance_date":("between",(from_date,to_date)), "docstatus": ("!=", 2)}, fields=["*"])
    for att in attendance:
        if att.shift and att.in_time and att.out_time:
            frappe.errprint('Work')
            if att.custom_ot_hours and att.custom_ot_hours > timedelta(hours=0, minutes=0, seconds=0):
                frappe.errprint('In')
                if att.status !="Absent":
                    frappe.errprint('Working')
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
                            frappe.errprint('Worked')
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

    # recipients = ['amar.p@groupteampro.com', 'sivarenisha.m@groupteampro.com']
    recipients = ['amar.p@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com',
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
            SELECT COUNT(status) AS shift1_count, SUM(custom_ot_hours) AS shift1_overtime
            FROM `tabAttendance`
            WHERE attendance_date =%s
            AND docstatus != 2
            AND in_time IS NOT NULL
            AND department = %s 
            AND shift = '1'
        """, (yesterday, department), as_dict=True)

        shift1_count = shift1_data[0].shift1_count if shift1_data and shift1_data[0].shift1_count is not None else 0
        shift1_overtime = shift1_data[0].shift1_overtime if shift1_data and shift1_data[0].shift1_overtime is not None else 0.0
        shift1_overtime_hours = flt(shift1_overtime) / 10000

        shift2_data = frappe.db.sql("""
            SELECT COUNT(status) AS shift2_count, SUM(custom_ot_hours) AS shift2_overtime
            FROM `tabAttendance`
            WHERE attendance_date =%s
            AND docstatus != 2
            AND in_time IS NOT NULL
            AND department = %s 
            AND shift = '2'
        """, (yesterday, department), as_dict=True)

        shift2_count = shift2_data[0].shift2_count if shift2_data and shift2_data[0].shift2_count is not None else 0
        shift2_overtime = shift2_data[0].shift2_overtime if shift2_data and shift2_data[0].shift2_overtime is not None else 0.0
        shift2_overtime_hours = flt(shift2_overtime) / 10000
        
        shiftg_data = frappe.db.sql("""
            SELECT COUNT(status) AS shiftg_count, SUM(custom_ot_hours) AS shiftg_overtime
            FROM `tabAttendance`
            WHERE attendance_date =%s
            AND docstatus != 2
            AND in_time IS NOT NULL
            AND department = %s 
            AND shift = 'G'
        """, (yesterday, department), as_dict=True)

        shiftg_count = shiftg_data[0].shiftg_count if shiftg_data and shiftg_data[0].shiftg_count is not None else 0
        shiftg_overtime = shiftg_data[0].shiftg_overtime if shiftg_data and shiftg_data[0].shiftg_overtime is not None else 0.0
        shiftg_overtime_hours = flt(shiftg_overtime) / 10000

        shift3_data = frappe.db.sql("""
            SELECT COUNT(status) AS shift3_count, SUM(custom_ot_hours) AS shift3_overtime
            FROM `tabAttendance`
            WHERE attendance_date =%s
            AND docstatus != 2
            AND in_time IS NOT NULL
            AND department = %s 
            AND shift = '3'
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
def cron_job_head_count():
    job = frappe.db.exists('Scheduled Job Type', 'head_count_mail_alert')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.head_count_mail_alert',
            "frequency": 'Cron',
            "cron_format": '0 8 * * *'
        })
        att.save(ignore_permissions=True)

@frappe.whitelist()
def late_entry_mail_alert_for_G_shift():
    today = frappe.utils.today()
    attendance = frappe.db.sql("""
        SELECT * FROM tabAttendance
        WHERE attendance_date = %s AND docstatus != 2
        order by employee
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
                # recipients=['amar.p@groupteampro.com', 'jenisha.p@groupteampro.com', 'sivarenisha.m@groupteampro.com'],
                recipients=['amar.p@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com', 'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com', 'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='Late Entry Report',
                message="""Dear Sir,<br><br>
                        Kindly find the attached Employee Late Entry List for today:<br>{0}
                        """.format(staff)
            )

@frappe.whitelist()
def cron_job_late_entry_for_G_shift():
    job = frappe.db.exists('Scheduled Job Type', 'late_entry_mail_alert_for_G_shift')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.late_entry_mail_alert_for_G_shift',
            "frequency": 'Cron',
            "cron_format": '30 08 * * *'
        })
        att.save(ignore_permissions=True)
  
@frappe.whitelist()
def late_entry_mail_alert_for_2_shift():
    today = frappe.utils.today()
    attendance = frappe.db.sql("""
        SELECT * FROM tabAttendance
        WHERE attendance_date = %s AND docstatus != 2
        order by employee
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
                # recipients=['amar.p@groupteampro.com', 'jenisha.p@groupteampro.com', 'sivarenisha.m@groupteampro.com'],
                recipients=['amar.p@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com', 'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com', 'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'],
                subject='Late Entry Report',
                message="""Dear Sir,<br><br>
                        Kindly find the attached Employee Late Entry List for today:<br>{0}
                        """.format(staff)
            )

@frappe.whitelist()
def cron_job_late_entry_for_evng_shift():
    job = frappe.db.exists('Scheduled Job Type', 'late_entry_mail_alert_for_2_shift')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'ir.custom.late_entry_mail_alert_for_2_shift',
            "frequency": 'Cron',
            "cron_format": '0 18 * * *'
        })
        att.save(ignore_permissions=True)

# @frappe.whitelist()
# def update_attendance_status():
#     frappe.db.sql("""
#         UPDATE `tabAttendance`
#             SET custom_early_out_time = "00:00:00" , custom_total_working_hours = "00:00:00" , custom_ot_hours = "00:00:00" , custom_late_entry_time = "00:00:00"
#             WHERE status = 'On Leave' and status = 'Absent'
#         """)
#     frappe.db.sql("""update `tabAttendance` set custom_late_entry_time = "00:00:00" where late_entry = 0 """,as_dict = True)

    # checkin = frappe.db.sql("""update `tabAttendance` set status = 'Present' where name= 'HR-ATT-2024-44664' """,as_dict = True)
    
    
# import frappe
# from datetime import datetime, timedelta

# @frappe.whitelist()
# def mark_cc(from_date,to_date):
#     attendance = frappe.db.get_all('Attendance', filters={
#         'attendance_date': ['between', (from_date, to_date)],
#         'docstatus': ['!=', '2']
#     }, fields=['name', 'shift', 'in_time', 'out_time', 'employee', 'custom_on_duty_application', 'employee_name', 'department', 'attendance_date', 'status'])

#     for att in attendance:
#         in_time1 = att.in_time
#         out_time1 = att.out_time

#         if in_time1 and out_time1:

            
#             if in_time1.date() != out_time1.date():
#                 if att.attendance_date == in_time1.date():
#                     out_time1 = datetime.combine(att.attendance_date, datetime.min.time()) + timedelta(days=1)

            
#             shift_doc = frappe.get_value('Shift Type', {'name': att.shift}, ['custom_night_shift'])
#             if shift_doc == 1:
               
#                 cc_exists = frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
#                 if not cc_exists:
                    
#                     cc = frappe.new_doc('Canteen Coupons')
#                     cc.employee = att.employee
#                     cc.employee_name = att.employee_name
#                     cc.department = att.department
#                     cc.date = att.attendance_date
#                     cc.attendance = att.name

                   
#                     items_to_add = []
#                     fm = frappe.db.sql("""SELECT * FROM `tabFood Menu` ORDER BY serial_no""", as_dict=True)
#                     for f in fm:
#                         items_to_add.append({
#                             'item': f.name,
#                             'status': 0
#                         })

#                     cc.set('items', items_to_add)
#                 else:
                    
#                     cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})

                
#                 time_in = in_time1.time()
#                 time_out = out_time1.time()

               
#                 for item in cc.get('items'):
#                     food_menu = frappe.get_doc('Food Menu', item.get('item'))

#                     from_time = (datetime.min + food_menu.from_time).time()
#                     to_time = (datetime.min + food_menu.to_time).time()

                   
#                     if time_in <= to_time and time_out >= from_time:
#                         item.status = 1
#                     elif item.item == "Dinner" and time_out <= to_time:
#                         item.status = 1

                
#                 cc.save(ignore_permissions=True)
#                 frappe.db.commit()




import frappe

@frappe.whitelist()
def update_second_manager():
    
    overtime_requests = frappe.db.get_all('Over Time Request', ['name', 'employee'])
    
    for request in overtime_requests:
        
        second_manager, second_manager_name = frappe.db.get_value('Employee', request['employee'], ['custom_second_manager', 'custom_second_manager_name'])

        if second_manager and second_manager_name:
            
            frappe.db.set_value('Over Time Request', request['name'], {
                'custom_second_manager': second_manager,
                'custom_second_manager_name': second_manager_name
            })

def ot_calculation():
    from_date = "2024-08-01"
    to_date = "2024-08-18"
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for att in attendance:
        ot_hours = '00:00:00'
        if att.shift and att.out_time and att.in_time :
            shift_et = frappe.db.get_value("Shift Type",{'name':att.shift},['end_time'])
            night_shift = frappe.db.get_value("Shift Type",{"name":att.shift},["custom_night_shift"])
            if night_shift == 1:
                if att.attendance_date != datetime.date(att.out_time):
                    out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                    shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                    if shift_et < out_time:
                        difference = time_diff_in_timedelta_1(shift_et,out_time)
                        diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                        
                        if diff_time.hour > 0 <3:
                            if diff_time.minute >= 50:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 50:
                                ot_hours = time(1,0,0)
                            else:
                                ot_hours = "00:00:00" 
                        elif diff_time.hour > 3:
                            if diff_time.minute >= 50:
                                ot_hours = time(diff_time.hour-1,0,0)
                            else:
                                ot_hours = time(diff_time.hour-1,0,0)
                        else:
                            ot_hours = "00:00:00"
                    else:
                        ot_hours = "00:00:00"
                else:
                    ot_hours = "00:00:00"
            else:
                out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                if shift_et < out_time:
                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                    
                    if diff_time.hour > 0 <3:
                        if diff_time.minute >= 50:
                            ot_hours = time(diff_time.hour+1,0,0)
                        else:
                            ot_hours = time(diff_time.hour,0,0)
                    elif diff_time.hour == 0:
                        if diff_time.minute >= 50:
                            ot_hours = time(1,0,0)
                        else:
                            ot_hours = "00:00:00" 
                    elif diff_time.hour > 3:
                        if diff_time.minute >= 50:
                            ot_hours = time(diff_time.hour-1,0,0)
                        else:
                            ot_hours = time(diff_time.hour-1,0,0)
                    else:
                        ot_hours = "00:00:00"
                else:
                    ot_hours = "00:00:00"
        else:
            ot_hours = "00:00:00"
        print(ot_hours)
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
        if ot_hours !='00:00:00':
            ftr = [3600,60,1]
            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
            ot_hr = round(hr/3600,1)
        else:
            ot_hr = '0.0'	
        
        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
        
    
@frappe.whitelist()
def check_on_duty(doc, method):
    value = frappe.db.sql("""
        SELECT name FROM `tabOn Duty Application` 
        WHERE employee = %s 
        AND docstatus != 2 
        AND (from_date BETWEEN %s AND %s OR from_date BETWEEN %s AND %s 
             OR (from_date <= %s AND from_date >= %s))
        AND from_date_session = 'Full Day'
    """, (doc.employee, doc.from_date, doc.to_date, doc.from_date, doc.to_date, doc.from_date, doc.to_date))

    if value:
        frappe.throw("You have already applied for an On Duty Application for the same or overlapping date range.")
        
        
                
