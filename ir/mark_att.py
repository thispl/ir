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

@frappe.whitelist()
def mark_att():
	# from_date = add_days(today(),-1)  
	# to_date = today()
	from_date='2024-05-10'
	to_date='2024-05-10'
	dates = get_dates(from_date,to_date)
	for date in dates:
		from_date = add_days(date,0)
		to_date = date
	checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
	for c in checkins:
		employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
		if employee:
			att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
			if att:
				frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
	mark_absent(from_date,to_date)
	mark_wh(from_date,to_date)
	# ot_calculation(from_date,to_date)

def get_dates(from_date,to_date):
	no_of_days = date_diff(add_days(to_date, 1), from_date)
	dates = [add_days(from_date, i) for i in range(0, no_of_days)]
	return dates

def mark_attendance_from_checkin(employee,time,log_type):
	att_date = time.date()
	att_time = time.time()
	shift_ass = frappe.db.exists("Shift Assignment",{'employee':employee,'start_date':('>=',att_date),'end_date':('<=',att_date)})
	
	if shift_ass:
		shift_type=frappe.get_doc("Shift Assignment",{'employee':employee,'start_date':('>=',att_date),'end_date':('<=',att_date)})
		shift_status=shift_type.shift_type
		if log_type == 'IN':
			shift=''
			shift1 = frappe.db.get_value('Shift Type',{'name':shift_status},['start_time'])
			shift_late_time=shift1 + timedelta(minutes=15)
			att_time_seconds = att_time.hour * 3600 + att_time.minute * 60 + att_time.second
			if att_time_seconds<shift1.total_seconds() or shift1.total_seconds() < att_time_seconds < shift_late_time.total_seconds():
				shift = shift_status
				print("hi")
			att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
			checkins = frappe.db.sql(""" select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' order by time ASC"""%(employee,att_date),as_dict=True)
			if not att and checkins:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.shift = shift
				att.status = 'Absent'
				if len(checkins) > 0:
					att.in_time = checkins[0].time
				else:
					att.in_time = checkins[0].time
				att.custom_total_working_hours = "00:00:00"
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
					att.save(ignore_permissions=True)
					frappe.db.commit()
					for c in checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
		
		if shift_status == '2':
			shift1 = frappe.db.get_value('Shift Type',{'name':shift_status},['end_time'])
			next_day = add_days(att_date,1)
			checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' order by time ASC "%(employee,next_day),as_dict=True)
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
			if att:
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0:
					if not att.out_time:
						if att.shift == '':
							if len(checkins) > 0:
								att.shift = shift_status
								att.out_time = checkins[-1].time
								for c in checkins:
									frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
									frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							else:
								att.shift = get_actual_shift(get_time(checkins[0].time),employee)
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
				att.status = 'Absent'
				if len(checkins) > 0:
					att.out_time = checkins[-1].time
					att.shift = shift_status
					for c in checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					att.out_time = checkins[0].time
					att.shift = shift_status
					frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
				att.save(ignore_permissions=True)
				frappe.db.commit()
		elif shift_status != '2':
			if log_type=='OUT':
				print(shift_status)
				checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' order by time ASC"%(employee,att_date),as_dict=True)
				att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
				if att:
					att = frappe.get_doc("Attendance",att)
					if att.docstatus == 0:
						
						if att.shift == '':
							print(att.employee_name)
							print(checkins[-1].time)
							if len(checkins) > 0:
								att.shift = shift_status
								att.out_time = checkins[-1].time
								for c in checkins:
									frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
									frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							else:
								att.shift = get_actual_shift(get_time(checkins[0].time),employee)
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
					if len(checkins) > 0:
						att.shift = shift_status
						att.out_time = checkins[-1].time
						for c in checkins:
							frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
					else:
						att.shift = get_actual_shift(get_time(checkins[0].time))
						att.out_time = checkins[0].time
						frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					att.save(ignore_permissions=True)
					frappe.db.commit()
	else:
		att = frappe.new_doc("Attendance")
		
		att.employee = employee
		att.attendance_date = att_date
		att.shift = ''
		att.status = 'Absent'				
		att.custom_total_working_hours = "00:00:00"
		att.working_hours = "0.0"
		att.save(ignore_permissions=True)
		frappe.db.commit()

def mark_wh():
	from_date='2024-05-09'
	to_date='2024-05-09'
	attendance = frappe.db.get_all('Attendance',{'employee':'HR-EMP-00002','attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
	for att in attendance:
		if att.shift:
			if att.in_time and att.out_time:
				shift1 = frappe.db.get_value('Shift Type',{'name':att.shift},['start_time'])
				shift_late_time=shift1 + timedelta(minutes=15)
				att_intime_seconds = att.in_time.hour * 3600 + att.in_time.minute * 60 + att.in_time.second
				if att_intime_seconds<=shift1.total_seconds():
					in_time=shift1
				elif shift1.total_seconds() < att_intime_seconds < shift_late_time.total_seconds():
					in_time = att.in_time
				
				out_time = att.out_time
				if isinstance(in_time, str):
					in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
				if isinstance(out_time, str):
					out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
				
				att_wh = time_diff_in_hours(out_time,in_time)
				wh = float(att_wh)
				print(wh)
				if wh > 0 :
					if wh < 24.0:
						time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
						frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
						frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
					else:
						wh = 24.0
						frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
						frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
					if wh < 4:
						frappe.db.set_value('Attendance',att.name,'status','Absent')
					elif wh >= 4 and wh < 8:
						frappe.db.set_value('Attendance',att.name,'status','Half Day')
					elif wh >= 8:
						frappe.db.set_value('Attendance',att.name,'status','Present')  
				else:
					frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
					frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
					
		else:
			frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
			
def time_diff_in_timedelta(in_time, out_time):
	datetime_format = "%H:%M:%S"
	if out_time and in_time :
		return out_time - in_time

@frappe.whitelist()
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
					att.save(ignore_permissions=True)
					frappe.db.commit()


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
