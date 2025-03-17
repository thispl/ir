# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import frappe
from frappe.utils.data import ceil, get_time, get_year_start
# import pandas as pd
import json
import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from datetime import datetime
from calendar import monthrange
from ir.mark_attendance import mark_wh_regularize
from ir.mark_attendance import ot_calculation_regularize
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
import requests
from datetime import date, timedelta,time
from datetime import datetime, timedelta
from frappe.utils import get_url_to_form
import math
from ir.mark_attendance import update_att_with_employee_regularize
import dateutil.relativedelta
import datetime as dt
from datetime import datetime, timedelta

class Regularize(Document):
    def validate(self):
        if self.holiday == 1:
            holiday_list = frappe.db.get_value('Company','Industrias Del Recambio India Private Limited','default_holiday_list')
            holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off from `tabHoliday List` 
            left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,self.attendance_date),as_dict=True)
            if holiday:
                if holiday[0].weekly_off == 1:
                    frappe.throw("Only Applicable for Holiday not in Weekoff")
            else:
                frappe.throw("Only Applicable for Holiday , not for Normal days")
        if frappe.db.exists("Regularize",{'employee':self.employee,'name':['!=',self.name],'attendance_date':self.attendance_date,'docstatus':('!=',2)}):
            frappe.throw(f"The Attendance Regularize document already exists for <b>{self.employee}</b> on <b>{self.attendance_date}</b>")
    def on_submit(self):
        if self.holiday == 1:
            if self.attendance_marked:
                frappe.db.set_value("Attendance",self.attendance_marked,'status',"Holiday")
            else:
                att = frappe.new_doc("Attendance")
                att.employee = self.employee
                att.attendance_date = self.attendance_date
                att.status = "Holiday"
                att.custom_regularize = self.name
                att.custom_regularize_marked = 1
                att.custom_late_entry_time = "00:00:00"
                att.custom_early_out_time = "00:00:00"
                att.custom_extra_hours_total = "00:00:00"
                att.custom_total_working_hours = "00:00:00"
                att.custom_ot_hours = "00:00:00"
                att.save(ignore_permissions=True)
                
        if self.attendance_marked:
            if self.shift==1:
                frappe.db.set_value("Attendance",self.attendance_marked,'shift',self.corrected_shift)
            if self.in_time==1:
                frappe.db.set_value("Attendance",self.attendance_marked,'in_time',self.corrected_in)
            if self.out_time==1:
                frappe.db.set_value("Attendance",self.attendance_marked,'out_time',self.corrected_out)
            att=frappe.get_doc("Attendance",self.attendance_marked)
            if att.in_time and att.out_time and att.shift:
                mark_wh_regularize(self.attendance_marked)
                to_date = add_days(self.attendance_date,1)
                if self.employment_type:
                    update_att_with_employee_regularize(self.attendance_date, to_date, self.employee)
                if self.over_time ==1 and self.corrected_ot:
                    ftr = [3600,60,1]
                    hr = sum([a*b for a,b in zip(ftr, map(int,str(self.corrected_ot).split(':')))])
                    ot_hr = round(hr/3600,1) 
                    frappe.db.set_value("Attendance",self.attendance_marked,'custom_ot_hours',self.corrected_ot)
                    frappe.db.set_value("Attendance",self.attendance_marked,'custom_over_time_hours',ot_hr)
                else:
                    ot_calculation_regularize(self.attendance_marked)
            
            frappe.db.set_value("Attendance",self.attendance_marked,'custom_regularize',self.name)
            frappe.db.set_value("Attendance",self.attendance_marked,'custom_regularize_marked',True)
            if self.over_time ==1 and self.corrected_ot:
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

    def on_cancel(self):
        attendance_obj = frappe.get_doc("Attendance", self.attendance_marked)
        if attendance_obj.docstatus ==1:
            attendance_obj.cancel()
            to_date = add_days(self.attendance_date,1)
            update_att_with_employee_regularize(self.attendance_date, to_date, self.employee)
        if attendance_obj.docstatus ==0:
            frappe.db.sql(""" Update  `tabAttendance` Set custom_regularize = "" , custom_regularize_marked = 0 WHERE name = %s""", (attendance_obj.name,), as_dict=True)
            to_date = add_days(self.attendance_date,1)
            frappe.db.set_value("Attendance",attendance_obj.name,'in_time',None)
            frappe.db.set_value("Attendance",attendance_obj.name,'out_time',None)
            frappe.db.set_value("Attendance",attendance_obj.name,'status','Absent')
            # attendance_obj.save(ignore_permissions=True)
            update_att_with_employee_regularize(self.attendance_date, to_date, self.employee)
        

@frappe.whitelist()
def get_assigned_shift_details(emp, att_date):
    datalist = []  
    assigned_shift = frappe.get_value("Employee", {'name': emp}, ['default_shift'])
    if assigned_shift:
        shift_in_time = frappe.db.get_value('Shift Type', {'name': assigned_shift}, ['start_time'])
        shift_out_time = frappe.db.get_value('Shift Type', {'name': assigned_shift}, ['end_time'])
    else:
        shift_in_time = ''
        shift_out_time = ''
    if frappe.db.exists('Attendance', {'employee': emp, 'attendance_date': att_date, 'docstatus': ("!=", 2)}):
        att_name = frappe.db.get_value('Attendance', {'employee': emp, 'attendance_date': att_date, 'docstatus': ("!=", 2)}, ['name'])
        att = frappe.get_doc('Attendance', att_name)
        data ={
            'assigned_shift': assigned_shift or '',
            'shift_in_time': shift_in_time or '00:00:00',
            'shift_out_time': shift_out_time or '00:00:00',
            'attendance_shift': att.shift or '',
            'first_in_time': att.in_time or '',
            'last_out_time': att.out_time or '',
            'attendance_marked': att.name,
            'ot_hrs': att.custom_ot_hours
        }
        datalist.append(data)
        return datalist

    else:
        frappe.throw(_("Attendance not Marked"))

@frappe.whitelist()
def validate_regularize_duplication(employee,att_date,name=None):
    exisiting=frappe.db.exists("Regularize",{'employee':employee,'name':['!=',name],'attendance_date':att_date,'docstatus':('!=',2)})
    if exisiting:
        return "Already Applied"