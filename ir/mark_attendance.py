# IR Current mark_attendance.py

from __future__ import print_function
from pickle import TRUE
from time import strptime
from traceback import print_tb
import frappe
from frappe.utils.data import ceil, get_time, get_year_start
# import pandas as pd
import json
import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from datetime import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
import requests
from datetime import date, timedelta,time
from datetime import datetime, timedelta
from frappe.utils import get_url_to_form
import math
import dateutil.relativedelta
import datetime as dt
from datetime import datetime, timedelta

status_map = {
    "Present": "P",
    "Absent": "A",
    "Half Day": "HD",
    "On Leave":"On Leave",
    "Work From Home": "WFH",
    "Holiday": "HH",
    "Weekly Off": "WW",
    "Leave Without Pay": "LOP",
    "Casual Leave": "CL",
    "Earned Leave": "EL",
    "ESI Leave": "ESI",
    "Compensatory Off": "C-OFF",
}

@frappe.whitelist()
def mark_att_process_manual():
    from_date = add_days(today(),-2)  
    to_date = today()
    dates = get_dates(from_date,to_date)
    for date in dates:
        from_date = add_days(date,0)
        to_date = date
        mark_att(from_date,to_date)
        mark_cc(from_date,to_date)
    return "ok"

# @frappe.whitelist()
# def delete_query():
#     frappe.db.sql("""DELETE FROM `tabAttendance` WHERE leave_application = 'HR-LAP-2024-00447'""")

@frappe.whitelist()
def mark_att_process():
    from_date = add_days(today(),-1)  
    to_date = today()
    # from_date="2024-09-17"
    # to_date="2024-09-18"
    dates = get_dates(from_date,to_date)
    dt = []
    frappe.log_error(title='dt',message=[from_date,to_date])
        
        
    mark_att(from_date,to_date)
    mark_cc(from_date,to_date)
    return "ok"

def get_dates(from_date,to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    return dates
@frappe.whitelist()
def mark_att(from_date,to_date):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    mark_absent(from_date,to_date)
    mark_wh(from_date,to_date)
    ot_calculation(from_date,to_date)
    

def ot_calculation(from_date,to_date):
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for att in attendance:
        ot_hours = '00:00:00'
        if att.shift and att.out_time and att.in_time :
            hh = check_holiday(att.attendance_date,att.employee)
            if not hh:
                shift_et = frappe.db.get_value("Shift Type",{'name':att.shift},['end_time'])
                night_shift = frappe.db.get_value("Shift Type",{"name":att.shift},["custom_night_shift"])
                if night_shift == 1:
                    if att.attendance_date != datetime.date(att.out_time):
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        if shift_et < out_time:
                            difference = time_diff_in_timedelta_1(shift_et,out_time)
                            diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                    frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                    if ot_hours !='00:00:00':
                        ftr = [3600,60,1]
                        hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                        ot_hr = round(hr/3600,1)
                    else:
                        ot_hr = '0.0'	
                    frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
                else:
                    out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                    shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                    if shift_et < out_time:
                        difference = time_diff_in_timedelta_1(shift_et,out_time)
                        diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                    frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                    if ot_hours !='00:00:00':
                        ftr = [3600,60,1]
                        hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                        ot_hr = round(hr/3600,1)
                    else:
                        ot_hr = '0.0'	
                    frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
            else:
                in_time = att.in_time
                out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                if diff_time.hour > 0:
                    if diff_time.minute >= 55:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 55:
                        ot_hours = time(1,0,0)
                    else:
                        ot_hours = "00:00:00" 
                    
                else:
                    ot_hours = "00:00:00"
                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                if ot_hours !='00:00:00':
                    ftr = [3600,60,1]
                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                    ot_hr = round(hr/3600,1)
                else:
                    ot_hr = '0.0'	
                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)  
        else:
            ot_hours = "00:00:00"		
            frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
            if ot_hours !='00:00:00':
                ftr = [3600,60,1]
                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                ot_hr = round(hr/3600,1)
            else:
                ot_hr = '0.0'	
            frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         


        print(ot_hours)
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
        if ot_hours !='00:00:00':
            ftr = [3600,60,1]
            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
            ot_hr = round(hr/3600,1)
        else:
            ot_hr = '0.0'	
        
        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)


def time_diff_in_timedelta_1(time1, time2):
    datetime1 = datetime.combine(datetime.min, time1)
    datetime2 = datetime.combine(datetime.min, time2)
    timedelta_seconds = (datetime2 - datetime1).total_seconds()
    diff_timedelta = timedelta(seconds=timedelta_seconds)
    return diff_timedelta

def mark_attendance_from_checkin(employee,time,log_type):
    att_date = time.date()
    att_time = time.time()
    shift = ''
    if log_type == 'IN' and datetime.strptime('05:00:00', '%H:%M:%S').time() < att_time < datetime.strptime('22:00:00', '%H:%M:%S').time():
        frappe.errprint("In")
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "05:00:00" and "22:00:00" order by time ASC"""%(employee,att_date),as_dict=True)
        # if frappe.db.exists('Employee',{'name':employee,"custom_employee_category":"White Collar"}):
        # 	default_shift = frappe.db.get_value('Employee',{'name':employee},['default_shift'])
        # 	if default_shift:
        # 		shift=default_shift
        # 	else:
        # 		shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkin_start_time','custom_checkin_end_time'])
        # 		shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkin_start_time','custom_checkin_end_time'])
        # 		shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkin_start_time','custom_checkin_end_time'])
        # 		if (datetime.min + shiftg[0]).time() < checkins[0].time.time() < (datetime.min + shiftg[1]).time():
        # 			shift = 'G'
        # 		elif (datetime.min + shift2[0]).time() < checkins[0].time.time() < (datetime.min + shift2[1]).time():
        # 			shift = '2'
        # 		elif (datetime.min + shift3[0]).time() < checkins[0].time.time() < (datetime.min + shift3[1]).time():
        # 			shift ='3'
        # 			print("3")
        # 			print(checkins[0].time.time())
        # 		else:
        # 			shift = ''
        # else:
        actual_shift=frappe.db.get_value('Employee',{'name':employee},['custom_shift'])
        if actual_shift=='Single':
            shift=frappe.db.get_value('Employee',{'name':employee},['default_shift'])
        # elif
        else:
            shift1 = frappe.db.get_value('Shift Type',{'name':'1'},['custom_checkin_start_time','custom_checkin_end_time'])
            shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkin_start_time','custom_checkin_end_time'])
            shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkin_start_time','custom_checkin_end_time'])
            shift4 = frappe.db.get_value('Shift Type',{'name':'4'},['custom_checkin_start_time','custom_checkin_end_time'])
            shiftG = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkin_start_time','custom_checkin_end_time'])
            if (datetime.min + shift1[0]).time() < checkins[0].time.time() < (datetime.min + shift1[1]).time():
                shift = '1'
            elif (datetime.min + shift2[0]).time() < checkins[0].time.time() < (datetime.min + shift2[1]).time():
                shift = '2'
            elif (datetime.min + shift3[0]).time() < checkins[0].time.time() < (datetime.min + shift3[1]).time():
                shift ='3'
            elif (datetime.min + shift4[0]).time() < checkins[0].time.time() < (datetime.min + shift4[1]).time():
                shift ='4'
            elif (datetime.min + shiftG[0]).time() < checkins[0].time.time() < (datetime.min + shiftG[1]).time():
                shift ='G'
            else:
                shift = ''
        att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "05:00:00" and "22:00:00" order by time ASC"""%(employee,att_date),as_dict=True)
        if not att and checkins:
            att = frappe.new_doc("Attendance")
            att.employee = employee
            att.attendance_date = att_date
            att.shift = shift
            att.status = 'Absent'
            att.in_time = checkins[0].time
            att.custom_total_working_hours = "00:00:00"
            att.custom_ot_hours = "00:00:00"
            att.custom_extra_hours_total = "00:00:00"
            att.working_hours = "0.0"
            att.save(ignore_permissions=True)
            frappe.db.commit()
            for c in checkins:
                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
        else:
            att = frappe.get_doc("Attendance",att)
            if att.docstatus == 0:
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.status = 'Absent'
                att.in_time = checkins[0].time
                att.custom_total_working_hours = "00:00:00"
                att.working_hours = "0.0"
                att.custom_ot_hours = "00:00:00"
                att.custom_extra_hours_total = "00:00:00"
                att.save(ignore_permissions=True)
                frappe.db.commit()
                for c in checkins:
                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                return att 
    
    if log_type == 'OUT':
        frappe.errprint("OUT")
        max_out = datetime.strptime('10:30','%H:%M').time()
        in_time = frappe.db.get_value("Attendance",{"employee":employee,"attendance_date":att_date},["in_time"])
        if att_time < max_out:
            frappe.errprint("OUT")
            if in_time and in_time.time() < max_out:
                frappe.errprint("GREAT MAX OUT")
                checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time)<'%s' order by time ASC "%(employee,att_date,max_out),as_dict=True)
                att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
                if att:
                    att = frappe.get_doc("Attendance",att)
                    if att.docstatus == 0:
                        if not att.shift:
                            if len(checkins) > 0:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                                att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                                att.out_time = checkins[0].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        else:
                            if len(checkins) > 0:
                                att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                att.out_time = checkins[-1].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name, 'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        # att.status = 'Absent'    
                        att.save(ignore_permissions=True)
                        frappe.db.commit()
                        return att
                else:
                    att = frappe.new_doc("Attendance")
                    att.employee = employee
                    att.attendance_date = yesterday
                    att.status = 'Absent'
                    att.custom_ot_hours = "00:00:00"
                    att.custom_extra_hours_total = "00:00:00"
                    if len(checkins) > 0:
                        att.out_time = checkins[-1].time
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                        for c in checkins:
                            frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                    else:
                        att.out_time = checkins[-1].time
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                        frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    return att
            else:
                frappe.errprint("LESS MAX OUT")
                yesterday = add_days(att_date,-1)
                checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time)<'%s' order by time ASC "%(employee,att_date,max_out),as_dict=True)
                att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':yesterday,"docstatus":("!=",2)})
                if att:
                    frappe.errprint(yesterday)
                    att = frappe.get_doc("Attendance",att)
                    frappe.errprint(att)
                    if att.docstatus == 0:
                        frappe.errprint(att.docstatus)
                        if not att.shift:
                            frappe.errprint("Employee")
                            if len(checkins) > 0:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                                att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                                att.out_time = checkins[0].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        else:
                            if len(checkins) > 0:
                                frappe.errprint(checkins[-1].time)
                                att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                frappe.errprint(att.name)
                                att.out_time = checkins[-1].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name, 'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        # att.status = 'Absent'    
                        att.save(ignore_permissions=True)
                        frappe.db.commit()
                        return att
                else:
                    att = frappe.new_doc("Attendance")
                    att.employee = employee
                    att.attendance_date = yesterday
                    att.status = 'Absent'
                    att.custom_ot_hours = "00:00:00"
                    att.custom_extra_hours_total = "00:00:00"
                    if len(checkins) > 0:
                        att.out_time = checkins[-1].time
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                        for c in checkins:
                            frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                    else:
                        att.out_time = checkins[-1].time
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                        frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    return att	
        else:
            checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' and time(time)>'%s' order by time ASC"%(employee,att_date,max_out),as_dict=True)
            att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':("!=",2)})
            if att:
                att = frappe.get_doc("Attendance",att)
                if att.docstatus == 0:
                    
                    if not att.shift:
                        if len(checkins) > 0:
                            if not att.shift:
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            if not att.shift:
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[0].time
                            frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    else:
                        if len(checkins) > 0:
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.out_time = checkins[0].time
                            frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    att.status = 'Absent'    
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
            else:
                att = frappe.new_doc("Attendance")
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.status = 'Absent'
                att.custom_ot_hours = "00:00:00"
                att.custom_extra_hours_total = "00:00:00"
                if len(checkins) > 0:
                    if not att.shift:
                        att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                    att.out_time = checkins[-1].time
                    for c in checkins:
                        frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                else:
                    if not att.shift:
                        att.shift = get_actual_shift(get_time(checkins[-1].time))
                    att.out_time = checkins[0].time
                    frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                att.save(ignore_permissions=True)
                frappe.db.commit()

def time_diff_in_timedelta(in_time, out_time):
    datetime_format = "%H:%M:%S"
    if out_time and in_time :
        return out_time - in_time

def get_actual_shift(get_shift_time,employee):
    from datetime import datetime
    from datetime import date, timedelta,time
    # if frappe.db.exists('Employee',{'name':employee,"custom_employee_category":"White Collar"}):
    # 	default_shift = frappe.db.get_value('Employee',{'name':employee},['default_shift'])
    # 	if default_shift:
    # 		shift=default_shift
    # 	else:
    # 		shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkout_start_time','custom_checkout_end_time'])
    # 		shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkout_start_time','custom_checkout_end_time'])
    # 		shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkout_start_time','custom_checkout_end_time'])
    # 		if (datetime.min + shiftg[0]).time() < get_shift_time < (datetime.min + shiftg[1]).time():
    # 			shift = 'G'
                
    # 		elif (datetime.min + shift2[0]).time() < get_shift_time < (datetime.min + shift2[1]).time():
    # 			shift = '2'
    # 		elif (datetime.min + shift3[0]).time() < get_shift_time < (datetime.min + shift3[1]).time():
    # 			shift ='3'
    # 			print("3")
    # 		else:
    # 			shift = ''
    # else:
    actual_shift=frappe.db.get_value('Employee',{'name':employee},['custom_shift'])
    if actual_shift=='Single':
        shift=frappe.db.get_value('Employee',{'name':employee},['default_shift'])
    else:
        shift1 = frappe.db.get_value('Shift Type',{'name':'1'},['custom_checkin_start_time','custom_checkin_end_time'])
        shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkin_start_time','custom_checkin_end_time'])
        shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkin_start_time','custom_checkin_end_time'])
        shift4 = frappe.db.get_value('Shift Type',{'name':'4'},['custom_checkin_start_time','custom_checkin_end_time'])
        shiftG = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkin_start_time','custom_checkin_end_time'])
        if (datetime.min + shift1[0]).time() < get_shift_time < (datetime.min + shift1[1]).time():
            shift = '1'
        elif (datetime.min + shift2[0]).time() < get_shift_time < (datetime.min + shift2[1]).time():
            shift = '2'
        elif (datetime.min + shift3[0]).time() < get_shift_time < (datetime.min + shift3[1]).time():
            shift ='3'
        elif (datetime.min + shift4[0]).time() < get_shift_time < (datetime.min + shift4[1]).time():
            shift ='4'
        elif (datetime.min + shiftG[0]).time() < get_shift_time < (datetime.min + shiftG[1]).time():
            shift ='G'
        else:
            shift = ''

    return shift


def mark_wh(from_date,to_date):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
    for att in attendance:
        update_late_deduction(att.employee,att.attendance_date)
        if att.in_time and att.out_time:
            if not att.on_duty_application:
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
            else:
                if att.session_from_time and att.session_to_time: 
                    in_time = att.session_from_time
                    out_time = att.session_to_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            
            wh = time_diff_in_hours(out_time,in_time)
            # wh = float(att_wh)
            default_shift=''
            actual_shift=frappe.db.get_value('Employee',{'name':att.employee},['custom_shift'])
            if actual_shift=='Single':
                default_shift=frappe.db.get_value('Employee',{'name':att.employee},['default_shift'])
            else:
                default_shift = frappe.db.get_value(
                    "Shift Assignment",
                    {'employee': att.employee, 'start_date': ('<=', att.attendance_date), 'end_date': ('>=', att.attendance_date), "docstatus": 1},
                    ['shift_type']
                )
            hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
            ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])    
            if default_shift:
                if default_shift == att.shift:
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < ab_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            elif att.custom_on_duty_application:
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half':
                                    if custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    totwh=wh+custom_od_time
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    elif totwh >= ab_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                                    frappe.errprint("Test")
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            totwh=0
                            custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                            custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                            if att.custom_attendance_permission:
                                totwh=wh+custom_permission_hours
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            elif att.custom_on_duty_application:
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half':
                                    if custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    totwh=wh+custom_od_time
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        elif wh >= hd_threshold:
                            frappe.db.set_value('Attendance',att.name,'status','Present')  
                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                    
                else:
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < ab_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')  
                        else:
                            frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                            frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
            else:
                if wh > 0 :
                    if wh < 24.0:
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < ab_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')  
                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                    
        hh = check_holiday(att.attendance_date,att.employee)
        if not hh:
            if att.shift and att.in_time:
                shift_time = frappe.get_value(
                    "Shift Type", {'name': att.shift}, ["start_time"])
                shift_start_time = datetime.strptime(
                    str(shift_time), '%H:%M:%S').time()
                start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                
                if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                    # print(att.in_time - start_time)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            


def mark_absent(from_date,to_date):
        dates = get_dates(from_date,to_date)
        for date in dates:
            employee = frappe.db.get_all('Employee',{'status':'Active','date_of_joining':['<=',from_date]})
            for emp in employee:
                hh = check_holiday(date,emp.name)
                if not hh:
                    if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':emp.name,'docstatus':('!=','2')}):
                        att = frappe.new_doc("Attendance")
                        att.employee = emp.name
                        att.status = 'Absent'
                        att.attendance_date = date
                        att.custom_total_working_hours = "00:00:00"
                        att.working_hours = "0.0"
                        att.custom_ot_hours = "00:00:00"
                        att.custom_extra_hours_total = "00:00:00"
                        att.save(ignore_permissions=True)
                        frappe.db.commit()

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
        if doj < holiday[0].holiday_date:
            if holiday[0].weekly_off == 1:
                status = "WW"
            else:
                status = "NH"
        else:
            status = 'Not Joined'
    return status


@frappe.whitelist()
def mark_att_cron():
    job = frappe.db.exists('Scheduled Job Type', 'mark_att_process')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method": 'ir.mark_attendance.mark_att_process',
            "frequency": 'Cron',
            "cron_format": '*/15 * * * *'
        })
        sjt.save(ignore_permissions=True)
    
@frappe.whitelist()
def mark_att_cron_manual():
    job = frappe.db.exists('Scheduled Job Type', 'mark_att_process_manual')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method": 'ir.mark_attendance.mark_att_process_manual',
            "frequency": 'Cron',
            "cron_format": '00 00 * * *'
        })
        sjt.save(ignore_permissions=True)

@frappe.whitelist()
def update_late_deduction(employee,attendance_date):
    # employee='HR-EMP-00002'
    # attendance_date='2024-05-27'
    month_start = get_first_day(attendance_date)
    attendance = frappe.db.sql("""select * from `tabAttendance` where employee ='%s' and attendance_date between '%s' and '%s' and docstatus!=2"""%(employee,month_start,attendance_date),as_dict=True)
    late=0
    late_min=0
    for att in attendance:
        if att.in_time and att.shift:
            shift_st = frappe.db.get_value("Shift Type",{'name':att.shift},['start_time'])
            in_time = datetime.strptime(str(att.in_time),'%Y-%m-%d %H:%M:%S').time()
            shift_st = datetime.strptime(str(shift_st), '%H:%M:%S').time()
            if shift_st < in_time:
                difference = time_diff_in_timedelta_1(shift_st,in_time)
                diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                
                late_min +=diff_time.minute
                frappe.db.set_value("Attendance",att.name,'custom_late',difference)
                if diff_time.minute > 0:
                    late+=1
                    if diff_time.minute >= 15 and late ==1:
                        pass
                    if diff_time.minute>=15 and late ==2:
                        if late_min>=30:
                            if att.late_entry==0:
                                emp=frappe.get_value("Employee",{"name":att.employee},['user_id'])
                                frappe.sendmail(
                                    recipients=[emp],
                                    subject=_("Warning - Late Entry"),
                                    message="""
                                        Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
                                        """%(att.employee)
                                )
                                frappe.db.set_value("Attendance",att.name,'late_entry',1)
                    if att.late_entry==0:
                        if late>2 and late<4:
                            if not att.custom_late:
                                emp=frappe.get_value("Employee",{"name":att.employee},['user_id'])
                                frappe.sendmail(
                                    recipients=[emp],
                                    subject=_("Warning - Late Entry"),
                                    message="""
                                        Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
                                        """%(att.employee)
                                )
                        elif late==5 or (late > 5 and (late - 5) % 3 == 0):
                            if not frappe.db.exists("Leave Ledger Entry",{'docstatus':1,'employee':att.employee,'from_date':month_start,'to_date':attendance_date}):
                                ad = frappe.new_doc('Leave Ledger Entry')
                                ad.employee = att.employee
                                ad.employee_name = att.employee_name
                                ad.from_date = month_start
                                ad.to_date = attendance_date
                                el = frappe.db.sql("""
                                    SELECT sum(leaves) 
                                    FROM `tabLeave Ledger Entry` 
                                    WHERE employee = %s 
                                    AND leave_type = 'Earned Leave'
                                    AND docstatus = 1
                                """, (att.employee))[0][0]
                                cl = frappe.db.sql("""
                                    SELECT sum(leaves) 
                                    FROM `tabLeave Ledger Entry` 
                                    WHERE employee = %s 
                                    AND leave_type = 'Casual Leave'
                                    AND docstatus = 1
                                """, (att.employee))[0][0]
                                if el:
                                    if el>0:
                                        ad.leave_type = 'Earned Leave'
                                elif cl:
                                    if cl>0:
                                        ad.leave_type = 'Casual Leave'
                                else:
                                    ad.leave_type = 'Leave without Pay'
                                ad.leaves =  -0.5
                                ad.save(ignore_permissions=1)
                                ad.submit()
                                frappe.db.commit()
                    elif late>2 and late<5:
                        if not att.custom_late:
                            emp=frappe.get_value("Employee",{"name":att.employee},['user_id'])
                            frappe.sendmail(
                                recipients=[emp],
                                subject=_("Warning - Late Entry"),
                                message="""
                                    Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
                                    """%(att.employee)
                            )
                    elif late==5 or (late > 5 and (late - 5) % 3 == 0):
                        if not frappe.db.exists("Leave Ledger Entry",{'docstatus':1,'employee':att.employee,'from_date':month_start,'to_date':attendance_date}):
                            ad = frappe.new_doc('Leave Ledger Entry')
                            ad.employee = att.employee
                            ad.employee_name = att.employee_name
                            ad.from_date = month_start
                            ad.to_date = attendance_date
                            el = frappe.db.sql("""
                                SELECT sum(leaves) 
                                FROM `tabLeave Ledger Entry` 
                                WHERE employee = %s 
                                AND leave_type = 'Earned Leave'
                                AND docstatus = 1
                            """, (att.employee))[0][0]
                            cl = frappe.db.sql("""
                                SELECT sum(leaves) 
                                FROM `tabLeave Ledger Entry` 
                                WHERE employee = %s 
                                AND leave_type = 'Casual Leave'
                                AND docstatus = 1
                            """, (att.employee))[0][0]
                            if el:
                                if el>0:
                                    ad.leave_type = 'Earned Leave'
                            elif cl:
                                if cl>0:
                                    ad.leave_type = 'Casual Leave'
                            else:
                                ad.leave_type = 'Leave without Pay'
                            ad.leaves = -0.5
                            ad.save(ignore_permissions=1)
                            ad.submit()
                            frappe.db.commit()
            else:
                frappe.db.set_value("Attendance",att.name,'custom_late_entry_time',"00:00:00")
        else:
            if att.status=='Absent' and not att.in_time and not att.shift:
                frappe.db.set_value("Attendance",att.name,'custom_late_entry_time',"00:00:00")

# def ot_calculation():
# 	attendance = frappe.db.sql("""select * from `tabAttendance` where name = 'HR-ATT-2024-39538'""",as_dict=True)
# 	for att in attendance:
# 		ot_hours = '00:00:00'
# 		if att.shift and att.out_time and att.in_time:
# 			shift_et = frappe.db.get_value("Shift Type",{'name':att.shift},['end_time'])
# 			out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
# 			shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
# 			if shift_et < out_time:
# 				difference = time_diff_in_timedelta_1(shift_et,out_time)
# 				diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
# 				if diff_time.hour > 0:
# 					if diff_time.minute >= 50:
# 						ot_hours = time(diff_time.hour+1,0,0)
# 					else:
# 						ot_hours = time(diff_time.hour,0,0)
# 				elif diff_time.hour == 0:
# 					if diff_time.minute >= 50:
# 						ot_hours = time(1,0,0)
# 				else:
# 					ot_hours = "00:00:00"			
# 		else:
# 			ot_hours = "00:00:00"
# 		if ot_hours !='00:00:00':
# 			ftr = [3600,60,1]
# 			hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
# 			ot_hr = round(hr/3600,1)
# 		else:
# 			ot_hr = '0.0'	
# 		frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
# 		frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)

@frappe.whitelist()
def update_att_without_employee(from_date,to_date):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where skip_auto_attendance = 0 and date(time) between '%s' and '%s' order by time  """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            mark_attendance_from_checkin(c.employee,c.time,c.log_type)
    # mark_absent(from_date,to_date)
    mark_wh_without_employee(from_date,to_date)
    return "ok"

@frappe.whitelist()    
def enqueue_update_att_with_employee(from_date,to_date,employee):
    frappe.errprint("Hello World")
    frappe.enqueue(
        update_att_with_employee, # python function or a module path as string
        queue="long", # one of short, default, long
        timeout=80000, # pass timeout manually
        is_async=True, # if this is True, method is run in worker
        now=False, # if this is True, method is run directly (not in a worker) 
        job_name='Attendance Setting with' + '' + employee,
        from_date=from_date,
        to_date=to_date,
        employee = employee
    ) 
    return 'OK'

@frappe.whitelist()
def update_att_with_employee(from_date,to_date,employee):
    frappe.errprint("Hello1")
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee='%s' order by time ASC """%(from_date,to_date,employee),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    # mark_absents(from_date,to_date,employee)
    mark_whs(from_date,to_date,employee)
    # ot_calculations(from_date,to_date,employee)
    return "ok"

@frappe.whitelist()
def update_att_with_department(from_date,to_date,department):
    employee = frappe.get_all('Employee',{'status':'Active','date_of_joining':['<=',from_date],'department':department},["*"])
    for i in employee:
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee = '%s' order by time ASC """%(from_date,to_date,i.name),as_dict=True)
        for c in checkins:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
        mark_whs(from_date,to_date,i.name)
    return "ok"

@frappe.whitelist()
def update_att_with_department_employee(from_date,to_date,department,name):
    employee = frappe.get_all('Employee',{'status':'Active','date_of_joining':['<=',from_date],'department':department,"name":name},["*"])
    for i in employee:
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee = '%s' order by time ASC """%(from_date,to_date,i.name),as_dict=True)
        for c in checkins:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
        mark_whs(from_date,to_date,i.name)
    return "ok"

@frappe.whitelist()    
def enqueue_update_att_with_department_employee(from_date,to_date,department,name):
    frappe.enqueue(
        update_att_with_department_employee, # python function or a module path as string
        queue="long", # one of short, default, long
        timeout=80000, # pass timeout manually
        is_async=True, # if this is True, method is run in worker
        now=False, # if this is True, method is run directly (not in a worker) 
        job_name='Attendance Setting with' + '' + department + '' +name,
        from_date=from_date,
        to_date=to_date,
        department = department,
        name = name
    ) 
    return 'OK'

@frappe.whitelist()    
def enqueue_update_att_with_department(from_date,to_date,department):
    frappe.enqueue(
        update_att_with_department, # python function or a module path as string
        queue="long", # one of short, default, long
        timeout=80000, # pass timeout manually
        is_async=True, # if this is True, method is run in worker
        now=False, # if this is True, method is run directly (not in a worker) 
        job_name='Attendance Setting with' + '' + department,
        from_date=from_date,
        to_date=to_date,
        department = department,

    ) 
    return 'OK'

@frappe.whitelist()
def mark_absents(from_date,to_date,employee):
        dates = get_dates(from_date,to_date)
        for date in dates:
            employee = frappe.db.get_all('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':employee})
            for emp in employee:
                hh = check_holiday(date,emp.name)
                if not hh:
                    if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':emp.name,'docstatus':('!=','2')}):
                        att = frappe.new_doc("Attendance")
                        att.employee = emp.name
                        att.status = 'Absent'
                        att.attendance_date = date
                        att.custom_total_working_hours = "00:00:00"
                        att.working_hours = "0.0"
                        att.custom_ot_hours = "00:00:00"
                        att.custom_extra_hours_total = "00:00:00"
                        att.save(ignore_permissions=True)
                        frappe.db.commit()


@frappe.whitelist()
def mark_whs(from_date,to_date,employee):
    frappe.errprint("matched1")
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'employee':employee},['*'])
    for att in attendance:
        att.custom_ot_hours = "00:00:00"
        att.custom_extra_hours_total ="00:00:00"
        if att.shift and att.in_time and att.out_time :
            if att.in_time and att.out_time:
                in_time = att.in_time
                out_time = att.out_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            wh = time_diff_in_hours(out_time,in_time)
            default_shift=''
            actual_shift=frappe.db.get_value('Employee',{'name':att.employee},['custom_shift'])
            if actual_shift=='Single':
                default_shift=frappe.db.get_value('Employee',{'name':att.employee},['default_shift'])
            else:
                default_shift = frappe.db.get_value(
                    "Shift Assignment",
                    {'employee': att.employee, 'start_date': ('<=', att.attendance_date), 'end_date': ('>=', att.attendance_date), "docstatus": 1},
                    ['shift_type']
                )
            hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
            ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])
            if default_shift:
                if att.shift == default_shift:
                    frappe.errprint("matched")
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < ab_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            elif att.custom_on_duty_application:
                                    frappe.errprint('custom_od_time')
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half':
                                        if custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        frappe.errprint(custom_od_time)
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                            frappe.errprint("Test")
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day') 
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent') 
                                    else:
                                        frappe.errprint("Test")
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            totwh=0
                            custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                            custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                            if att.custom_attendance_permission:
                                totwh=wh+custom_permission_hours
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            elif att.custom_on_duty_application:
                                frappe.errprint('custom_od_time')
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half':
                                    if custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    frappe.errprint(custom_od_time)
                                    totwh=wh+custom_od_time
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:     
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        elif wh >= hd_threshold:
                            frappe.db.set_value('Attendance',att.name,'status','Present')  
                        shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                        shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        ot_hours = "00:00:00"
                        hh = check_holiday(att.attendance_date,att.employee)
                        if not hh:
                            night_shift=frappe.db.get_value("Shift Type",{'name':att.shift},['custom_night_shift'])
                            if night_shift ==1:
                                if att.attendance_date != datetime.date(att.out_time):
                                    if shift_et < out_time:
                                        difference = time_diff_in_timedelta_1(shift_et,out_time)
                                        diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()                 
                                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                        if diff_time.hour > 3:
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
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         

                            else:
                                if shift_et < out_time:
                                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         
                                
                        else:
                            in_time = att.in_time
                            out_time = att.out_time
                            if isinstance(in_time, str):
                                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                            if isinstance(out_time, str):
                                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                            if diff_time.hour > 0:
                                if diff_time.minute >= 55:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 55:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                                
                            else:
                                ot_hours = "00:00:00"			
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         


                            print(ot_hours)
                            frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                            if ot_hours !='00:00:00':
                                ftr = [3600,60,1]
                                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                ot_hr = round(hr/3600,1)
                            else:
                                ot_hr = '0.0'	
                            
                            frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)

         

                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',str(time_in_standard_format))
                        frappe.db.set_value('Attendance',att.name,'working_hours',wh)
                        frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
                else:
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < ab_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent') 
                        shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                        shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        ot_hours = "00:00:00"
                        hh = check_holiday(att.attendance_date,att.employee)
                        if not hh:
                            night_shift=frappe.db.get_value("Shift Type",{'name':att.shift},['custom_night_shift'])
                            if night_shift ==1:
                                if att.attendance_date != datetime.date(att.out_time):
                                    if shift_et < out_time:
                                        difference = time_diff_in_timedelta_1(shift_et,out_time)
                                        diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                        if diff_time.hour > 3:
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
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)  
                            else:
                                if shift_et < out_time:
                                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                    if diff_time.hour > 3:
                                        if diff_time.minute >= 50:
                                            ot_hours = time(diff_time.hour-1,0,0)
                                        else:
                                            ot_hours = time(diff_time.hour-1,0,0)
                                    else:
                                        ot_hours = "00:00:00"	
                                else:
                                    ot_hours = "00:00:00"			
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr) 
                        else:   
                            in_time = att.in_time
                            out_time = att.out_time
                            if isinstance(in_time, str):
                                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                            if isinstance(out_time, str):
                                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                            if diff_time.hour > 0:
                                if diff_time.minute >= 55:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 55:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                                
                            else:
                                ot_hours = "00:00:00"			
                            frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                            if ot_hours !='00:00:00':
                                ftr = [3600,60,1]
                                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                ot_hr = round(hr/3600,1)
                            else:
                                ot_hr = '0.0'	
                            frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         


                            print(ot_hours)
                            frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                            if ot_hours !='00:00:00':
                                ftr = [3600,60,1]
                                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                ot_hr = round(hr/3600,1)
                            else:
                                ot_hr = '0.0'	
                            
                            frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)

                            
                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
            else:
                if wh > 0 :
                    if wh < 24.0:
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < ab_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')  
                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                    hh = check_holiday(att.attendance_date,att.employee)
                    shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                    out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                    shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                    ot_hours = "00:00:00"
                    if not hh:
                        
                            night_shift=frappe.db.get_value("Shift Type",{'name':att.shift},['custom_night_shift'])
                            if night_shift ==1:
                                if att.attendance_date != datetime.date(att.out_time):
                                    if shift_et < out_time:
                                        difference = time_diff_in_timedelta_1(shift_et,out_time)
                                        diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                        if diff_time.hour > 3:
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
                                if shift_et < out_time:
                                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                    if diff_time.hour > 3:
                                        if diff_time.minute >= 50:
                                            ot_hours = time(diff_time.hour-1,0,0)
                                        else:
                                            ot_hours = time(diff_time.hour-1,0,0)
                                    else:
                                        ot_hours = "00:00:00"	
                                else:
                                    ot_hours = "00:00:00"			
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
                    else:
                        in_time = att.in_time
                        out_time = att.out_time
                        if isinstance(in_time, str):
                            in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                        if isinstance(out_time, str):
                            out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                        if diff_time.hour > 0:
                            if diff_time.minute >= 55:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 55:
                                ot_hours = time(1,0,0)
                            else:
                                ot_hours = "00:00:00" 
                            
                        else:
                            ot_hours = "00:00:00"			
                        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                        if ot_hours !='00:00:00':
                            ftr = [3600,60,1]
                            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                            ot_hr = round(hr/3600,1)
                        else:
                            ot_hr = '0.0'	
                        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)        

            
                else:
                    frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                    frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
                    frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
        else:
            frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
          
        hh = check_holiday(att.attendance_date,att.employee)
        if not hh:
            if att.shift and att.in_time:
                shift_time = frappe.get_value(
                    "Shift Type", {'name': att.shift}, ["start_time"])
                shift_start_time = datetime.strptime(
                    str(shift_time), '%H:%M:%S').time()
                start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                
                if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                    # print(att.in_time - shift_start_time)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
            if att.shift and att.out_time:
                shift_time = frappe.get_value(
                    "Shift Type", {'name': att.shift}, ["end_time"])
                shift_end_time = datetime.strptime(
                    str(shift_time), '%H:%M:%S').time()
                end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                # if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                #     # frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                #     # frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', att.out_time - end_time)
                # else:
                #     # frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                #     # frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        else:
            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            # frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
            # frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',  "00:00:00")
    

@frappe.whitelist()
def get_urc_to_ec(from_date,to_date,employee):
    pin = frappe.get_value('Employee',{'name':employee},['attendance_device_id'])
    urc = frappe.db.sql("""select * from `tabUnregistered Employee Checkin` where date(biometric_time) between '%s' and '%s' and biometric_pin = '%s' """%(from_date,to_date,pin),as_dict=True)
    for uc in urc:
        pin = uc.biometric_pin
        time = uc.biometric_time
        dev = uc.location_device_id
        typ = uc.log_type
        nam = uc.name
        if time != "":
            if not frappe.db.exists('Employee Checkin',{'attendance_device_id':pin,"time":time}):
                ec = frappe.new_doc('Employee Checkin')
                ec.biometric_pin = pin
                ec.employee = frappe.db.get_value('Employee',{'attendance_device_id':pin},['name'])
                ec.time = time
                ec.device_id = dev
                ec.log_type = typ
                ec.save(ignore_permissions=True)
                frappe.db.commit()
                attendance = frappe.db.sql(""" delete from `tabUnregistered Employee Checkin` where name = '%s' """%(nam))      
    return "ok"

@frappe.whitelist()
def enqueue_get_urc_to_ec_without_employee(from_date,to_date):
    frappe.enqueue(
        method="ir.mark_attendance.get_urc_to_ec_without_employee",
        queue="long",
        is_async=True,
        job_name="Checkin Process",
        from_date = from_date,
        to_date = to_date
    )
    return 'ok'

@frappe.whitelist()
def get_urc_to_ec_without_employee(from_date,to_date):
    urc = frappe.db.sql("""select * from `tabUnregistered Employee Checkin` where date(biometric_time) between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for uc in urc:
        pin = uc.biometric_pin
        time = uc.biometric_time
        dev = uc.location_device_id
        typ = uc.log_type
        nam = uc.name
        if time != "":
            if frappe.db.exists('Employee',{'attendance_device_id':pin}):
                if not frappe.db.exists('Employee Checkin',{'attendance_device_id':pin,"time":time}):
                    ec = frappe.new_doc('Employee Checkin')
                    ec.biometric_pin = pin
                    ec.employee = frappe.db.get_value('Employee',{'attendance_device_id':pin},['name'])
                    ec.time = time
                    ec.device_id = dev
                    ec.log_type = typ
                    ec.save(ignore_permissions=True)
                    frappe.db.commit()
                    attendance = frappe.db.sql(""" delete from `tabUnregistered Employee Checkin` where name = '%s' """%(nam))      
    return "ok"


@frappe.whitelist()
def enqueue_update_att_without_employee(from_date,to_date):
    frappe.enqueue(
        method="ir.mark_attendance.update_att_without_employee",
        queue="long",
        is_async=True,
        job_name="Attendance Process",
        from_date = from_date,
        to_date = to_date
    )
    return 'ok'

@frappe.whitelist()
def mark_wh_without_employee(from_date,to_date):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
    for att in attendance:
        if att.shift and att.in_time and att.out_time :
            if att.in_time and att.out_time:
                in_time = att.in_time
                out_time = att.out_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            wh = time_diff_in_hours(out_time,in_time)
            default_shift=''
            actual_shift=frappe.db.get_value('Employee',{'name':att.employee},['custom_shift'])
            if actual_shift=='Single':
                default_shift=frappe.db.get_value('Employee',{'name':att.employee},['default_shift'])
            else:
                default_shift = frappe.db.get_value(
                    "Shift Assignment",
                    {'employee': att.employee, 'start_date': ('<=', att.attendance_date), 'end_date': ('>=', att.attendance_date), "docstatus": 1},
                    ['shift_type']
                )
            hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
            ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])
            if default_shift:
                if att.shift == default_shift:
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < ab_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            totwh=0
                            custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                            custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                            if att.custom_attendance_permission:
                                totwh=wh+custom_permission_hours
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            elif att.custom_on_duty_application:
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half':
                                    if custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    totwh=wh+custom_od_time
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        elif wh >= hd_threshold:
                            frappe.db.set_value('Attendance',att.name,'status','Present')  
                        shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                        shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        ot_hours = "00:00:00"
                        hh = check_holiday(att.attendance_date,att.employee)
                        if not hh:
                            if shift_et < out_time:
                                if att.status == "Half Day" or att.status == "Present":
                                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
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
                                    if diff_time.hour > 3:
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
                            frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                            if ot_hours !='00:00:00':
                                ftr = [3600,60,1]
                                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                ot_hr = round(hr/3600,1)
                            else:
                                ot_hr = '0.0'	
                            frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)  
                        else:
                            in_time = att.in_time
                            out_time = att.out_time
                            if isinstance(in_time, str):
                                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                            if isinstance(out_time, str):
                                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                            if diff_time.hour > 0:
                                if diff_time.minute >= 55:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 55:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                                
                            else:
                                ot_hours = "00:00:00"			
                            frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                            if ot_hours !='00:00:00':
                                ftr = [3600,60,1]
                                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                ot_hr = round(hr/3600,1)
                            else:
                                ot_hr = '0.0'	
                            frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         




                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
            else:
                if wh > 0 :
                    if wh < 24.0:
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < ab_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')  
        else:
            frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
        hh = check_holiday(att.attendance_date,att.employee)
        if not hh:
            if att.shift and att.in_time:
                shift_time = frappe.get_value(
                    "Shift Type", {'name': att.shift}, ["start_time"])
                shift_start_time = datetime.strptime(
                    str(shift_time), '%H:%M:%S').time()
                start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                
                if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            if att.shift and att.out_time:
                shift_time = frappe.get_value(
                    "Shift Type", {'name': att.shift}, ["end_time"])
                shift_end_time = datetime.strptime(
                    str(shift_time), '%H:%M:%S').time()
                end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                # if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                #     # frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                #     # frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', att.out_time - end_time)
                # else:
                #     # frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                #     # frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        else:
            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            # frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
            # frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',  "00:00:00"

def mark_cc(from_date,to_date):
    attendance = frappe.db.get_all('Attendance', filters={
        'attendance_date': ['between', (from_date, to_date)],
        'docstatus': ['!=', '2']
    }, fields=['name', 'shift', 'in_time', 'out_time', 'employee', 'custom_on_duty_application', 'employee_name', 'department', 'attendance_date', 'status'])

    for att in attendance:
        in_time1 = att.in_time
        out_time1 = att.out_time
        
        if in_time1 and out_time1:
            
            if in_time1.date() != out_time1.date():
                if att.attendance_date == in_time1.date():
                    if frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date}):
                        cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
                        for i in cc.items:
                            if i.item == "Dinner" or i.item =="Supper":
                                i.status=1
                                cc.save(ignore_permissions=True)
                                frappe.db.commit()
                    out_time1 = datetime.combine(att.attendance_date, datetime.min.time()) + timedelta(days=1)

            cc_exists = frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
            if not cc_exists:
                cc = frappe.new_doc('Canteen Coupons')
                cc.employee = att.employee
                cc.employee_name = att.employee_name
                cc.department = att.department
                cc.date = att.attendance_date
                cc.attendance = att.name

                items_to_add = []
                fm = frappe.db.sql("""SELECT * FROM `tabFood Menu` ORDER BY serial_no""", as_dict=True)
                for f in fm:
                    items_to_add.append({
                        'item': f.name,
                        'status': 0
                    })

                cc.set('items', items_to_add)
            else:
                cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})

            
            in_time = in_time1.strftime('%H:%M:%S')
            out_time = out_time1.strftime('%H:%M:%S')
            time_in = datetime.strptime(in_time, '%H:%M:%S').time()
            time_out = datetime.strptime(out_time, '%H:%M:%S').time()

            for item in cc.get('items'):
                food_menu = frappe.get_doc('Food Menu', item.get('item'))
                from_time = str(food_menu.from_time)
                st = datetime.strptime(from_time, '%H:%M:%S').time()

                if time_in <= st <= time_out:
                    item.status = 1

            cc.save(ignore_permissions=True)
            frappe.db.commit()