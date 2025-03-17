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
    # from_date = add_days(today(),-2)  
    # to_date = today()
    from_date = "2025-01-19"  
    to_date = "2025-01-19"
    dates = get_dates(from_date,to_date)
    for date in dates:
        from_date = add_days(date,0)
        to_date = date
        mark_att(from_date,to_date)
        mark_cc(from_date,to_date)
    return "ok"

@frappe.whitelist()
def mark_att_process_manual_for_one_month():
    from_date = add_days(today(),-31)  
    to_date = today()
    dates = get_dates(from_date,to_date)
    for date in dates:
        from_date = add_days(date,0)
        to_date = date
        mark_att(from_date,to_date)
        mark_cc(from_date,to_date)
    return "ok"


from ir.custom import update_ot_request
@frappe.whitelist()
def mark_att_process():
    # from_date = add_days(today(),-1)  
    # to_date = today()
    from_date="2025-01-06"
    to_date="2025-01-06"
    dates = get_dates(from_date,to_date)
    dt = []
        
        
    mark_att(from_date,to_date)
    # update_ot_request(from_date,to_date)
    # mark_cc(from_date,to_date)
    
    return "ok"

def get_dates(from_date,to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    return dates
@frappe.whitelist()
def mark_att(from_date,to_date):
    # checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee='W1191' order by time ASC """%(from_date,to_date),as_dict=True)    
    
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    # mark_absent(from_date,to_date)
    # mark_wh(from_date,to_date)
    # grace_late_time(to_date)
    ot_calculation(from_date,to_date)
    
    

def ot_calculation(from_date,to_date):
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' and docstatus =1 and employee='W1191'"""%(from_date,to_date),as_dict=True)
    for att in attendance:
        ot_hours = '00:00:00'
        if att.shift and att.out_time and att.in_time :
            hh = check_holiday(att.attendance_date,att.employee)
            if not hh:
                shift_et = frappe.db.get_value("Shift Type",{'name':att.shift},['end_time'])
                shift_st=frappe.db.get_value("Shift Type",{'name':att.shift},['start_time'])
                night_shift = frappe.db.get_value("Shift Type",{"name":att.shift},["custom_night_shift"])
                if night_shift == 1:
                    print("hi1")
                    if att.attendance_date != datetime.date(att.out_time):
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        if shift_et < out_time:
                            difference = time_diff_in_timedelta_1(shift_et,out_time)
                            diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                            if diff_time.hour > 0 <3:
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                            elif diff_time.hour > 3:
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour-1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour-1,0,0)
                            else:
                                ot_hours = "00:00:00"
                        else:
                            ot_hours = "00:00:00"
                    else:
                        ot_hours = "00:00:00"
                    # frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                    if ot_hours !='00:00:00':
                        ftr = [3600,60,1]
                        hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                        ot_hr = round(hr/3600,1)
                    else:
                        ot_hr = '0.0'	
                    frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
                else:
                    print("hi2")
                    in_time = datetime.strptime(str(att.in_time), '%Y-%m-%d %H:%M:%S')
                    out_time = datetime.strptime(str(att.out_time), '%Y-%m-%d %H:%M:%S')
                    shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                    shift_st = datetime.strptime(str(shift_st), '%H:%M:%S').time()

                    total_working_hours = (out_time - in_time).total_seconds() / 3600  

                    if total_working_hours > 8 and out_time.date() != in_time.date():
                        shift_end_datetime = datetime.combine(in_time.date(), shift_et)

                        if shift_end_datetime < out_time:
                            
                            overtime_duration = out_time - shift_end_datetime
                            overtime_seconds = overtime_duration.total_seconds()

                            ot_hours = int(overtime_seconds // 3600)  # Get hours
                            ot_minutes = int((overtime_seconds % 3600) // 60)  # Get minutes
                            ot_seconds = int(overtime_seconds % 60)  # Get seconds

                            ot_time_str = f"{ot_hours:02}:{ot_minutes:02}:{ot_seconds:02}"
                            ot_time = datetime.strptime(ot_time_str, "%H:%M:%S").time()
                            ot_decimal = round(overtime_seconds / 3600, 1)
                            
                            if ot_time.hour > 0:
                                if ot_time.minute >= 60:
                                    ot_hours = time(ot_time.hour+1,0,0)
                                else:
                                    ot_hours = time(ot_time.hour,0,0)
                            elif ot_time.hour == 0:
                                if ot_time.minute >= 60:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                                
                            else:
                                ot_hours = "00:00:00"
                            print(ot_hours)
                            frappe.db.set_value("Attendance", att.name, "custom_ot_hours", ot_hours)

                            frappe.db.set_value("Attendance", att.name, "custom_over_time_hours", ot_decimal)
                        else:
                            frappe.db.set_value("Attendance", att.name, "custom_ot_hours", "00:00:00")
                            frappe.db.set_value("Attendance", att.name, "custom_over_time_hours", 0.0)
                            print("No Overtime")
                    else:
                        frappe.db.set_value("Attendance", att.name, "custom_ot_hours", "00:00:00")
                        frappe.db.set_value("Attendance", att.name, "custom_over_time_hours", 0.0)
                        print("No Overtime")
            else:
                print("hi3")
                in_time = att.in_time
                out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                if isinstance(shift_in_time, timedelta):
                    shift_in_time = (datetime.min + shift_in_time).time()
                if in_time.time()<shift_in_time:
                    in_time = datetime.combine(in_time.date(), shift_in_time)
                else:
                    in_time = in_time
                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                if diff_time.hour > 0:
                    if diff_time.minute >= 60:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 60:
                        ot_hours = time(1,0,0)
                    else:
                        ot_hours = "00:00:00" 
                    
                else:
                    ot_hours = "00:00:00"
                # frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                if ot_hours !='00:00:00':
                    ftr = [3600,60,1]
                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                    ot_hr = round(hr/3600,1)
                else:
                    ot_hr = '0.0'	
                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)  
        
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
        
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "05:00:00" and "22:00:00" order by time ASC"""%(employee,att_date),as_dict=True)
        employement_type = frappe.db.get_value("Employee",{"name":employee},["employment_type"])
        if not employement_type =="Agency":
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
                value = frappe.db.get_value("Special Occassions",{"date":att_date},["shift"])
                shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
                shift_start_time = frappe.db.get_value('Shift Type',{'name':shift_assignment},['custom_checkin_start_time','custom_checkin_end_time'])
                if shift_assignment and shift_start_time:
                    
                    # shift_start_time = datetime.min + shift_start_time 
                    if (datetime.min + shift_start_time[0]).time() < checkins[0].time.time() < (datetime.min + shift_start_time[1]).time():
                        shift = shift_assignment
                    else:
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
                        elif value:
                            shift = value
                        
                        else:
                            shift = ''
                else:
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
                    elif value:
                        shift = value
                    
                    else:
                        shift = ''
        else:
            shift1 = frappe.db.get_value('Shift Type',{'name':'1'},['custom_checkin_start_time','custom_checkin_end_time'])
            shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkin_start_time','custom_checkin_end_time'])
            shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkin_start_time','custom_checkin_end_time'])
            shift4 = frappe.db.get_value('Shift Type',{'name':'4'},['custom_checkin_start_time','custom_checkin_end_time'])
            shiftG = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkin_start_time','custom_checkin_end_time'])
            value = frappe.db.get_value("Special Occassions",{"date":att_date},["shift"])
            shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
            shift_start_time = frappe.db.get_value('Shift Type',{'name':shift_assignment},['custom_checkin_start_time','custom_checkin_end_time'])
            if shift_assignment and shift_start_time:
                shift_start_time = datetime.min + shift_start_time 
                if (datetime.min + shift_start_time[0]).time() < checkins[0].time.time() < (datetime.min + shift_start_time[1]).time():
                    shift = shift_assignment
                else:
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
                    elif value:
                        shift = value
                    
                    else:
                        shift = ''
            else:
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
                elif value:
                    shift = value
                
                else:
                    shift = ''
        att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "05:00:00" and "22:00:00" order by time ASC"""%(employee,att_date),as_dict=True)
        if not att and checkins:
            shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
            att = frappe.new_doc("Attendance")
            att.employee = employee
            att.attendance_date = att_date
            att.shift = shift
            att.custom_assigned_shift = shift_assignment
            att.status = 'Absent'
            att.in_time = checkins[0].time
            att.custom_total_working_hours = "00:00:00"
            att.custom_ot_hours = "00:00:00"
            att.custom_late_entry_time = "00:00:00"
            att.custom_extra_hours_total = "00:00:00"
            att.custom_early_out_time = "00:00:00"
            att.working_hours = "0.0"
            att.save(ignore_permissions=True)
            frappe.db.commit()
            for c in checkins:
                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
        else:
            shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
            att = frappe.get_doc("Attendance",att)
            if att.docstatus == 0:
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.custom_assigned_shift = shift_assignment
                # att.status = 'Absent'
                if att.custom_regularize_marked == 0:
                    att.in_time = checkins[0].time
                else:
                    if  frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"in_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"in_time":1}):  
                        att.in_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize},["corrected_in"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize},["corrected_in"])
                    else:
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
        max_out = datetime.strptime('10:30','%H:%M').time()
        in_time = frappe.db.get_value("Attendance",{"employee":employee,"attendance_date":att_date},["in_time"])
        if att_time < max_out:
            
            if in_time and in_time.time() < max_out and att_time > in_time.time():
                checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time)<'%s' order by time ASC "%(employee,att_date,max_out),as_dict=True)
                att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
                if att:
                    att = frappe.get_doc("Attendance",att)
                    if att.docstatus == 0:
                        if not att.shift:
                            if len(checkins) > 0:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                  
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[-1].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                    else:
                                        att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[0].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                    else:
                                        att.out_time = checkins[0].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        else:
                            if len(checkins) > 0:
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[-1].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"]):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                    else:
                                        att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[-1].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
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
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                        for c in checkins:
                            frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                    else:
                        att.out_time = checkins[-1].time
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                        frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    return att
            else:
                yesterday = add_days(att_date,-1)
                checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time)<'%s' order by time ASC "%(employee,att_date,max_out),as_dict=True)
                att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':yesterday,"docstatus":("!=",2)})
                if att:
                    att = frappe.get_doc("Attendance",att)
                    if att.docstatus == 0:
                        if not att.shift:
                            if len(checkins) > 0:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[-1].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                    else:
                                        att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[0].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                    else:
                                        att.out_time = checkins[0].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        else:
                            if len(checkins) > 0:
                                
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[-1].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                    else:
                                        att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                        
                                if att.custom_regularize_marked == 0:
                                    att.out_time = checkins[-1].time
                                else:
                                    if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                        att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
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
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                        for c in checkins:
                            frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                    else:
                        att.out_time = checkins[-1].time
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
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
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                            if att.custom_regularize_marked == 0:
                                att.out_time = checkins[-1].time
                            else:
                                if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                    att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                else:
                                    att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            if not att.shift:
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                            if att.custom_regularize_marked == 0:
                                att.out_time = checkins[0].time
                            else:
                                if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                    att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                else:
                                    att.out_time = checkins[0].time
                            frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    else:
                        if len(checkins) > 0:
                            if att.custom_regularize_marked == 0:
                                att.out_time = checkins[-1].time
                            else:
                                if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                    att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                else:
                                    att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            if att.custom_regularize_marked == 0:
                                att.out_time = checkins[0].time
                            else:
                                if frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1}) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1}):
                                    att.out_time = frappe.db.get_value("Attendance Regularize",{"name":att.custom_attendance_regularize,"out_time":1},["corrected_out"]) or frappe.db.get_value("Regularize",{"name":att.custom_regularize,"out_time":1},["corrected_out"])
                                else:
                                    att.out_time = checkins[0].time
                            frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    # att.status = 'Absent'    
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
            else:
                shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
                att = frappe.new_doc("Attendance")
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.custom_assigned_shift = shift_assignment
                att.status = 'Absent'
                att.custom_ot_hours = "00:00:00"
                att.custom_extra_hours_total = "00:00:00"
                if len(checkins) > 0:
                    if not att.shift:
                        att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                    att.out_time = checkins[-1].time
                    for c in checkins:
                        frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                else:
                    if not att.shift:
                        att.shift = get_actual_shift(get_time(checkins[-1].time),att_date)
                    att.out_time = checkins[0].time
                    frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                att.save(ignore_permissions=True)
                frappe.db.commit()

def time_diff_in_timedelta(in_time, out_time):
    datetime_format = "%H:%M:%S"
    if out_time and in_time :
        return out_time - in_time

def get_actual_shift(get_shift_time,employee,att_date):
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
        value = frappe.db.get_value("Special Occassions",{"date":att_date},["shift"])
        shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
        shift_start_time = frappe.db.get_value('Shift Type',{'name':shift_assignment},['custom_checkin_start_time','custom_checkin_end_time'])
        if shift_assignment and shift_start_time:
            shift_start_time = datetime.min + shift_start_time 
            if (datetime.min + shift_start_time[0]).time() < get_shift_time < (datetime.min + shift_start_time[1]).time():
                shift = shift_assignment
            else:
                if (datetime.min + shift1[0]).time() < get_shift_time < (datetime.min + shift1[0]).time():
                    shift = '1'
                elif (datetime.min + shift2[0]).time() < get_shift_time < (datetime.min + shift2[0]).time():
                    shift = '2'
                elif (datetime.min + shift3[0]).time() < get_shift_time < (datetime.min + shift3[0]).time():
                    shift ='3'
                elif (datetime.min + shift4[0]).time() < get_shift_time < (datetime.min + shift4[0]).time():
                    shift ='4'
                elif (datetime.min + shiftG[0]).time() < get_shift_time < (datetime.min + shiftG[0]).time():
                    shift ='G'
                elif value:
                    shift = '5'
                else:
                    shift = ''

        else:
            if (datetime.min + shift1[0]).time() < get_shift_time < (datetime.min + shift1[0]).time():
                shift = '1'
            elif (datetime.min + shift2[0]).time() < get_shift_time < (datetime.min + shift2[0]).time():
                shift = '2'
            elif (datetime.min + shift3[0]).time() < get_shift_time < (datetime.min + shift3[0]).time():
                shift ='3'
            elif (datetime.min + shift4[0]).time() < get_shift_time < (datetime.min + shift4[0]).time():
                shift ='4'
            elif (datetime.min + shiftG[0]).time() < get_shift_time < (datetime.min + shiftG[0]).time():
                shift ='G'
            elif value:
                shift = '5'
            else:
                shift = ''

    return shift


def mark_wh(from_date,to_date):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),"employee":"W1191"},['*'])
    for att in attendance:
        employement_type = frappe.db.get_value("Employee",{"name":att.employee},["employment_type"])
        if not employement_type == "Agency":
            if att.shift and att.in_time and att.out_time :
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
                if isinstance(shift_start_time_str, timedelta):
                    shift_start_time = (datetime.min + shift_start_time_str).time()
                elif isinstance(shift_start_time_str, str):
                    shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
                else:
                    shift_start_time = shift_start_time_str
                if in_time.time() < shift_start_time :
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    in_time = in_time
                
                # shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
                # shift_end_time = (datetime.min + shift_end_time_str).time()

                # if att.shift == "1":
                #     if out_time.time() > shift_end_time:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                #     else:
                #         out_time = out_time

                # elif att.shift == "G":
                #     if out_time.date().weekday() == 5 or out_time.date().weekday() == 6:
                #         reduced_end_time = (datetime.combine(out_time.date(), shift_end_time) - timedelta(minutes=30)).time()
                #         if out_time.time() > reduced_end_time:
                #             out_time = datetime.combine(out_time.date(), reduced_end_time)
                #         else:
                #             out_time = out_time
                #     else:
                        
                #         if out_time.time() > shift_end_time:
                #             out_time = datetime.combine(out_time.date(), shift_end_time)
                #         else:
                #             out_time = out_time

                # elif att.shift == "2":
                #     if out_time.time() <= time(23, 59, 59):
                #         out_time = out_time
                #     elif time(0, 0, 0) <= out_time.time() <= time(0, 59, 59):
                #         out_time = out_time
                #     else:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)

                wh = time_diff_in_hours(out_time,in_time)
                if wh:
                    wh = round(wh,1)
                default_shift=''
                actual_shift=frappe.db.get_value('Employee',{'name':att.employee},['custom_shift'])
                if actual_shift=='Single':
                    default_shift=frappe.db.get_value('Employee',{'name':att.employee},['default_shift'])
                else:
                    default_shift = frappe.db.get_value(
                        "Shift Assignment",
                        {'employee': att.employee, 'start_date': ('<=', att.attendance_date), 'end_date': ('>=', att.attendance_date)},
                        ['shift_type']
                    )
                
                    
                hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
                
                ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])    
                hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                date = check_holiday(att.attendance_date,att.employee)
                if att.shift =="G":
                    if hh == "WW" or date == "WW":
                        hd_threshold = hd_threshold - 0.5
                        ab_threshold = ab_threshold-0.25
                    else:
                        hd_threshold = hd_threshold
                        ab_threshold = ab_threshold
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
                if default_shift:
                    if default_shift == att.shift:
                        
                        if wh > 0 :
                            if wh < 24.0:
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                            else:
                                wh = 24.0
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                                frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                            if wh < ab_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    print(att.custom_on_duty_application)
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                        print(od_ses)
                                        if att.custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time
                                        totwh=wh+custom_od_time
                                        print(totwh)
                                        
                                        if totwh >= hd_threshold:
                                            if att.custom_attendance_permission:
                                                if att.shift=="3":
                                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                                            frappe.db.set_value('Attendance', att.name, 'status', 'Present')
                                        

                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                           
                                            frappe.db.set_value('Attendance', att.name, 'status', 'Half Day')
                                        else:
                                            frappe.db.set_value('Attendance', att.name, 'status', 'Absent')
                                    else:
                                
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                            elif wh >= hd_threshold:
                        

                                frappe.db.set_value('Attendance',att.name,'status','Present')
                            elif wh >= ab_threshold and wh < hd_threshold:
                                totwh=0
                                custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                                custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                                if att.custom_attendance_permission:
                                    totwh=round(wh,1)+custom_permission_hours
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                        if att.custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance', att.name, 'status', 'Present')
                                        if att.custom_attendance_permission:
                                            if att.shift=="3":
                                                frappe.db.set_value('Attendance',att.name,'shift','2')
                                
                                    elif totwh >= ab_threshold and totwh < hd_threshold:
                                        frappe.db.set_value('Attendance', att.name, 'status', 'Half Day')
                            
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
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                                if att.custom_attendance_permission:
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                            elif wh >= ab_threshold and wh < hd_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                                if att.custom_attendance_permission:
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                            elif wh >= hd_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                                if att.custom_attendance_permission:
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')  
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
                                if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
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
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
            else:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        else:
            if att.shift and att.in_time and att.out_time :
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
                if isinstance(shift_start_time_str, timedelta):
                    shift_start_time = (datetime.min + shift_start_time_str).time()
                elif isinstance(shift_start_time_str, str):
                    shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
                else:
                    shift_start_time = shift_start_time_str
                if in_time.time() < shift_start_time:
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    if att.in_time - dt.datetime.combine(att.attendance_date,shift_start_time)<timedelta(minutes=1):
                        in_time = datetime.combine(in_time.date(), shift_start_time)
                    else:
                        in_time = in_time
                
                # shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
                # shift_end_time = (datetime.min + shift_end_time_str).time()

                # if att.shift == "1":
                #     if out_time.time() > shift_end_time:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                #     else:
                #         out_time = out_time

                # elif att.shift == "G":
                #     if out_time.date().weekday() == 5 or out_time.date().weekday() == 6:
                #         reduced_end_time = (datetime.combine(out_time.date(), shift_end_time) - timedelta(minutes=30)).time()
                #         if out_time.time() > reduced_end_time:
                #             out_time = datetime.combine(out_time.date(), reduced_end_time)
                #         else:
                #             out_time = out_time
                #     else:
                        
                #         if out_time.time() > shift_end_time:
                #             out_time = datetime.combine(out_time.date(), shift_end_time)
                #         else:
                #             out_time = out_time

                # elif att.shift == "2":
                #     if out_time.time() <= time(23, 59, 59):
                #         out_time = out_time
                #     elif time(0, 0, 0) <= out_time.time() <= time(0, 59, 59):
                #         out_time = out_time
                #     else:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)

                wh = time_diff_in_hours(out_time,in_time)
                if wh:
                    wh = round(wh,1)
                hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
                ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])
                hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                date = check_holiday(att.attendance_date,att.employee)
                if att.shift =="G":
                    if hh == "WW" or date == "WW":
                        hd_threshold = hd_threshold - 0.5
                        ab_threshold = ab_threshold - 0.25
                    else:
                        hd_threshold = hd_threshold
                        ab_threshold = ab_threshold
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
                    
                if wh > 0 :
                    if wh < 24.0:
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        
                        frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59") 
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < ab_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift == "3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        elif att.custom_on_duty_application:
                            
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                    if att.custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                        
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day') 
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent') 
                                    else:
                                        custom_od_time = att.custom_od_time
                                        totwh=wh+custom_od_time
                                        print(totwh)
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                                
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        totwh=0
                        custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                        custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                        if att.custom_attendance_permission:
                            totwh=round(wh,1)+custom_permission_hours
                            if totwh >= hd_threshold:
                                frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift=="3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        elif att.custom_on_duty_application:
                        
                            od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                            if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                if custom_od_time==0.0:
                                    from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                    to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                    custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                    frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                else:
                                    custom_od_time = att.custom_od_time
                                totwh=wh+custom_od_time
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Present')
                        
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
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                    if diff_time.hour > 0 <3:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(diff_time.hour+1,0,0)
                                        else:
                                            ot_hours = time(diff_time.hour,0,0)
                                    elif diff_time.hour == 0:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(1,0,0)
                                        else:
                                            ot_hours = "00:00:00" 
                                    if diff_time.hour > 3:
                                        if diff_time.minute >= 60:
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
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(1,0,0)
                                    else:
                                        ot_hours = "00:00:00" 
                                elif diff_time.hour > 3:
                                    if diff_time.minute >= 60:
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
                        
                        shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                        if isinstance(shift_in_time, timedelta):
                            shift_in_time = (datetime.min + shift_in_time).time()
                        if in_time.time()<shift_in_time:
                            in_time = datetime.combine(in_time.date(), shift_in_time)
                        else:
                            in_time = in_time
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                        if diff_time.hour > 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
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


                    
                        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                        if ot_hours !='00:00:00':
                            ftr = [3600,60,1]
                            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                            ot_hr = round(hr/3600,1)
                        else:
                            ot_hr = '0.0'	
                        
                        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
                        
                hh = check_holiday(att.attendance_date,att.employee)
                if not hh:
                    if att.shift and att.in_time:
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["start_time"])
                        shift_start_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                        
                        if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                            if att.in_time - start_time > timedelta(minutes=1):
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    
                    if att.shift and att.out_time:
                        if att.shift =='1':
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        elif att.shift =='G':
                            hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                            date = check_holiday(att.attendance_date,att.employee)
                            if hh == "WW" or date == "WW":
                                shift_time = frappe.get_value(
                                    "Shift Type", {'name': att.shift}, ["end_time"])
                                shift_end_time = datetime.strptime(
                                    str(shift_time), '%H:%M:%S').time()
                                end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                                end_time = end_time_30 - timedelta(minutes=30)
                                if att.out_time < end_time:
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                                else:
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                            else:
                                shift_time = frappe.get_value(
                                    "Shift Type", {'name': att.shift}, ["end_time"])
                                shift_end_time = datetime.strptime(
                                    str(shift_time), '%H:%M:%S').time()
                                end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                                if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                                else:
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        elif att.shift == '2' or att.shift == '8 to 8':
                            shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                            shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                            if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                                shift_end_datetime += timedelta(days=1)

                            if att.out_time < shift_end_datetime:
                                early_out_duration = shift_end_datetime - att.out_time
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                else:
                    if att.shift and att.in_time:
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["start_time"])
                        shift_start_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                        
                        if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                            if att.in_time - start_time > timedelta(minutes=1):
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    
                    if att.shift and att.out_time:
                        if att.shift =='1':
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        elif att.shift =='G':
                            hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                            date = check_holiday(att.attendance_date,att.employee)
                            if hh == "WW" or date == "WW":
                                shift_time = frappe.get_value(
                                    "Shift Type", {'name': att.shift}, ["end_time"])
                                shift_end_time = datetime.strptime(
                                    str(shift_time), '%H:%M:%S').time()
                                end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                                end_time = end_time_30 - timedelta(minutes=30)
                                if att.out_time < end_time:
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                                else:
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                            else:
                                shift_time = frappe.get_value(
                                    "Shift Type", {'name': att.shift}, ["end_time"])
                                shift_end_time = datetime.strptime(
                                    str(shift_time), '%H:%M:%S').time()
                                end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                                if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                                else:
                                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        elif att.shift == '2' or att.shift == '8 to 8':
                            shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                            shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                            if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                                shift_end_datetime += timedelta(days=1)

                            if att.out_time < shift_end_datetime:
                                early_out_duration = shift_end_datetime - att.out_time
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
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


    

# @frappe.whitelist()
# def update_late_deduction(employee,attendance_date):
#     # employee='HR-EMP-00002'
#     # attendance_date='2024-05-27'
#     month_start = get_first_day(attendance_date)
#     attendance = frappe.db.sql("""select * from `tabAttendance` where employee ='%s' and attendance_date between '%s' and '%s' and docstatus!=2"""%(employee,month_start,attendance_date),as_dict=True)
#     late=0
#     late_min=0
#     for att in attendance:
#         if att.in_time and att.shift:
#             shift_st = frappe.db.get_value("Shift Type",{'name':att.shift},['start_time'])
#             in_time = datetime.strptime(str(att.in_time),'%Y-%m-%d %H:%M:%S').time()
#             shift_st = datetime.strptime(str(shift_st), '%H:%M:%S').time()
#             if shift_st < in_time:
#                 difference = time_diff_in_timedelta_1(shift_st,in_time)
#                 diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                
#                 late_min +=diff_time.minute
#                 frappe.db.set_value("Attendance",att.name,'custom_late',difference)
#                 if diff_time.minute > 0:
#                     late+=1
#                     if diff_time.minute >= 15 and late ==1:
#                         pass
#                     if diff_time.minute>=15 and late ==2:
#                         if late_min>=30:
#                             if att.late_entry==0:
#                                 emp=frappe.get_value("Employee",{"name":att.employee},['user_id'])
#                                 # frappe.sendmail(
#                                 #     recipients=[emp],
#                                 #     subject=_("Warning - Late Entry"),
#                                 #     message="""
#                                 #         Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
#                                 #         """%(att.employee)
#                                 # )
#                                 frappe.db.set_value("Attendance",att.name,'late_entry',1)
#                     if att.late_entry==0:
#                         if late>2 and late<4:
#                             if not att.custom_late:
#                                 emp=frappe.get_value("Employee",{"name":att.employee},['user_id'])
#                                 # frappe.sendmail(
#                                 #     recipients=[emp],
#                                 #     subject=_("Warning - Late Entry"),
#                                 #     message="""
#                                 #         Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
#                                 #         """%(att.employee)
#                                 # )
#                         elif late==5 or (late > 5 and (late - 5) % 3 == 0):
#                             if not frappe.db.exists("Leave Ledger Entry",{'docstatus':1,'employee':att.employee,'from_date':month_start,'to_date':attendance_date}):
#                                 ad = frappe.new_doc('Leave Ledger Entry')
#                                 ad.employee = att.employee
#                                 ad.employee_name = att.employee_name
#                                 ad.from_date = month_start
#                                 ad.to_date = attendance_date
#                                 el = frappe.db.sql("""
#                                     SELECT sum(leaves) 
#                                     FROM `tabLeave Ledger Entry` 
#                                     WHERE employee = %s 
#                                     AND leave_type = 'Earned Leave'
#                                     AND docstatus = 1
#                                 """, (att.employee))[0][0]
#                                 cl = frappe.db.sql("""
#                                     SELECT sum(leaves) 
#                                     FROM `tabLeave Ledger Entry` 
#                                     WHERE employee = %s 
#                                     AND leave_type = 'Casual Leave'
#                                     AND docstatus = 1
#                                 """, (att.employee))[0][0]
#                                 if el:
#                                     if el>0:
#                                         ad.leave_type = 'Earned Leave'
#                                 elif cl:
#                                     if cl>0:
#                                         ad.leave_type = 'Casual Leave'
#                                 else:
#                                     ad.leave_type = 'Leave without Pay'
#                                 ad.leaves =  -0.5
#                                 ad.save(ignore_permissions=1)
#                                 ad.submit()
#                                 frappe.db.commit()
#                     elif late>2 and late<5:
#                         if not att.custom_late:
#                             emp=frappe.get_value("Employee",{"name":att.employee},['user_id'])
#                             # frappe.sendmail(
#                             #     recipients=[emp],
#                             #     subject=_("Warning - Late Entry"),
#                             #     message="""
#                             #         Dear %s,<br> Already you have taken your two times 15 minutes grace time per month. If you have marked as another late, Half Day will be Deducted from your Leave Balance <br><br>Thanks & Regards,<br>IRINDIA<br>"This email has been automatically generated. Please do not reply"
#                             #         """%(att.employee)
#                             # )
#                     elif late==5 or (late > 5 and (late - 5) % 3 == 0):
#                         if not frappe.db.exists("Leave Ledger Entry",{'docstatus':1,'employee':att.employee,'from_date':month_start,'to_date':attendance_date}):
#                             ad = frappe.new_doc('Leave Ledger Entry')
#                             ad.employee = att.employee
#                             ad.employee_name = att.employee_name
#                             ad.from_date = month_start
#                             ad.to_date = attendance_date
#                             el = frappe.db.sql("""
#                                 SELECT sum(leaves) 
#                                 FROM `tabLeave Ledger Entry` 
#                                 WHERE employee = %s 
#                                 AND leave_type = 'Earned Leave'
#                                 AND docstatus = 1
#                             """, (att.employee))[0][0]
#                             cl = frappe.db.sql("""
#                                 SELECT sum(leaves) 
#                                 FROM `tabLeave Ledger Entry` 
#                                 WHERE employee = %s 
#                                 AND leave_type = 'Casual Leave'
#                                 AND docstatus = 1
#                             """, (att.employee))[0][0]
#                             if el:
#                                 if el>0:
#                                     ad.leave_type = 'Earned Leave'
#                             elif cl:
#                                 if cl>0:
#                                     ad.leave_type = 'Casual Leave'
#                             else:
#                                 ad.leave_type = 'Leave without Pay'
#                             ad.leaves = -0.5
#                             ad.save(ignore_permissions=1)
#                             ad.submit()
#                             frappe.db.commit()
#             else:
#                 frappe.db.set_value("Attendance",att.name,'custom_late_entry_time',"00:00:00")
#         else:
#             if att.status=='Absent' and not att.in_time and not att.shift:
#                 frappe.db.set_value("Attendance",att.name,'custom_late_entry_time',"00:00:00")


@frappe.whitelist()
def update_att_without_employee(from_date,to_date):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time  """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            mark_attendance_from_checkin(c.employee,c.time,c.log_type)
    # mark_absent(from_date,to_date)
    mark_wh_without_employee(from_date,to_date)
    grace_late_time(to_date)
    ot_calculation(from_date,to_date)
    update_ot_request(from_date,to_date)
    return "ok"

@frappe.whitelist()
def enqueue_update_att_with_employee(from_date,to_date,employee):
    frappe.enqueue(
        method="ir.mark_attendance.update_att_with_employee",
        queue="long",
        is_async=True,
        job_name="Attendance Process" + '' +employee,
        from_date = from_date,
        to_date = to_date,
        employee = employee
    )
    return 'ok'

@frappe.whitelist()
def update_att_with_employee(from_date,to_date,employee):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee='%s' order by time ASC """%(from_date,to_date,employee),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    # mark_absents(from_date,to_date,employee)
    mark_whs(from_date,to_date,employee)
    grace_late_time(to_date)
    ot_calculation_for_employee(from_date,to_date,employee)
    update_ot_request(from_date,to_date)
    return "ok"


@frappe.whitelist()
def update_on_duty(from_date,to_date,employee):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee='%s' order by time ASC """%(from_date,to_date,employee),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    # mark_absents(from_date,to_date,employee)
    mark_whs(from_date,to_date,employee)
    
    ot_calculation_for_employee(from_date,to_date,employee)
    update_ot_request(from_date,to_date)
    return "ok"

@frappe.whitelist()
def update_att_with_employee_regularize(from_date,to_date,employee):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee='%s' order by time ASC """%(from_date,to_date,employee),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    # mark_absents(from_date,to_date,employee)
    mark_whs(from_date,to_date,employee)
    # grace_late_time(to_date)
    ot_calculation_for_employee(from_date,to_date,employee)
    update_ot_request(from_date,to_date)
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
    grace_late_time(to_date)
    ot_calculation_for_department(from_date,to_date,department)
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
    grace_late_time(to_date)
    ot_calculation_for_department_employee(from_date,to_date,department,name)
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

from frappe.utils import add_days, formatdate

@frappe.whitelist()
def mark_whs(from_date,to_date,employee):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'employee':employee},['*'])
    for att in attendance:
        att.custom_ot_hours = "00:00:00"
        att.custom_extra_hours_total ="00:00:00"
        employment_type = frappe.db.get_value("Employee",{"name":att.employee},["employment_type"])
        if not employment_type == "Agency":
            if att.shift and att.in_time and att.out_time :
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
                if isinstance(shift_start_time_str, timedelta):
                    shift_start_time = (datetime.min + shift_start_time_str).time()
                elif isinstance(shift_start_time_str, str):
                    shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
                else:
                    shift_start_time = shift_start_time_str
                if in_time.time() < shift_start_time:
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    if att.in_time - dt.datetime.combine(att.attendance_date,shift_start_time)<timedelta(minutes=1):
                        in_time = datetime.combine(in_time.date(), shift_start_time)
                    else:
                        in_time = in_time
                
                # shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
                # shift_end_time = (datetime.min + shift_end_time_str).time()

                # if att.shift == "1":
                #     if out_time.time() > shift_end_time:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                #     else:
                #         out_time = out_time

                # elif att.shift == "G":
                #     if out_time.date().weekday() == 5 or out_time.date().weekday() == 6:
                #         reduced_end_time = (datetime.combine(out_time.date(), shift_end_time) - timedelta(minutes=30)).time()
                #         if out_time.time() > reduced_end_time:
                #             out_time = datetime.combine(out_time.date(), reduced_end_time)
                #         else:
                #             out_time = out_time
                #     else:
                        
                #         if out_time.time() > shift_end_time:
                #             out_time = datetime.combine(out_time.date(), shift_end_time)
                #         else:
                #             out_time = out_time

                # elif att.shift == "2":
                #     if out_time.time() <= time(23, 59, 59):
                #         out_time = out_time
                #     elif time(0, 0, 0) <= out_time.time() <= time(0, 59, 59):
                #         out_time = out_time
                #     else:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                
                wh = time_diff_in_hours(out_time,in_time)
                if wh:
                    wh = round(wh,1)
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
                hh = check_holiday(add_days(att.attendance_date,1),employee)
                date = check_holiday(att.attendance_date,employee)
                if att.shift =="G":
                    if hh == "WW" or date == "WW":
                        hd_threshold = hd_threshold - 0.5
                        ab_threshold = ab_threshold - 0.25
                    else:
                        hd_threshold = hd_threshold
                        ab_threshold = ab_threshold
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
                
                if default_shift:
                    if att.shift == default_shift:
                        if wh > 0 :
                            if wh < 24.0:
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                
                                frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                            else:
                                wh = 24.0
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59") 
                                frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                            if wh < ab_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    
                                        od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                        if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                            if att.custom_od_time==0.0:
                                                from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                                to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                                custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                                frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                            
                                                totwh=wh+custom_od_time
                                                if totwh >= hd_threshold:
                                                
                                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                                elif totwh >= ab_threshold and totwh < hd_threshold:
                                                    frappe.db.set_value('Attendance',att.name,'status','Half Day') 
                                                else:
                                                    frappe.db.set_value('Attendance',att.name,'status','Absent') 
                                            else:
                                                custom_od_time = att.custom_od_time
                                                totwh=wh+custom_od_time
                                                print(totwh)
                                                if totwh >= hd_threshold:
                                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                                elif totwh >= ab_threshold and totwh < hd_threshold:
                                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                                else:
                                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                                        else:
                                        
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                            elif wh >= ab_threshold and wh < hd_threshold:
                                totwh=0
                                custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                                custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                                if att.custom_attendance_permission:
                                    totwh=round(wh,1)+custom_permission_hours
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                        if custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time
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
                                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                            if diff_time.hour > 0 <3:
                                                if diff_time.minute >= 60:
                                                    ot_hours = time(diff_time.hour+1,0,0)
                                                else:
                                                    ot_hours = time(diff_time.hour,0,0)
                                            elif diff_time.hour == 0:
                                                if diff_time.minute >= 60:
                                                    ot_hours = time(1,0,0)
                                                else:
                                                    ot_hours = "00:00:00" 
                                            if diff_time.hour > 3:
                                                if diff_time.minute >= 60:
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
                                            if diff_time.minute >= 60:
                                                ot_hours = time(diff_time.hour+1,0,0)
                                            else:
                                                ot_hours = time(diff_time.hour,0,0)
                                        elif diff_time.hour == 0:
                                            if diff_time.minute >= 60:
                                                ot_hours = time(1,0,0)
                                            else:
                                                ot_hours = "00:00:00" 
                                        elif diff_time.hour > 3:
                                            if diff_time.minute >= 60:
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
                                
                                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                                if isinstance(shift_in_time, timedelta):
                                    shift_in_time = (datetime.min + shift_in_time).time()
                                if in_time.time()<shift_in_time:
                                    in_time = datetime.combine(in_time.date(), shift_in_time)
                                else:
                                    in_time = in_time
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                if diff_time.hour > 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
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


                            
                                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                                if ot_hours !='00:00:00':
                                    ftr = [3600,60,1]
                                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                                    ot_hr = round(hr/3600,1)
                                else:
                                    ot_hr = '0.0'	
                                
                                frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)

            

                        else:
                            # frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',str(time_in_standard_format))
                            # frappe.db.set_value('Attendance',att.name,'working_hours',wh)
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
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                            elif wh >= ab_threshold and wh < hd_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                            elif wh >= hd_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
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
                                                if diff_time.minute >= 60:
                                                    ot_hours = time(diff_time.hour+1,0,0)
                                                else:
                                                    ot_hours = time(diff_time.hour,0,0)
                                            elif diff_time.hour == 0:
                                                if diff_time.minute >= 60:
                                                    ot_hours = time(1,0,0)
                                                else:
                                                    ot_hours = "00:00:00" 
                                            if diff_time.hour > 3:
                                                if diff_time.minute >= 60:
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
                                            if diff_time.minute >= 60:
                                                ot_hours = time(diff_time.hour+1,0,0)
                                            else:
                                                ot_hours = time(diff_time.hour,0,0)
                                        elif diff_time.hour == 0:
                                            if diff_time.minute >= 60:
                                                ot_hours = time(1,0,0)
                                            else:
                                                ot_hours = "00:00:00" 
                                        if diff_time.hour > 3:
                                            if diff_time.minute >= 60:
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
                                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                                if isinstance(shift_in_time, timedelta):
                                    shift_in_time = (datetime.min + shift_in_time).time()
                                if in_time.time()<shift_in_time:
                                    in_time = datetime.combine(in_time.date(), shift_in_time)
                                else:
                                    in_time = in_time
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                if diff_time.hour > 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
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
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
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
                                                if diff_time.minute >=60:
                                                    ot_hours = time(diff_time.hour+1,0,0)
                                                else:
                                                    ot_hours = time(diff_time.hour,0,0)
                                            elif diff_time.hour == 0:
                                                if diff_time.minute >= 60:
                                                    ot_hours = time(1,0,0)
                                                else:
                                                    ot_hours = "00:00:00" 
                                            if diff_time.hour > 3:
                                                if diff_time.minute >= 60:
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
                                            if diff_time.minute >=60:
                                                ot_hours = time(diff_time.hour+1,0,0)
                                            else:
                                                ot_hours = time(diff_time.hour,0,0)
                                        elif diff_time.hour == 0:
                                            if diff_time.minute >= 60:
                                                ot_hours = time(1,0,0)
                                            else:
                                                ot_hours = "00:00:00" 
                                        if diff_time.hour > 3:
                                            if diff_time.minute >= 60:
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
                            shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                            if isinstance(shift_in_time, timedelta):
                                shift_in_time = (datetime.min + shift_in_time).time()
                            if in_time.time()<shift_in_time:
                                in_time = datetime.combine(in_time.date(), shift_in_time)
                            else:
                                in_time = in_time
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                            
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                            if diff_time.hour > 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
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
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
            else:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        
        else:
            if att.shift and att.in_time and att.out_time :
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
                if isinstance(shift_start_time_str, timedelta):
                    shift_start_time = (datetime.min + shift_start_time_str).time()
                elif isinstance(shift_start_time_str, str):
                    shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
                else:
                    shift_start_time = shift_start_time_str
                if in_time.time() < shift_start_time:
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    if att.in_time - dt.datetime.combine(att.attendance_date,shift_start_time)<timedelta(minutes=1):
                        in_time = datetime.combine(in_time.date(), shift_start_time)
                    else:
                        in_time = in_time
                        
                # shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
                # shift_end_time = (datetime.min + shift_end_time_str).time()

                # if att.shift == "1":
                #     if out_time.time() > shift_end_time:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                #     else:
                #         out_time = out_time

                # elif att.shift == "G":
                #     if out_time.date().weekday() == 5 or out_time.date().weekday() == 6:
                #         reduced_end_time = (datetime.combine(out_time.date(), shift_end_time) - timedelta(minutes=30)).time()
                #         if out_time.time() > reduced_end_time:
                #             out_time = datetime.combine(out_time.date(), reduced_end_time)
                #         else:
                #             out_time = out_time
                #     else:
                        
                #         if out_time.time() > shift_end_time:
                #             out_time = datetime.combine(out_time.date(), shift_end_time)
                #         else:
                #             out_time = out_time

                # # If shift is "2", handle cases for shifts crossing midnight
                # if att.shift == "2":
                #     if out_time.time() <= time(23, 59, 59):
                #         out_time = out_time
                #     elif time(0, 0, 0) <= out_time.time() <= time(0, 59, 59):
                #         out_time = out_time
                #     else:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)


                wh = time_diff_in_hours(out_time,in_time)
                if wh:
                    wh = wh
                hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
                ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])
                hh = check_holiday(add_days(att.attendance_date,1),employee)
                date = check_holiday(att.attendance_date,employee)
                if att.shift =="G":
                    if hh == "WW" or date == "WW":
                        hd_threshold = hd_threshold - 0.5
                        ab_threshold = ab_threshold - 0.25
                    else:
                        hd_threshold = hd_threshold
                        ab_threshold = ab_threshold
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
                    
                if wh > 0 :
                    if wh < 24.0:
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        
                        frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59") 
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < ab_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift == "3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        elif att.custom_on_duty_application:
                            
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                    if att.custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                        
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day') 
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent') 
                                    else:
                                        custom_od_time = att.custom_od_time
                                        totwh=wh+custom_od_time
                                        print(totwh)
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                                
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        totwh=0
                        custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                        custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                        if att.custom_attendance_permission:
                            totwh=round(wh,1)+custom_permission_hours
                            if totwh >= hd_threshold:
                                frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift=="3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        elif att.custom_on_duty_application:
                        
                            od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                            if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                if custom_od_time==0.0:
                                    from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                    to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                    custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                    frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                else:
                                    custom_od_time = att.custom_od_time
                                totwh=wh+custom_od_time
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Present')
                        
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
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                    if diff_time.hour > 0 <3:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(diff_time.hour+1,0,0)
                                        else:
                                            ot_hours = time(diff_time.hour,0,0)
                                    elif diff_time.hour == 0:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(1,0,0)
                                        else:
                                            ot_hours = "00:00:00" 
                                    if diff_time.hour > 3:
                                        if diff_time.minute >= 60:
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
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(1,0,0)
                                    else:
                                        ot_hours = "00:00:00" 
                                elif diff_time.hour > 3:
                                    if diff_time.minute >= 60:
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
                        
                        shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                        if isinstance(shift_in_time, timedelta):
                            shift_in_time = (datetime.min + shift_in_time).time()
                        if in_time.time()<shift_in_time:
                            in_time = datetime.combine(in_time.date(), shift_in_time)
                        else:
                            in_time = in_time
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                        if diff_time.hour > 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
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


                    
                        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                        if ot_hours !='00:00:00':
                            ftr = [3600,60,1]
                            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                            ot_hr = round(hr/3600,1)
                        else:
                            ot_hr = '0.0'	
                        
                        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
            hh = check_holiday(att.attendance_date,att.employee)
            if not hh:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
            else:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        
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
        employement_type=frappe.db.get_value("Employee",{"name":att.employee},["employment_type"])
        if not employement_type == "Agency":
            if att.shift and att.in_time and att.out_time :
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
                if isinstance(shift_start_time_str, timedelta):
                    shift_start_time = (datetime.min + shift_start_time_str).time()
                elif isinstance(shift_start_time_str, str):
                    shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
                else:
                    shift_start_time = shift_start_time_str
                if in_time.time() < shift_start_time:
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    if att.in_time - dt.datetime.combine(att.attendance_date,shift_start_time)<timedelta(minutes=1):
                        in_time = datetime.combine(in_time.date(), shift_start_time)
                    else:
                        in_time = in_time
                
                # shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
                # shift_end_time = (datetime.min + shift_end_time_str).time()
                # if att.shift == "1":
                #     if out_time.time() > shift_end_time:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                #     else:
                #         out_time = out_time

                # elif att.shift == "G":
                #     if out_time.date().weekday() == 5:  
                #         reduced_end_time = (datetime.combine(out_time.date(), shift_end_time) - timedelta(minutes=30)).time()
                #         if out_time.time() > reduced_end_time:
                #             out_time = datetime.combine(out_time.date(), reduced_end_time)
                #         else:
                #             out_time = out_time
                #     else:
                #         if out_time.time() > shift_end_time:
                #             out_time = datetime.combine(out_time.date(), shift_end_time)
                #         else:
                #             out_time = out_time

                # elif att.shift == "2":
                #     if out_time.time() <= time(23, 59, 59):
                #         out_time = out_time
                #     elif time(0, 0, 0) <= out_time.time() <= time(0, 59, 59):
                #         out_time = out_time
                #     else:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)

                wh = time_diff_in_hours(out_time,in_time)
                if wh:
                    wh = round(wh,1)
                else:
                    wh =0
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
                hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                date = check_holiday(att.attendance_date,att.employee)
                if att.shift =="G":
                    if hh == "WW" or date == "WW":
                        hd_threshold = hd_threshold - 0.5
                        ab_threshold = ab_threshold-0.25
                    else:
                        hd_threshold = hd_threshold
                        ab_threshold = ab_threshold
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
                if default_shift:
                    if att.shift == default_shift:
                        if wh > 0 :
                            if wh < 24.0:
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                # if isinstance(time_in_standard_format, str):
                                #     working_hour = datetime.strptime(time_in_standard_format, "%H:%M:%S")
                                #     time_in_standard_format = timedelta(hours=working_hour.hour, minutes=working_hour.minute, seconds=working_hour.second)
                                # hours = time_in_standard_format.total_seconds() // 3600
                                # minutes = (time_in_standard_format.total_seconds() % 3600) // 60
                                # if minutes > 30:
                                #     wh = hours+0.5
                                # else:
                                #     wh = hours
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                            else:
                                wh = 24.0
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                                frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                            if wh < ab_threshold:
                                if att.leave_application:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses=='Full Day':
                                        if att.custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time 
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                        
                                            
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')

                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                            
                            elif wh >= ab_threshold and wh < hd_threshold:
                                totwh=0
                                custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                                custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                                if att.custom_attendance_permission:
                                    totwh=round(wh,1)+custom_permission_hours
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses=='Full Day':
                                        if att.custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time 
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                        
                                            
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                
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
                                            if diff_time.minute >= 60:
                                                ot_hours = time(diff_time.hour+1,0,0)
                                            else:
                                                ot_hours = time(diff_time.hour,0,0)
                                        elif diff_time.hour == 0:
                                            if diff_time.minute >= 60:
                                                ot_hours = time(1,0,0)
                                            else:
                                                ot_hours = "00:00:00" 
                                        if diff_time.hour > 3:
                                            if diff_time.minute >= 60:
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
                                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                                if isinstance(shift_in_time, timedelta):
                                    shift_in_time = (datetime.min + shift_in_time).time()
                                if in_time.time()<shift_in_time:
                                    in_time = datetime.combine(in_time.date(), shift_in_time)
                                else:
                                    in_time = in_time
                                
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                if diff_time.hour > 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
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
                                    if att.shift == "3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses=='Full Day':
                                        if att.custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time 
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                        
                                            
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')

                            elif wh >= ab_threshold and wh < hd_threshold:
                                totwh=0
                                custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                                custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                                if att.custom_attendance_permission:
                                    totwh=round(wh,1)+custom_permission_hours
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                    if att.shift=="3":
                                        frappe.db.set_value('Attendance',att.name,'shift','2')
                                elif att.custom_on_duty_application:
                                    od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                    if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                        if att.custom_od_time==0.0:
                                            from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                            to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                            custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                            frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                        else:
                                            custom_od_time = att.custom_od_time
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            elif wh >= hd_threshold:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')  
                            shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                            shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                            out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                            shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                            ot_hours = "00:00:00"
                            hh = check_holiday(att.attendance_date,att.employee)
                            if not hh:
                                if shift_et < out_time:
                                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                    if diff_time.hour > 0 <3:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(diff_time.hour+1,0,0)
                                        else:
                                            ot_hours = time(diff_time.hour,0,0)
                                    elif diff_time.hour == 0:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(1,0,0)
                                        else:
                                            ot_hours = "00:00:00" 
                                    if diff_time.hour > 3:
                                        if diff_time.minute >= 60:
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
                                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                                if isinstance(shift_in_time, timedelta):
                                    shift_in_time = (datetime.min + shift_in_time).time()
                                if in_time.time()<shift_in_time:
                                    in_time = datetime.combine(in_time.date(), shift_in_time)
                                else:
                                    in_time = in_time
                                
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                if diff_time.hour > 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
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
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            totwh=0
                            custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                            custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                            if att.custom_attendance_permission:
                                totwh=round(wh,1)+custom_permission_hours
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Absent')
                                if att.shift=="3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            elif att.custom_on_duty_application:
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                    if custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    else:
                                        custom_od_time = att.custom_od_time
                                    totwh=wh+custom_od_time
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                    
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')  
                        shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                        shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        ot_hours = "00:00:00"
                        hh = check_holiday(att.attendance_date,att.employee)
                        if not hh:
                            if shift_et < out_time:
                                difference = time_diff_in_timedelta_1(shift_et,out_time)
                                diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                if diff_time.hour > 0 <3:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(1,0,0)
                                    else:
                                        ot_hours = "00:00:00" 
                                if diff_time.hour > 3:
                                    if diff_time.minute >= 60:
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
                            shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                            if isinstance(shift_in_time, timedelta):
                                shift_in_time = (datetime.min + shift_in_time).time()
                            if in_time.time()<shift_in_time:
                                in_time = datetime.combine(in_time.date(), shift_in_time)
                            else:
                                in_time = in_time
                            
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                            frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                            if diff_time.hour > 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
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
            hh = check_holiday(att.attendance_date,att.employee)
            if not hh:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift =='8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        
        else:
            if att.shift and att.in_time and att.out_time :
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
                if isinstance(shift_start_time_str, timedelta):
                    shift_start_time = (datetime.min + shift_start_time_str).time()
                elif isinstance(shift_start_time_str, str):
                    shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
                else:
                    shift_start_time = shift_start_time_str
                if in_time.time() < shift_start_time:
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    if att.in_time - dt.datetime.combine(att.attendance_date,shift_start_time)<timedelta(minutes=1):
                        in_time = datetime.combine(in_time.date(), shift_start_time)
                    else:
                        in_time = in_time
                # shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
                # shift_end_time = (datetime.min + shift_end_time_str).time()

                # if att.shift == "1":
                #     if out_time.time() > shift_end_time:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                #     else:
                #         out_time = out_time

                # elif att.shift == "G":
                #     if out_time.date().weekday() == 5 or out_time.date().weekday() == 6:
                #         reduced_end_time = (datetime.combine(out_time.date(), shift_end_time) - timedelta(minutes=30)).time()
                #         if out_time.time() > reduced_end_time:
                #             out_time = datetime.combine(out_time.date(), reduced_end_time)
                #         else:
                #             out_time = out_time
                #     else:
                        
                #         if out_time.time() > shift_end_time:
                #             out_time = datetime.combine(out_time.date(), shift_end_time)
                #         else:
                #             out_time = out_time

                # elif att.shift == "2":
                #     if out_time.time() <= time(23, 59, 59):
                #         out_time = out_time
                #     elif time(0, 0, 0) <= out_time.time() <= time(0, 59, 59):
                #         out_time = out_time
                #     else:
                #         out_time = datetime.combine(out_time.date(), shift_end_time)
                        
                wh = time_diff_in_hours(out_time,in_time)
                if wh:
                    wh = round(wh,1)
                hd_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_half_day'])
                ab_threshold=frappe.db.get_value("Shift Type",{'name':att.shift},['working_hours_threshold_for_absent'])
                hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                date = check_holiday(att.attendance_date,att.employee)
                if att.shift =="G":
                    if hh == "WW" or date == "WW":
                        hd_threshold = hd_threshold - 0.5
                        ab_threshold = ab_threshold - 0.25
                    else:
                        hd_threshold = hd_threshold
                        ab_threshold = ab_threshold
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
                    
                if wh > 0 :
                    if wh < 24.0:
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        
                        frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59") 
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < ab_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift == "3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        elif att.custom_on_duty_application:
                            
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                    if att.custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    
                                        totwh=wh+custom_od_time
                                        if totwh >= hd_threshold:
                                        
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day') 
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent') 
                                    else:
                                        custom_od_time = att.custom_od_time
                                        totwh=wh+custom_od_time
                                        print(totwh)
                                        if totwh >= hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Present')
                                        elif totwh >= ab_threshold and totwh < hd_threshold:
                                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                        else:
                                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                                
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        totwh=0
                        custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                        custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                        if att.custom_attendance_permission:
                            totwh=round(wh,1)+custom_permission_hours
                            if totwh >= hd_threshold:
                                frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift=="3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        elif att.custom_on_duty_application:
                        
                            od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                            if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                if custom_od_time==0.0:
                                    from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                    to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                    custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                    frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                else:
                                    custom_od_time = att.custom_od_time
                                totwh=wh+custom_od_time
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Present')
                        
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
                                    frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                                    if diff_time.hour > 0 <3:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(diff_time.hour+1,0,0)
                                        else:
                                            ot_hours = time(diff_time.hour,0,0)
                                    elif diff_time.hour == 0:
                                        if diff_time.minute >= 60:
                                            ot_hours = time(1,0,0)
                                        else:
                                            ot_hours = "00:00:00" 
                                    if diff_time.hour > 3:
                                        if diff_time.minute >= 60:
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
                                    if diff_time.minute >= 60:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 60:
                                        ot_hours = time(1,0,0)
                                    else:
                                        ot_hours = "00:00:00" 
                                elif diff_time.hour > 3:
                                    if diff_time.minute >= 60:
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
                        
                        shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                        if isinstance(shift_in_time, timedelta):
                            shift_in_time = (datetime.min + shift_in_time).time()
                        if in_time.time()<shift_in_time:
                            in_time = datetime.combine(in_time.date(), shift_in_time)
                        else:
                            in_time = in_time
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                        frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                        if diff_time.hour > 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
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


                    
                        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                        if ot_hours !='00:00:00':
                            ftr = [3600,60,1]
                            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                            ot_hr = round(hr/3600,1)
                        else:
                            ot_hr = '0.0'	
                        
                        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
            hh = check_holiday(att.attendance_date,att.employee)
            if not hh:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
            else:
                if att.shift and att.in_time:
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                
                if att.shift and att.out_time:
                    if att.shift =='1':
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift =='G':
                        hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                        date = check_holiday(att.attendance_date,att.employee)
                        if hh == "WW" or date == "WW":
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                            end_time = end_time_30 - timedelta(minutes=30)
                            if att.out_time < end_time:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                        else:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    elif att.shift == '2' or att.shift == '8 to 8':
                        shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                        shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                        if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                            shift_end_datetime += timedelta(days=1)

                        if att.out_time < shift_end_datetime:
                            early_out_duration = shift_end_datetime - att.out_time
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
            
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
            

def ot_calculation_for_employee(from_date,to_date,employee):
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' and employee = '%s' """%(from_date,to_date,employee),as_dict=True)
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
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                            elif diff_time.hour > 3:
                                if diff_time.minute >= 60:
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
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(1,0,0)
                            else:
                                ot_hours = "00:00:00" 
                        elif diff_time.hour > 3:
                            if diff_time.minute >= 60:
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
                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                if isinstance(shift_in_time, timedelta):
                    shift_in_time = (datetime.min + shift_in_time).time()
                if in_time.time()<shift_in_time:
                    in_time = datetime.combine(in_time.date(), shift_in_time)
                else:
                    in_time = in_time
                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                if diff_time.hour > 0:
                    if diff_time.minute >= 60:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 60:
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
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
        if ot_hours !='00:00:00':
            ftr = [3600,60,1]
            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
            ot_hr = round(hr/3600,1)
        else:
            ot_hr = '0.0'	
        
        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)


def ot_calculation_for_department(from_date,to_date,department):
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' and department = '%s' """%(from_date,to_date,department),as_dict=True)
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
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                            elif diff_time.hour > 3:
                                if diff_time.minute >= 60:
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
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(1,0,0)
                            else:
                                ot_hours = "00:00:00" 
                        elif diff_time.hour > 3:
                            if diff_time.minute >= 60:
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
                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                if isinstance(shift_in_time, timedelta):
                    shift_in_time = (datetime.min + shift_in_time).time()
                if in_time.time()<shift_in_time:
                    in_time = datetime.combine(in_time.date(), shift_in_time)
                else:
                    in_time = in_time
                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                if diff_time.hour > 0:
                    if diff_time.minute >= 60:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 60:
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
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
        if ot_hours !='00:00:00':
            ftr = [3600,60,1]
            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
            ot_hr = round(hr/3600,1)
        else:
            ot_hr = '0.0'	
        
        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
        
def ot_calculation_for_department_employee(from_date,to_date,department,name):
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' and department = '%s' and employee = '%s' """%(from_date,to_date,department,name),as_dict=True)
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
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                            elif diff_time.hour > 3:
                                if diff_time.minute >= 60:
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
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(1,0,0)
                            else:
                                ot_hours = "00:00:00" 
                        elif diff_time.hour > 3:
                            if diff_time.minute >= 60:
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
                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                if isinstance(shift_in_time, timedelta):
                    shift_in_time = (datetime.min + shift_in_time).time()
                if in_time.time()<shift_in_time:
                    in_time = datetime.combine(in_time.date(), shift_in_time)
                else:
                    in_time = in_time
                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                if diff_time.hour > 0:
                    if diff_time.minute >= 60:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 60:
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
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
        if ot_hours !='00:00:00':
            ftr = [3600,60,1]
            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
            ot_hr = round(hr/3600,1)
        else:
            ot_hr = '0.0'	
        
        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
        
        

def mark_wh_regularize(name):
    attendance = frappe.db.get_all('Attendance',{'name':name,'docstatus':('!=','2')},['*'])
    for att in attendance:
        # update_late_deduction(att.employee,att.attendance_date)
        # if att.in_time and att.out_time:
        #     if not att.custom_on_duty_application:
        #         in_time = att.in_time
        #         out_time = att.out_time
        #     else:
        #         if att.session_from_time and att.session_to_time: 
        #             in_time = att.session_from_time
        #             out_time = att.session_to_time
        #         else:
        if att.shift and att.in_time and att.out_time :
            if att.in_time and att.out_time:
                in_time = att.in_time
                out_time = att.out_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
            shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
            if isinstance(shift_start_time_str, timedelta):
                shift_start_time = (datetime.min + shift_start_time_str).time()
            elif isinstance(shift_start_time_str, str):
                shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
            else:
                shift_start_time = shift_start_time_str
            if in_time.time() < shift_start_time:
                in_time = datetime.combine(in_time.date(), shift_start_time)
            else:
                if att.in_time - dt.datetime.combine(att.attendance_date,shift_start_time)<timedelta(minutes=1):
                    in_time = datetime.combine(in_time.date(), shift_start_time)
                else:
                    in_time = in_time
            
          
            wh = time_diff_in_hours(out_time,in_time)
            if wh:
                wh = round(wh,1)
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
            hh = check_holiday(add_days(att.attendance_date,1),att.employee)
            date = check_holiday(att.attendance_date,att.employee)
            if att.shift =="G":
                if hh == "WW" or date == "WW":
                    hd_threshold = hd_threshold - 0.5
                    ab_threshold = ab_threshold-0.25
                else:
                    hd_threshold = hd_threshold
                    ab_threshold = ab_threshold
            else:
                hd_threshold = hd_threshold
                ab_threshold = ab_threshold
            if default_shift:
                if default_shift == att.shift:
                    
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < ab_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            elif att.custom_on_duty_application:
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                print(att.custom_on_duty_application)
                                if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                    print(od_ses)
                                    if att.custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    else:
                                        custom_od_time = att.custom_od_time
                                    totwh=wh+custom_od_time
                                    print(totwh)
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    elif totwh >= ab_threshold and totwh < hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                else:
                            
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            
                            frappe.db.set_value('Attendance',att.name,'status','Present')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            totwh=0
                            custom_permission_hours = float(att.custom_permission_hour) if att.custom_permission_hour else 0.0
                            custom_od_time=float(att.custom_od_time) if att.custom_od_time else 0.0
                            if att.custom_attendance_permission:
                                totwh=round(wh,1)+custom_permission_hours
                                if totwh >= hd_threshold:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift=="3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            elif att.custom_on_duty_application:
                                od_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_date_session'])
                                if od_ses=='First Half' or od_ses=='Second Half' or od_ses == 'Full Day':
                                    if att.custom_od_time==0.0:
                                        from_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['from_time'])
                                        to_ses=frappe.db.get_value("On Duty Application",{'name':att.custom_on_duty_application},['to_time'])
                                        custom_od_time=time_diff_in_hours(to_ses,from_ses)
                                        frappe.db.set_value('Attendance',att.name,'custom_od_time',custom_od_time)
                                    else:
                                        custom_od_time = att.od_time
                                    totwh=wh+custom_od_time
                                    if totwh >= hd_threshold:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')
                                    else:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                else:
                                    frappe.db.set_value('Attendance',att.name,'status','Present')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                          
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
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= ab_threshold and wh < hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= hd_threshold:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                if att.shift == "3":
                                    frappe.db.set_value('Attendance',att.name,'shift','2')
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
                            if att.shift == "3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= ab_threshold and wh < hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift == "3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    elif wh >= hd_threshold:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            if att.shift == "3":
                                frappe.db.set_value('Attendance',att.name,'shift','2')
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
                    if att.in_time - start_time > timedelta(minutes=1):
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            
            if att.shift and att.out_time:
                if att.shift =='1':
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                    if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                elif att.shift =='G':
                    hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                    date = check_holiday(att.attendance_date,att.employee)
                    if hh == "WW" or date == "WW":
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                        end_time = end_time_30 - timedelta(minutes=30)
                        if att.out_time < end_time:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    else:
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                elif att.shift == '2' or att.shift == '8 to 8':
                    shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                    shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                    if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                        shift_end_datetime += timedelta(days=1)

                    if att.out_time < shift_end_datetime:
                        early_out_duration = shift_end_datetime - att.out_time
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
        else:
            if att.shift and att.in_time:
                shift_time = frappe.get_value(
                    "Shift Type", {'name': att.shift}, ["start_time"])
                shift_start_time = datetime.strptime(
                    str(shift_time), '%H:%M:%S').time()
                start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                
                if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                    if att.in_time - start_time > timedelta(minutes=1):
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
            
            if att.shift and att.out_time:
                if att.shift =='1':
                    shift_time = frappe.get_value(
                        "Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                    if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                elif att.shift =='G':
                    hh = check_holiday(add_days(att.attendance_date,1),att.employee)
                    date = check_holiday(att.attendance_date,att.employee)
                    if hh == "WW" or date == "WW":
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time_30 = dt.datetime.combine(att.attendance_date,shift_end_time)
                        end_time = end_time_30 - timedelta(minutes=30)
                        if att.out_time < end_time:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    else:
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                elif att.shift == '2' or att.shift == '8 to 8':
                    shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                    shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                    if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                        shift_end_datetime += timedelta(days=1)

                    if att.out_time < shift_end_datetime:
                        early_out_duration = shift_end_datetime - att.out_time
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', early_out_duration)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
def ot_calculation_regularize(name):
    attendance = frappe.db.get_all('Attendance',{'name':name,'docstatus':('!=','2')},['*'])
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
                                if diff_time.minute >= 60:
                                    ot_hours = time(diff_time.hour+1,0,0)
                                else:
                                    ot_hours = time(diff_time.hour,0,0)
                            elif diff_time.hour == 0:
                                if diff_time.minute >= 60:
                                    ot_hours = time(1,0,0)
                                else:
                                    ot_hours = "00:00:00" 
                            elif diff_time.hour > 3:
                                if diff_time.minute >= 60:
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
                            if diff_time.minute >= 60:
                                ot_hours = time(diff_time.hour+1,0,0)
                            else:
                                ot_hours = time(diff_time.hour,0,0)
                        elif diff_time.hour == 0:
                            if diff_time.minute >= 60:
                                ot_hours = time(1,0,0)
                            else:
                                ot_hours = "00:00:00" 
                        elif diff_time.hour > 3:
                            if diff_time.minute >= 60:
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
                shift_in_time = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
                if isinstance(shift_in_time, timedelta):
                    shift_in_time = (datetime.min + shift_in_time).time()
                if in_time.time()<shift_in_time:
                    in_time = datetime.combine(in_time.date(), shift_in_time)
                else:
                    in_time = in_time
                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                diff_time = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_extra_hours_total",diff_time)
                if diff_time.hour > 0:
                    if diff_time.minute >= 60:
                        ot_hours = time(diff_time.hour+1,0,0)
                    else:
                        ot_hours = time(diff_time.hour,0,0)
                elif diff_time.hour == 0:
                    if diff_time.minute >= 60:
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
        frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
        if ot_hours !='00:00:00':
            ftr = [3600,60,1]
            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
            ot_hr = round(hr/3600,1)
        else:
            ot_hr = '0.0'	
        
        frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)
        
        
@frappe.whitelist()
def grace_late_time(to_date):
    start_of_month = datetime.strptime(to_date, "%Y-%m-%d")
    end_of_month = to_date
    start_of_month_str = start_of_month.replace(day=1)
    end_of_month_str = to_date
    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "docstatus": ("!=", 2),
            "late_entry": 1,
            "attendance_date": ("between", (start_of_month_str, end_of_month_str))
        },
        fields=["name", "employee", "custom_attendance_permission","attendance_date", "custom_late_entry_time", "early_exit", "status"]
    )
    
    employee_attendance = {}
    for record in attendance_records:
        if record["employee"] not in employee_attendance:
            employee_attendance[record["employee"]] = []
        employee_attendance[record["employee"]].append(record)
    for employee, records in employee_attendance.items():
        records.sort(key=lambda x: x["attendance_date"])

        late_entry_threshold = timedelta(minutes=10)
        processed_days = 0  

        for record in records:
            
            if isinstance(record["custom_late_entry_time"], timedelta):
                custom_late_entry_time = record["custom_late_entry_time"]
            else:
                custom_late_entry_time = timedelta(
                    hours=record["custom_late_entry_time"].hour,
                    minutes=record["custom_late_entry_time"].minute,
                    seconds=record["custom_late_entry_time"].second
                )
            if processed_days < 3 and custom_late_entry_time <= late_entry_threshold:
                if record["early_exit"] == 0 :
                    if record["status"] != "Present":
                        frappe.db.set_value("Attendance", record["name"], "status", "Present")
                    processed_days += 1

