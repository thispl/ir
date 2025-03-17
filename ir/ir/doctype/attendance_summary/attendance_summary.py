# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, add_days, date_diff,format_datetime
from datetime import date, timedelta, datetime, time


class AttendanceSummary(Document):
    pass

#Attendance summary showing HTML format
@frappe.whitelist()
def get_data_system(emp, from_date, to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(no_of_days)]
    emp_details = frappe.db.get_value('Employee', emp, ['employee_name', 'department'])
    data = "<table class='table table-bordered=1'>"	
    data += "<tr><td style='border: 1px solid black;background-color:#FF6347'><b><center>ID</b></center></b><td style='border: 1px solid black;background-color:#FF6347;' colspan=3><b><center>%s</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Name</b></center></b><td style='border: 1px solid black;background-color:#FF6347;' colspan=3><b><center>%s</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Dept</b></center></b><td style='border: 1px solid black;background-color:#FF6347;' colspan=2><b><center>%s</b></center></b></tr>" % (emp, emp_details[0], emp_details[1])
    data += "<tr><td style='border: 1px solid black;' colspan=11><b><center>Attendance</b></center></td><tr>"
    data += "<tr><td style='border: 1px solid black;background-color:#FF6347'><b><center>Date</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Day</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Working</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>In Time</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Out Time</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Shift</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Status</b></center></b><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Working Hours</b></center></b></td><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Extra Hours(OT)</b></center></b></td><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Late Entry Time</b></center></b></td><td style='border: 1px solid black;background-color:#FF6347;'><b><center>Early Exit Time</b></center></b></td></tr>"
    for date in dates:
        dt = datetime.strptime(date, '%Y-%m-%d')
        d = dt.strftime('%d-%b')
        day = datetime.date(dt).strftime('%a')
        if frappe.db.exists('Attendance', {'employee': emp, "attendance_date": date, 'docstatus': ('!=', '2')}):
            att = frappe.get_doc("Attendance",{'attendance_date':date,'employee':emp,'docstatus':('!=','2')})
            in_time = att.in_time 
            out_time = att.out_time 
            shift = att.shift 
            status = att.status
            leave_type= att.leave_type
            twh=att.custom_total_working_hours 
            leave_type = att.leave_type
            od = att.custom_on_duty_application
            late = att.custom_late_entry_time
            early = att.custom_early_out_time
            # early = att.custom_early_out_time
            if leave_type :
                if leave_type =="Bereavement leave":
                    leave = "BL"
                if leave_type =="Casual Leave":
                    leave = "CL"
                if leave_type =="Compensatory Off":
                    leave = "C-OFF"
                if leave_type =="Earned Leave":
                    leave = "EL"
                if leave_type =="Leave Without Pay":
                    leave = "LOP"
                if leave_type =="Marriage leave":
                    leave = "MAL"
                if leave_type =="Maternity leave":
                    leave = "MTL"
                if leave_type =="Medical Leave":
                    leave = "MDL"
                if leave_type =="Menstruation Leave":
                    leave = "MSL"
                if leave_type =="Paternity leaves":
                    leave = "PL"
                if leave_type =="Privilege Leave":
                    leave = "PVL"
                if leave_type =="Sick Leave":
                    leave = "SL"
                if leave_type =="Sabbatical Leave":
                    leave = "SBL"
            else:
                leave = "LOP"
            custom_extra_hours = att.custom_ot_hours 
            # custom_overtime_hours = att.custom_ot_hours 
            holiday = check_holiday(date ,emp)
            if holiday[0]:
                if in_time or out_time:
                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#DB2CE3'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day,holiday[0], format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', holiday[1] or '', '', custom_extra_hours or '', late or '', early or '')
                else:
                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#BD2A0F'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" %  (d,day,holiday[0],'','','',holiday[1],'','','',early or '')
            else:
                if status == "On Leave":
                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#b9597f'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "L" , format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '',leave, twh or ' ',custom_extra_hours,' ',early or '')
                elif status == "Half Day":
                    if leave_type:
                        leave_applications = frappe.db.sql("""
                        SELECT leave_type 
                        FROM `tabLeave Application` 
                            WHERE from_date=%s AND employee=%s AND status='Approved'
                        """, (date, emp), as_dict=True)
                        if len(leave_applications) > 1:
                            leave_types = []
                            leave_type_map = {
                                "Earned Leave": "EL",
                                "Compensatory Off": "COFF",
                                "Casual Leave": "CL",
                                "Sick Leave": "SL",
                                "Leave Without Pay": "LOP"
                            }
                            for leave in leave_applications:
                                leave_types.append(leave_type_map.get(leave['leave_type'], leave['leave_type']))
                            lstatus = "/".join(leave_types)
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', lstatus, twh or '',custom_extra_hours or '',late or '',early or '')
                        
                        elif leave_type and att.in_time and att.out_time:
                            if att.shift == 'G':
                                minute = 30
                            else:
                                minute = 15
                            if att.custom_assigned_shift and att.shift == att.custom_assigned_shift:
                                
                                if att.custom_total_working_hours >= timedelta(hours=4,minutes=minute):
                                    if att.custom_late_entry_time >= timedelta(hours=3):
                                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', leave + "/P", twh or '',custom_extra_hours or '',late or '',early or '')
                                    else:
                                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "P/" + leave, twh or '',custom_extra_hours or '',late or '',early or '')
                                else:
                                    if att.custom_permission_hour:
                                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "P/" + leave, twh or '',custom_extra_hours or '',late or '',early or '')
                                    else:    
                                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/" + leave, twh or '',custom_extra_hours or '',late or '',early or '')
                            else:
                                data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/" + leave, twh or '',custom_extra_hours or '',late or '',early or '')
                        elif leave_type and not att.in_time and not att.out_time:
                                data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/" + leave, twh or '',custom_extra_hours or '',late or '',early or '')
                        elif leave_type and not att.in_time or not att.out_time:
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/" + leave, twh or '',custom_extra_hours or '',late or '',early or '')
                    elif att.custom_permission_hour:
                        pr = frappe.db.get_value("Permission Request",{'docstatus':('!=','2'),"name":att.custom_attendance_permission},['session'])
                        if pr == 'Second Half':    
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/PR",twh or '',custom_extra_hours or '',late or '',early or '')
                        elif pr == 'First Half':    
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "PR/A",twh or '',custom_extra_hours or '',late or '',early or '')
                    elif att.custom_on_duty_application:
                        od = frappe.db.get_value("On Duty Application",{'docstatus':('!=','2'),"name":att.custom_on_duty_application},['from_date_session'])
                        time = frappe.db.get_value("On Duty Application",{'docstatus':('!=','2'),"name":att.custom_on_duty_application},['od_time'])
                        if time >4:
                            if od == 'Second Half':
                                if att.custom_total_working_hours >= timedelta(hours=4):
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "P/OD",twh or '',custom_extra_hours or '',late or '',early or '')
                                else:
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/OD",twh or '',custom_extra_hours or '',late or '',early or '')
                            elif od == 'First Half':
                                if att.custom_total_working_hours >= timedelta(hours=4):
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "OD/P",twh or '',custom_extra_hours or '',late or '',early or '')
                                else:
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "OD/A",twh or '',custom_extra_hours or '',late or '',early or '')
                            else:
                                data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , '', '', '',"OD/A", '',' ',' ','')
                        else:
                            if od == 'Second Half':
                                if att.custom_total_working_hours >= timedelta(hours=4):
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "P/A",twh or '',custom_extra_hours or '',late or '',early or '')
                                else:
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A",twh or '',custom_extra_hours or '',late or '',early or '')
                            elif od == 'First Half':
                                if att.custom_total_working_hours >= timedelta(hours=4):
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/P",twh or '',custom_extra_hours or '',late or '',early or '')
                                else:
                                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A",twh or '',custom_extra_hours or '',late or '',early or '')
                            else:
                                data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , '', '', '',"OD/A", '',' ',' ','')

                    else:
                        if att.late_entry:
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "A/P",twh or '',custom_extra_hours or '',late or '',early or '')
                        else:
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "P/A",twh or '',custom_extra_hours or '',late or '',early or '')
                elif status == "Present" and att.attendance_request:
                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , '', '', '',"On Duty", '',' ',' ',early or '')
                elif status == "Present" and att.custom_on_duty_application:
                    od = frappe.db.get_value("On Duty Application",{'docstatus':('!=','2'),"name":att.custom_on_duty_application},['from_date_session'])
                    if od == 'Second Half':
                         data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , '', '', '',"P/OD", '',' ',' ',early or '')
                    elif od == 'First Half':
                         data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '',"OD/P", twh or '',custom_extra_hours or '',late or '',early or '')
                    else:
                         data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , '', '', '',"OD", '',' ',' ',early or '')
                elif status == "Present" and att.custom_permission_hour:
                    pr = frappe.db.get_value("Permission Request",{'docstatus':('!=','2'),"name":att.custom_attendance_permission},['session'])
                    if pr == 'Second Half':    
                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "P/PR",twh or '',custom_extra_hours or '',late or '',early or '')
                    elif pr == 'First Half':    
                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', "PR/P",twh or '',custom_extra_hours or '',late or '',early or '')
                
                
                elif status =="Present":
                    data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', status,twh or '', custom_extra_hours or '',late or '',early or '')
                elif status =="Absent":
                    if att.custom_on_duty_application:
                        od = frappe.db.get_value("On Duty Application",{'docstatus':('!=','2'),"name":att.custom_on_duty_application},['from_date_session'])
                        if od == 'Second Half':
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '',"A/OD", '',' ',' ',early or '')
                        elif od == 'First Half':
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '',"OD/A", twh or '',custom_extra_hours or '',late or '',early or '')
                        else:
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , '', '', '',"OD", '',' ',' ','')
                    elif att.custom_attendance_permission:
                        pr = frappe.db.get_value("Permission Request",{'docstatus':('!=','2'),"name":att.custom_attendance_permission},['session'])
                        if pr == 'Second Half':
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '',"A/PR", '',' ',' ',early or '')
                        elif pr == 'First Half':
                            data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#82EB31'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W" , format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '',"PR/A", twh or '',custom_extra_hours or '',late or '',early or '')
                        
                    else:
                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#d57b64'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', status,twh or '', custom_extra_hours or '',late or '',early or '')
                else:
                    if att.custom_permission_hour :
                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#9FF60E'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', status + "/PR",twh or '',custom_extra_hours or '',late or '',early or '')
                    else:
                        data += "<tr><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;color:#6b8855'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d, day, "W", format_datetime(in_time) or '', format_datetime(out_time) or '', shift or '', status,twh or '', custom_extra_hours or '',late or '',early or '')

        else:
            holiday_list = frappe.db.get_value('Employee',{'name':emp	},'holiday_list')
            holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off, `tabHoliday`.description from `tabHoliday List` 
            left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
            doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
            status = ''
            desc = ''
            if holiday :
                if doj <= holiday[0].holiday_date:
                    if holiday[0].weekly_off == 1:
                        status = "WW"
                        desc = "Weekly Off"
                    else:
                        status = "HH"
                        desc = holiday[0].description
                else:
                    status = 'NJ'
                    desc = "Not Joined"
            if holiday:
                data += "<tr><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;color:#DB2CE3'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d,day,status,'','',"",desc,''," ","","")
            else:
                data += "<tr><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style = 'border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td><td style='border: 1px solid black;'><center>%s</center></td></tr>" % (d,day,"","","","","","","","","")
                
    data += "</table>"
    return data

def check_holiday(date,emp):
    holiday_list = frappe.db.get_value('Employee',{'name':emp},'holiday_list')
    holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off, `tabHoliday`.description from `tabHoliday List` 
    left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
    doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
    status = ''
    desc = ''
    if holiday :
        if doj <= holiday[0].holiday_date:
            if holiday[0].weekly_off == 1:
                status = "WW"
                desc = "Weekly Off"
            else:
                status = "HH"
                desc = holiday[0].description
        else:
            status = 'NJ'
            desc = "Not Joined"
    return status,desc
        

from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days,date_diff
@frappe.whitelist()
def get_from_to_dates(month,year):
    if month == 'January':
        month1 = "01"
    if month == 'February':
        month1 = "02"
    if month == 'March':
        month1 = "03"
    if month == 'April':
        month1 = "04"
    if month == 'May':
        month1 = "05"
    if month == 'June':
        month1 = "06"
    if month == 'July':
        month1 = "07"
    if month == 'August':
        month1 = "08"
    if month == 'September':
        month1 = "09"
    if month == 'October':
        month1 = "10"
    if month == 'November':
        month1 = "11"
    if month == 'December':
        month1 = "12"
    formatted_start_date = year + '-' + month1 + '-01'
    formatted_end_date = get_last_day(formatted_start_date)
    return formatted_start_date,formatted_end_date

