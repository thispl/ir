from email import message
import frappe
from frappe import _
import datetime, math
from datetime import date, timedelta, datetime,time
import datetime as dt
from frappe.utils import time_diff_in_hours
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from ir.ir.doctype.attendance_regularize.attendance_regularize import AttendanceRegularize
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,

    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime,today, format_date)
# import pandas as pd
import math
from frappe.utils import add_months, cint, flt, getdate, time_diff_in_hours
import datetime as dt
from datetime import datetime, timedelta
from ir.mark_attendance import update_att_with_employee


class CustomSalarySlip(SalarySlip):
    def get_date_details(self):
        ots = frappe.db.sql("""
            SELECT * FROM `tabOver Time Request`
            WHERE ot_date BETWEEN %s AND %s
            AND employee = %s  and workflow_state ="Approved"
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        
        ots_od = frappe.db.sql("""
            SELECT *
            FROM `tabOver Time Request`
            WHERE od_date BETWEEN %s AND %s
            AND employee = %s  and workflow_state ="Approved"
        """, (self.start_date, self.end_date, self.employee), as_dict=True)

        custom_ot_hours = 0
        for ot in ots:
            total_seconds = ot.ot_hour.total_seconds()
            ot_hr = total_seconds / 3600  
            custom_ot_hours += ot_hr
        for od in ots_od:
            total_seconds = od.ot_hour.total_seconds()
            od_hr = total_seconds / 3600  
            custom_ot_hours += od_hr
        self.custom_overtime = custom_ot_hours

    
        canteen = frappe.db.sql("""
            SELECT COUNT(status) AS present_days
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus !=2  AND employee = %s
            AND status = 'Present'
        
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        
        canteen_half = frappe.db.sql("""
            SELECT COUNT(status) AS present_days
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus !=2  AND employee = %s
            AND status = 'Half Day'
        
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        
        canteens = frappe.db.sql("""
            SELECT status , working_hours,custom_od_time
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus !=2  AND employee = %s
            AND status IN ('Present', 'Half Day')
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        # Fetch attendance records
        attendance = frappe.db.sql("""
        SELECT attendance_date, status
        FROM `tabAttendance`
        WHERE attendance_date BETWEEN %s AND %s
        AND docstatus != 2 AND employee = %s
        AND status IN ('Present', 'Half Day')
        """, (self.start_date, self.end_date, self.employee), as_dict=True)

        holiday_list = frappe.db.get_value('Company', {'name': self.company}, 'default_holiday_list')

        holiday = frappe.db.sql("""
        SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off
        FROM `tabHoliday List`
        LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name
        WHERE `tabHoliday List`.name = %s
        AND holiday_date BETWEEN %s AND %s
        """, (holiday_list, self.start_date, self.end_date), as_dict=True)

        agency_holiday = frappe.db.sql("""
        SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off
        FROM `tabHoliday List`
        LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name
        WHERE `tabHoliday List`.name = %s
        AND holiday_date BETWEEN %s AND %s AND `tabHoliday`.weekly_off = 1
        """, (holiday_list, self.start_date, self.end_date), as_dict=True)

        if not self.custom_agency:
            holiday_count = len(holiday)
        else:
            holiday_count = len(agency_holiday)
        if not self.custom_agency:
            self.custom_holidays = holiday_count
        else:
            self.custom_holidays = holiday_count

        agency_holiday_date = frappe.db.sql("""
            SELECT COUNT(status) AS present_days
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus !=2  AND employee = %s
            AND status = 'Holiday'
        
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        
        if agency_holiday_date[0]['present_days']:
            self.custom_agency_paid_holiday = agency_holiday_date[0]['present_days']
        compoffdays = 0
        count = 0

        for h in holiday:
            for a in attendance:
                if h.holiday_date == a.attendance_date:
                    if a.status == "Present":
                        count += 1
                        compoffdays += 1
                    elif a.status == "Half Day":
                        count += 0.5
                        compoffdays += 0.5
            
                            
        count_pre = 0
        for present in canteens:
            if present.status == "Present":
                count_pre  += 1
                
            elif present.status == "Half Day":
                if not self.custom_agency:
                    if present.working_hours is not None:
                        if present.working_hours + present.custom_od_time >= 4:
                            count_pre += 0.5
                else:
                   count_pre += 0.5 
            
        if not self.custom_agency:
            
            self.custom_present_days_holiday = count_pre - count if count_pre else 0
        else:
            including_holiday = frappe.db.get_value("Agency",{"name":self.custom_agency},["including_holiday"])
            if including_holiday == 1:
                self.custom_present_days_holiday = count_pre if count_pre else 0
            else:
                self.custom_present_days_holiday = count_pre - count if count_pre else 0
            
        custom_present_days=canteen[0]['present_days']+holiday_count-compoffdays+(canteen_half[0]['present_days']/2)
        if custom_present_days>0:
                
            self.custom_present_days=canteen[0]['present_days']+holiday_count-compoffdays +(canteen_half[0]['present_days']/2)
        else:
            self.custom_present_days=0
        if self.custom_present_days ==0:
            self.leave_without_pay = self.custom_holidays

class CustomAttendanceRegularize(AttendanceRegularize): 
    def on_submit(self):
        if self.corrected_shift or self.corrected_in or self.corrected_out:
            att_ = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':self.attendance_date})
            if att_:
                att = frappe.get_doc('Attendance', att_)
                if self.shift:
                    frappe.db.set_value("Attendance",att.name,"shift",self.corrected_shift)
                if self.in_time:
                    frappe.db.set_value("Attendance",att.name,"in_time",self.corrected_in)
                else:
                    self.corrected_in = None
                if self.out_time:
                    frappe.db.set_value("Attendance",att.name,"out_time",self.corrected_out)
                else:
                    self.corrected_out = None
                attendance = frappe.get_all('Attendance',{'name':att_},['*'])
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
                        if wh > 0 :
                            if wh < 24.0:
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                                if att.docstatus == 1:
                                    time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                    frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                    frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                            else:
                                wh = 24.0
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                                frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                            if wh < 4:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                            elif wh >= 4 and wh < 6:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            elif wh >= 6:
                                frappe.db.set_value('Attendance',att.name,'status','Present')  
                            shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                            shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                            out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                            shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                            ot_hours = None
                            hh = check_holiday(att.attendance_date,att.employee)
                            if not hh:
                                if shift_et < out_time:
                                    difference = time_diff_in_timedelta_1(shift_et,out_time)
                                    diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
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
                        if str(ot_hours) != '00:00:00':
                            if shift_et < out_time and out_time:	
                                ftr = [3600, 60, 1]
                                if ot_hours:
                                    hours = ot_hours.hour
                                    minutes = ot_hours.minute
                                    seconds = ot_hours.second
                                    hr = hours + minutes / 60 + seconds / 3600
                                    
                                else:
                                    hr = 0
                                ot_hr = round(hr)
                                
                                ot_hours = "00:00:00"
                            else:
                                ot_hr = '0.0'
                        else:
                            ot_hours = "00:00:00"
                        # if shift_et < out_time:	
                        #     frappe.errprint(ot_hr)	
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
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        if att.shift and att.out_time:
                            shift_time = frappe.get_value(
                                "Shift Type", {'name': att.shift}, ["end_time"])
                            shift_end_time = datetime.strptime(
                                str(shift_time), '%H:%M:%S').time()
                            end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                            if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', att.out_time - end_time)
                            else:
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',  "00:00:00")
                frappe.db.set_value('Attendance', att.name, 'custom_regularize_marked', 1)
                frappe.db.set_value('Attendance', att.name, 'custom_attendance_regularize',self.name)
                if self.over_time ==1 and self.corrected_ot:
                    if str(self.corrected_ot) != '00:00:00':
                        ot_hours = self.corrected_ot
                        if ot_hours:
                            ot_hours_dt = datetime.strptime(ot_hours, '%H:%M:%S')
                            hours = ot_hours_dt.hour
                            minutes = ot_hours_dt.minute
                            seconds = ot_hours_dt.second
                            hr = hours + minutes / 60 + seconds / 3600
                            
                            ot_hr = round(hr)
                            
                            ot_hours = "00:00:00"
                        else:
                            ot_hr = '0.0'
                    frappe.db.set_value('Attendance', att.name, 'custom_attendance_regularize', self.name)
                    frappe.db.set_value('Attendance', att.name, 'custom_ot_hours', self.corrected_ot)
                    frappe.db.set_value('Attendance', att.name, 'custom_over_time_hours',ot_hr)
                    if frappe.db.exists("Over Time Request",{'employee':self.employee,'ot_date':self.attendance_date,'docstatus':['!=',2]}):
                        ot_req=frappe.get_doc("Over Time Request",{'employee':self.employee,'ot_date':self.attendance_date,'docstatus':['!=',2]})
                        ot_req.ot_hour=self.corrected_ot
                        ot_req.save()
                    else:
                        ot_req=frappe.new_doc("Over Time Request")
                        ot_req.employee = self.employee
                        ot_req.ot_date = self.attendance_date
                        ot_req.ot_hour = self.corrected_ot
                        ot_req.save(ignore_permissions=True)
                        frappe.db.commit()
                else:
                   
                    att_ = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':self.attendance_date})
                    if att_:
                        att = frappe.get_doc('Attendance', att_)
                        if self.shift:
                            frappe.db.set_value("Attendance",att.name,"shift",self.corrected_shift)
                        if self.in_time:
                            frappe.db.set_value("Attendance",att.name,"in_time",self.corrected_in)
                        else:
                            self.corrected_in = None
                        if self.out_time:
                            frappe.db.set_value("Attendance",att.name,"out_time",self.corrected_out)
                        else:
                            self.corrected_out = None
                        attendance = frappe.get_all('Attendance',{'name':att_},['*'])
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
                                if wh > 0 :
                                    if wh < 24.0:
                                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                        frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                                        if att.docstatus == 1:
                                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                                    else:
                                        wh = 24.0
                                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                                    if wh < 4:
                                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                                    elif wh >= 4 and wh < 6:
                                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                                    elif wh >= 6:
                                        frappe.db.set_value('Attendance',att.name,'status','Present')  
                                    shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                                    shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                                    out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                                    shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                                    ot_hours = None
                                    hh = check_holiday(att.attendance_date,att.employee)
                                    if not hh:
                                        if shift_et < out_time:
                                
                                            difference = time_diff_in_timedelta_1(shift_et,out_time)
                                            diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
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
                                if str(ot_hours) != '00:00:00':
                                    if shift_et < out_time and out_time:	
                                        ftr = [3600, 60, 1]
                                        if ot_hours:
                                            hours = ot_hours.hour
                                            minutes = ot_hours.minute
                                            seconds = ot_hours.second
                                            hr = hours + minutes / 60 + seconds / 3600
                                            
                                        else:
                                            hr = 0
                                        ot_hr = round(hr)
                                        
                                        ot_hours = "00:00:00"
                                    else:
                                        ot_hr = '0.0'
                                else:
                                    ot_hours = "00:00:00"
                                # if shift_et < out_time:	
                                #     frappe.errprint(ot_hr)	
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
                                        frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                                    else:
                                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                                if att.shift and att.out_time:
                                    shift_time = frappe.get_value(
                                        "Shift Type", {'name': att.shift}, ["end_time"])
                                    shift_end_time = datetime.strptime(
                                        str(shift_time), '%H:%M:%S').time()
                                    end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                                    if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', att.out_time - end_time)
                                    else:
                                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                        frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                            else:
                                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                                frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',  "00:00:00")
                        frappe.db.set_value('Attendance', att.name, 'custom_regularize_marked', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_attendance_regularize',self.name)              
    def on_cancel(self):
        attendance_obj = frappe.get_doc("Attendance", self.attendance_marked)
        if attendance_obj.docstatus ==1:
            attendance_obj.cancel()
            to_date = add_days(self.attendance_date,1)
            
            update_att_with_employee(self.attendance_date, to_date, self.employee)
        if attendance_obj.docstatus ==0:
            frappe.db.sql(""" Update  `tabAttendance` Set custom_attendance_regularize = "" , custom_regularize_marked = 0 WHERE name = %s""", (attendance_obj.name,), as_dict=True)
            to_date = add_days(self.attendance_date,1)
            # update_att_with_employee(self.attendance_date, to_date, self.employee)             
    
                
@frappe.whitelist()
def check_holiday(date,emp):
    holiday_list = frappe.db.get_value('Employee',{'name':emp},'holiday_list')
    holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off from `tabHoliday List`
    left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
    doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
    if holiday :
        if doj < holiday[0].holiday_date:
            if holiday[0].weekly_off == 1:
                return "WW"     
            else:
                return "HH"  


@frappe.whitelist()           
def time_diff_in_timedelta_1(time1, time2):
    datetime1 = datetime.combine(datetime.min, time1)
    datetime2 = datetime.combine(datetime.min, time2)
    timedelta_seconds = (datetime2 - datetime1).total_seconds()
    diff_timedelta = timedelta(seconds=timedelta_seconds)
    return diff_timedelta



    
@frappe.whitelist()
def time_diff_in_timedelta(time1, time2):
        return time2 - time1


    
#Set payment days for agency employees
@frappe.whitelist()
def set_payment_days(employee,from_date,to_date):
    count = 0
    attendance = frappe.get_all("Attendance",{"attendance_date":("between",(from_date,to_date)),"docstatus":1,"employee":employee},["status","leave_type"])
    for i in attendance:
        if i.status == "Present":
            count +=1
        elif i.status =="Half Day" and not i.leave_type:
            count +=0.5
        elif i.status == "On Leave" and not i.leave_type =="Leave Without Pay":
            count +=1
        elif i.status == "Half Day" and not i.leave_type =="Leave Without Pay":
            count +=0.5
    return count
    