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
# from __future__ import unicode_literals
from time import gmtime
import frappe
from frappe.model import workflow
from frappe.utils import cstr, add_days, date_diff, getdate
from frappe import _
from frappe.utils.csvutils import UnicodeWriter, read_csv_content
from frappe.utils.file_manager import get_file
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form, format_date



@frappe.whitelist()
def absent_mail_alert():
	yesterday = add_days(frappe.utils.today(), -1)
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
			</tr>
	"""

	idx = 1  # Initialize serial number
	for att in attendance:
		staff += """
		<tr style="border: 1px solid black;">
			<td style="padding: 4px; border: 1px solid black;">{0}</td>
			<td style="padding: 4px; border: 1px solid black;">{1}</td>
			<td style="padding: 4px; border: 1px solid black;">{2}</td>
			<td style="padding: 4px; border: 1px solid black;">{3}</td>
			<td style="padding: 4px; border: 1px solid black;">{4}</td>
		</tr>
		""".format(idx, att.employee, att.employee_name, att.department, att.name or ' ')
		idx += 1  # Increment serial number

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
			# recipients=['siva.m@groupteampro.com','sivarenisha.m@groupteampro.com'],
			recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com'],
			subject='Absent Report',
			message="""Dear Sir,<br><br>
				Kindly find the attached Employee Absent Employee List for yesterday:<br>{0}
				""".format(staff)
		)

  
@frappe.whitelist()
def cron_job_absent():
	job = frappe.db.exists('Scheduled Job Type', 'absent_mail_alert')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.absent_mail_alert',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def leave_report():
	yesterday = add_days(frappe.utils.today(), -1)
	leave = frappe.db.sql("""
		SELECT * FROM `tabLeave Application`
		WHERE from_date = %s AND docstatus = 1
		ORDER BY employee
	""", (yesterday,), as_dict=True)
	
	staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">Leave Report</h2>
		</div>
		<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
			<tr style="border: 1px solid black;">
				<th style="padding: 4px; border: 1px solid black;">S.NO</th>
				<th style="padding: 4px; border: 1px solid black;">Employee</th>
				<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
				<th style="padding: 4px; border: 1px solid black;">Department</th>
				<th style="padding: 4px; border: 1px solid black;">Leave</th>
				<th style="padding: 4px; border: 1px solid black;">Leave Type</th>
			</tr>
	"""
	
	idx = 1  # Initialize serial number
	for lve in leave:
		staff += """
		<tr style="border: 1px solid black;">
			<td style="padding: 4px; border: 1px solid black;">{0}</td>
			<td style="padding: 4px; border: 1px solid black;">{1}</td>
			<td style="padding: 4px; border: 1px solid black;">{2}</td>
			<td style="padding: 4px; border: 1px solid black;">{3}</td>
			<td style="padding: 4px; border: 1px solid black;">{4}</td>
			<td style="padding: 4px; border: 1px solid black;">{5}</td>
		</tr>
		""".format(idx, lve.employee, lve.employee_name, lve.department,
				   lve.name or ' ', lve.leave_type or '')
		idx += 1  # Increment serial number

	staff += "</table>"

	user = frappe.db.sql("""
		SELECT `tabUser`.name as name
		FROM `tabUser`
		LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
		WHERE `tabHas Role`.Role = "HR User" AND `tabUser`.enabled = 1
	""", as_dict=True)

	if leave:
		for i in user:
			frappe.sendmail(
				recipients=[i.name],
				subject='Leave Report',
				message="""Dear Sir/Mam,<br><br>
					Kindly Check the Leave Employee List for yesterday ({1}):<br>{0}
				""".format(staff, format_date(yesterday))
			)
		frappe.sendmail(
			# recipients=['siva.m@groupteampro.com','sivarenisha.m@groupteampro.com'],
			recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
			subject='Leave Application Report',
			message="""Dear Sir,<br><br>
				Kindly find the attached Employee Leave Application List for yesterday:<br>{0}
			""".format(staff)
		)

  
@frappe.whitelist()
def cron_job_leave():
	job = frappe.db.exists('Scheduled Job Type', 'leave_report')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.leave_report',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def od_report():
	yesterday = add_days(frappe.utils.today(), -1)
	employee = frappe.db.sql("""
		SELECT `tabMulti Employee`.employee_id, `tabMulti Employee`.employee_name, 
		       `tabOn Duty Application`.department, `tabOn Duty Application`.name,
		       `tabOn Duty Application`.from_date_session
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
				<th style="padding: 4px; border: 1px solid black;">S.NO</th>
				<th style="padding: 4px; border: 1px solid black;">Employee</th>
				<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
				<th style="padding: 4px; border: 1px solid black;">Department</th>
				<th style="padding: 4px; border: 1px solid black;">On Duty</th>
				<th style="padding: 4px; border: 1px solid black;">Session</th>
			</tr>
	"""
	
	idx = 1  # Initialize serial number
	for i in employee:
		staff += """
		<tr style="border: 1px solid black;">
			<td style="padding: 4px; border: 1px solid black;">{0}</td>
			<td style="padding: 4px; border: 1px solid black;">{1}</td>
			<td style="padding: 4px; border: 1px solid black;">{2}</td>
			<td style="padding: 4px; border: 1px solid black;">{3}</td>
			<td style="padding: 4px; border: 1px solid black;">{4}</td>
			<td style="padding: 4px; border: 1px solid black;">{5}</td>
		</tr>
		""".format(idx, i.employee_id, i.employee_name, i.department, i.name or ' ', i.from_date_session or '')
		idx += 1  # Increment serial number
	
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
				message="""Dear Sir/Mam,<br><br>
					Kindly Check the On Duty Employee List for yesterday ({1}):<br>{0}
				""".format(staff, format_date(yesterday))
			)
		frappe.sendmail(
			recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com'],
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
			"method": 'ir.email_alerts.od_report',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def permission_request_report():
    yesterday = add_days(frappe.utils.today(), -1)
    permission = frappe.db.sql("""
        SELECT * FROM `tabPermission Request`
        WHERE attendance_date = %s AND docstatus=1
        ORDER BY employee
    """, (yesterday,), as_dict=True)
    
    staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">Permission Request Report</h2>
        </div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
            <tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.NO</th>
                <th style="padding: 4px; border: 1px solid black;">Employee</th>
                <th style="padding: 4px; border: 1px solid black;">Employee Name</th>
                <th style="padding: 4px; border: 1px solid black;">Permission Request</th>
                <th style="padding: 4px; border: 1px solid black;">Session</th>
            </tr>
    """
    
    idx = 1  # Initialize serial number
    for per in permission:
        staff += """
        <tr style="border: 1px solid black;">
            <td style="padding: 4px; border: 1px solid black;">{0}</td>
            <td style="padding: 4px; border: 1px solid black;">{1}</td>
            <td style="padding: 4px; border: 1px solid black;">{2}</td>
            <td style="padding: 4px; border: 1px solid black;">{3}</td>
            <td style="padding: 4px; border: 1px solid black;">{4}</td>
        </tr>
        """.format(idx, per.employee, per.employee_name, per.name or ' ', per.session or '')
        idx += 1  # Increment serial number
    
    staff += "</table>"
    
    user = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.Role="HR User" AND `tabUser`.enabled=1
    """, as_dict=True)
    
    if permission:
        for i in user:
            frappe.sendmail(
                recipients=[i.name],
                subject='Permission Request Report',
                message="""Dear Sir/Mam,<br><br>
                    Kindly Check the Permission Request Employee List for yesterday ({1}):<br>{0}
                """.format(staff, format_date(yesterday))
            )
        frappe.sendmail(
            recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
            subject='Permission Request Report',
            message="""Dear Sir,<br><br>
                Kindly find the attached Employee Permission Request List for yesterday:<br>{0}
            """.format(staff)
        )

  
@frappe.whitelist()
def cron_job_permission():
	job = frappe.db.exists('Scheduled Job Type', 'permission_request_report')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.permission_request_report',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def permission_request_firstmanager():
	
	permission_requests = frappe.db.sql("""
		SELECT name, employee, employee_name, session, custom_first_manager
		FROM `tabPermission Request`
		WHERE workflow_state="FM Pending"
		ORDER BY employee
	""", as_dict=True)

	if permission_requests:
		
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
						<th style="padding: 4px; border: 1px solid black;">Employee</th>
						<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
						<th style="padding: 4px; border: 1px solid black;">Permission Request</th>
						<th style="padding: 4px; border: 1px solid black;">Session</th>
					</tr>
				"""

				for per in requests:
					staff += """
					<tr style="border: 1px solid black;">
						<td style="padding: 4px; border: 1px solid black;">{0}</td>
						<td style="padding: 4px; border: 1px solid black;">{1}</td>
						<td style="padding: 4px; border: 1px solid black;">{2}</td>
						<td style="padding: 4px; border: 1px solid black;">{3}</td>
					</tr>
					""".format(per.employee, per.employee_name, per.name or ' ', per.session or '')

				staff += "</table>"

				
				frappe.sendmail(
					recipients=[manager],
					subject='Permission Request Report',
					message="""Dear Sir/Madam,<br><br>
					Kindly find the list of Permission Requests waiting for your approval:<br>{0}
					""".format(staff)
				)

		frappe.sendmail(
				recipients=['siva.m@groupteampro.com','arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
				# recipients=['siva.m@groupteampro.com','sivarenisha.m@groupteampro.com'],
				subject='Permission Request Report',
				message="""Dear Sir,<br><br>
						Kindly Find the list of Permission Request waiting for your Approval:<br>{0}
						""".format(staff)
			)
  
@frappe.whitelist()
def cron_job_perfm():
	job = frappe.db.exists('Scheduled Job Type', 'permission_request_firstmanager')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.permission_request_firstmanager',
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

	if permission_requests:
		
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
						<th style="padding: 4px; border: 1px solid black;">Employee</th>
						<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
						<th style="padding: 4px; border: 1px solid black;">Permission Request</th>
						<th style="padding: 4px; border: 1px solid black;">Session</th>
					</tr>
				"""

				for per in requests:
					staff += """
					<tr style="border: 1px solid black;">
						<td style="padding: 4px; border: 1px solid black;">{0}</td>
						<td style="padding: 4px; border: 1px solid black;">{1}</td>
						<td style="padding: 4px; border: 1px solid black;">{2}</td>
						<td style="padding: 4px; border: 1px solid black;">{3}</td>
					</tr>
					""".format(per.employee, per.employee_name, per.name or ' ', per.session or '')

				staff += "</table>"

				
				frappe.sendmail(
					recipients=[manager],
					subject='Permission Request Report',
					message="""Dear Sir/Madam,<br><br>
					Kindly find the list of Permission Requests waiting for your approval:<br>{0}
					""".format(staff)
				)

		frappe.sendmail(
				recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com','siva.m@groupteampro.com'],
					# recipients=['siva.m@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
				subject='Permission Request Report',
				message="""Dear Sir,<br><br>
						Kindly Find the list of Permission Request for your Approval:<br>{0}
						""".format(staff)
			)
  
@frappe.whitelist()
def cron_job_persm():
	job = frappe.db.exists('Scheduled Job Type', 'permission_request_secondmanager')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.permission_request_secondmanager',
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
				staff = """
				<div style="text-align: center;">
					<h2 style="font-size: 16px;">Leave Application Report</h2>
				</div>
				<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
					<tr style="border: 1px solid black;">
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
					</tr>
					""".format(lve.employee, lve.employee_name, lve.name or ' ', lve.leave_type or '')

				staff += "</table>"

				
				frappe.sendmail(
					recipients=[manager],
					subject='Leave Application Report',
					message="""Dear Sir/Madam,<br><br>
					Kindly find the list of Leave Applications waiting for your approval:<br>{0}
					""".format(staff)
				)

	   
		frappe.sendmail(
			recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com'],
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
			"method": 'ir.email_alerts.leave_application_secondmanager_test',
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

		
		for manager, applications in managers_leaves.items():
			if manager:  
				staff = """
				<div style="text-align: center;">
					<h2 style="font-size: 16px;">Leave Application Report</h2>
				</div>
				<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
					<tr style="border: 1px solid black;">
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
					</tr>
					""".format(lve.employee, lve.employee_name, lve.name or ' ', lve.leave_type or '')

				staff += "</table>"

				
			frappe.sendmail(
				recipients=[manager],
				subject='Leave Application Report',
				message="""Dear Sir/Madam,<br><br>
				Kindly find the list of Leave Applications waiting for your approval:<br>{0}
				""".format(staff)
			)

	   
		frappe.sendmail(
			recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com'],
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
			"method": 'ir.email_alerts.leave_application_firstmanager_test',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def leave_application_hod_format():
	
	leave = frappe.db.sql("""
		SELECT name, employee, employee_name, department, leave_type
		FROM `tabLeave Application`
		WHERE workflow_state = 'HR Pending'
		ORDER BY employee
	""", as_dict=True)
	
	if not leave:
		return "No leave applications are currently pending approval."
	idx = 1
	
	staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">Leave Application Report</h2>
		</div>
		<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
			<tr style="border: 1px solid black;">
				<th style="padding: 4px; border: 1px solid black;">Employee</th>
				<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
				<th style="padding: 4px; border: 1px solid black;">Department</th>
				<th style="padding: 4px; border: 1px solid black;">Document ID</th>
    			<th style="padding: 4px; border: 1px solid black;">From Date</th>
				<th style="padding: 4px; border: 1px solid black;">To Date</th>
				<th style="padding: 4px; border: 1px solid black;">Leave Type</th>
			</tr>
	"""
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
		""".format(idx, lve.employee, lve.employee_name, lve.department, lve.name or ' ',lve.from_date,lve.to_date, lve.leave_type or '')
		idx += 1
	staff += "</table>"
	
	
	hr_users = frappe.db.sql("""
		SELECT `tabUser`.name as name
		FROM `tabUser`
		LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
		WHERE `tabHas Role`.role = 'HR User' AND `tabUser`.enabled = 1
	""", as_dict=True)

   
	for user in hr_users:
		frappe.sendmail(
			recipients=[user.name],
			subject='Leave Application Report - HR Pending',
			message="""Dear Sir/Madam,<br><br>
				Kindly find the list of leave applications waiting for your approval:<br>{0}
			""".format(staff)
		)
	
	
	frappe.sendmail(
		recipients=['siva.m@groupteampro.com', 'sivarenisha.m@groupteampro.com'],
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
			"method": 'ir.email_alerts.leave_application_hod_format',
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
				recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
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
			"method": 'ir.email_alerts.od_hod',
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
				recipients=['arockia.k@groupteampro.com', 'sivarenisha.m@groupteampro.com', 'anil.p@groupteampro.com'],
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
				recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','anil.p@groupteampro.com'],
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
			"method": 'ir.email_alerts.od_secondmanager',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def ot_hours_mail_alert():
    yesterday = add_days(frappe.utils.today(), -1)
    attendance = frappe.db.sql("""
        SELECT * FROM tabAttendance
        WHERE attendance_date = %s AND docstatus != 2
        order by employee
    """, (yesterday,), as_dict=True)
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
    no_ot = True
    serial_number = 1  # Initialize serial number
    for att in attendance:
        if att.custom_ot_hours:
            no_ot = False
            staff += """
            <tr style="border: 1px solid black;">
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{0}</td>
                <td style="padding: 4px; border: 1px solid black;">{1}</td>
                <td style="padding: 4px; border: 1px solid black;">{2}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{3}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{4}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{5}</td>
                <td style="padding: 4px; border: 1px solid black; text-align: center;">{6}</td>
            </tr>
            """.format(serial_number, att.employee, att.employee_name, att.department,
                       format_date(att.attendance_date) or ' ', att.custom_ot_hours or ' ',
                       att.shift or ' ')
            serial_number += 1  # Increment serial number for each row
    if no_ot:
        staff = """
        <div style="text-align: center;">
            <h2 style="font-size: 16px;">No OT hours for yesterday.</h2>
        </div>
        """
    else:
        staff += "</table>"
    user = frappe.db.sql("""
        SELECT `tabUser`.name as name
        FROM `tabUser`
        LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name 
        WHERE `tabHas Role`.Role="HOD" AND `tabUser`.enabled=1
    """, as_dict=True)
    if attendance:
        for i in user:
            frappe.sendmail(
                recipients=[i.name],
                subject='OT Hours Report',
                message="""Dear Sir,<br><br>
                        Kindly find the attached Employee OT Hours List for yesterday:<br>{0}
                        """.format(staff)
            )    
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
			"method": 'ir.email_alerts.ot_hours_mail_alert',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def late_entry_mail_alert():
	yesterday = add_days(frappe.utils.today(), -1)
	attendance = frappe.db.sql("""
		SELECT * FROM tabAttendance
		WHERE attendance_date = %s AND docstatus != 2
		ORDER BY employee
	""", (yesterday,), as_dict=True)

	staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">Late Entry Report</h2>
		</div>
		<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
			<tr style="border: 1px solid black;">
                <th style="padding: 4px; border: 1px solid black;">S.NO</th>
				<th style="padding: 4px; border: 1px solid black;">Employee</th>
				<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
				<th style="padding: 4px; border: 1px solid black;">Department</th>
				<th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
				<th style="padding: 4px; border: 1px solid black;">Late Entry Time</th>
				<th style="padding: 4px; border: 1px solid black;">Shift</th>
			</tr>
	"""

	idx = 1
	for att in attendance:
		if att.custom_late_entry_time:
			dt = datetime.strptime(str(att.custom_late_entry_time), "%H:%M:%S")
			
			late_entry_minutes = dt.hour * 60 + dt.minute

			# Filter only if late entry is 1 minute or more
			if late_entry_minutes >= 1:
				time_string_no_ms = dt.strftime("%H:%M:%S")
				staff += """
				<tr style="border: 1px solid black;">
	                <td style="padding: 4px; border: 1px solid black;">{0}</td>
					<td style="padding: 4px; border: 1px solid black;">{1}</td>
					<td style="padding: 4px; border: 1px solid black;">{2}</td>
					<td style="padding: 4px; border: 1px solid black;">{3}</td>
					<td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
					<td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
					<td style="padding: 4px; border: 1px solid black;text-align: center;">{6}</td>
				</tr>
				""".format(idx, att.employee, att.employee_name, att.department,
						format_date(att.attendance_date) or ' ', time_string_no_ms or ' ',
							att.shift or ' ')
				idx += 1  # Increment serial number

	staff += "</table>"
 
	if attendance:	
		frappe.sendmail(
                # recipients='siva.m@groupteampro.com',
				recipients=['arockia.k@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com', 'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com', 'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com'],
				subject='Late Entry Report',
				message="""Dear Sir,<br><br>
						Kindly find the attached Employee Late Entry List for yesterday:<br>{0}
						""".format(staff)
			)
  
@frappe.whitelist()
def cron_late_entry():
	job = frappe.db.exists('Scheduled Job Type', 'late_entry_mail_alert')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.late_entry_mail_alert',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)

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
	'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'
	]

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

	departments = frappe.db.sql("""
		SELECT DISTINCT department
		FROM `tabAttendance`
		WHERE attendance_date = %s
		AND docstatus != 2
	""", (yesterday), as_dict=True)

	tot1 = tot2 = tot3 = tot4 = tot5 = tot6 = tot7 = tot8 = 0
	s_no = 1

	for dept in departments:
		department = dept.department
		shift1_data = frappe.db.sql("""
			SELECT COUNT(status) AS shift1_count, SUM(custom_ot_hours) AS shift1_overtime
			FROM `tabAttendance`
			WHERE attendance_date = %s
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
			WHERE attendance_date = %s
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
			WHERE attendance_date = %s
			AND docstatus != 2
			AND in_time IS NOT NULL
			AND department = %s 
			AND shift = 'G'
		""", (yesterday, department), as_dict=True)

		shiftg_count = shiftg_data[0].shiftg_count if shiftg_data and shiftg_data[0].shiftg_count is not None else 0
		shiftg_overtime = shiftg_data[0].shiftg_overtime if shiftg_data and shiftg_data[0].shiftg_overtime is not None else 0.0
		shiftg_overtime_hours = flt(shiftg_overtime) / 10000

		total_over_time = flt(shift1_overtime_hours) + flt(shift2_overtime_hours) + flt(shiftg_overtime_hours)
		total_count = shift1_count + shift2_count + shiftg_count
		if flt(shift1_count) or flt(shift2_count) or flt(shiftg_count):
			data.append([
				s_no,
				department,
				shift1_count,
				shift2_count,
				shiftg_count,
				total_count,
				shift1_overtime_hours,
				shift2_overtime_hours,
				shiftg_overtime_hours,
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
			"method": 'ir.email_alerts.head_count_mail_alert',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def miss_punch_mail_alert():
	yesterday = add_days(frappe.utils.today(), -1)
	attendance = frappe.db.sql("""
		SELECT * FROM `tabAttendance`
		WHERE attendance_date = %s AND docstatus != 2
		ORDER BY employee
	""", (yesterday,), as_dict=True)
	
	staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">Miss Punch Report</h2>
		</div>
		<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
			<tr style="border: 1px solid black;">
				<th style="padding: 4px; border: 1px solid black;">S.NO</th>
				<th style="padding: 4px; border: 1px solid black;">Employee</th>
				<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
				<th style="padding: 4px; border: 1px solid black;">Department</th>
				<th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
				<th style="padding: 4px; border: 1px solid black;">In Time</th>
				<th style="padding: 4px; border: 1px solid black;">Out Time</th>
				<th style="padding: 4px; border: 1px solid black;">Shift</th>
			</tr>
	"""

	idx = 1  # Initialize serial number
	no_punches = True
	for att in attendance:
		if att.in_time and not att.out_time:
			no_punches = False
			staff += """
			<tr style="border: 1px solid black;">
				<td style="padding: 4px; border: 1px solid black;">{0}</td>
				<td style="padding: 4px; border: 1px solid black;">{1}</td>
				<td style="padding: 4px; border: 1px solid black;">{2}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{3}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{6}</td>
			</tr>
			""".format(idx, att.employee, att.employee_name, att.department,
					format_date(att.attendance_date) or ' ', format_datetime(att.in_time) or ' ',
					format_datetime(att.out_time) or ' ', att.shift or ' ')
			idx += 1  # Increment serial number
		elif not att.in_time and att.out_time:
			no_punches = False
			staff += """
			<tr style="border: 1px solid black;">
				<td style="padding: 4px; border: 1px solid black;">{0}</td>
				<td style="padding: 4px; border: 1px solid black;">{1}</td>
				<td style="padding: 4px; border: 1px solid black;">{2}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{3}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
				<td style="padding: 4px; border: 1px solid black;text-align: center;">{6}</td>
			</tr>
			""".format(idx, att.employee, att.employee_name, att.department,
					format_date(att.attendance_date) or ' ', format_datetime(att.in_time) or ' ',
					format_datetime(att.out_time) or ' ', att.shift or ' ')
			idx += 1  # Increment serial number

	if no_punches:
		staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">No missed punch for yesterday.</h2>
		</div>
		"""
	else:
		staff += "</table>"

	# For Testing
	# recipients = ['amar.p@groupteampro.com']
	recipients = ['amar.p@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com',
	'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com',
	'anil.p@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'
	]

	frappe.sendmail(
		recipients=recipients,
		subject='Miss Punch Report',
		message="""Dear Sir,<br><br>
				Kindly find the attached Employee Miss Punch List for yesterday:<br>{0}
				""".format(staff)
	)

 
@frappe.whitelist()
def cron_job_miss_punch():
	job = frappe.db.exists('Scheduled Job Type', 'miss_punch_mail_alert')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.miss_punch_mail_alert',
			"frequency": 'Cron',
			"cron_format": '0 8 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def late_entry_mail_alert_for_2_shift():
	yesterday = frappe.utils.today()
	attendance = frappe.db.sql("""
		SELECT * FROM tabAttendance
		WHERE attendance_date = %s AND shift = '2' AND docstatus != 2 AND late_entry = 1
		order by employee
	""", (yesterday), as_dict=True)
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
	for att in attendance:
		if att.custom_late_entry_time:
			dt = str(att.custom_late_entry_time)
			if '.' in dt:
				dt = dt.split('.')[0]
			print(dt)
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
					format_date(att.attendance_date) or ' ',dt or ' ',
						att.shift or ' ')
	staff += "</table>"
	if attendance:	
		frappe.sendmail(
				recipients = ['amar.p@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com',
								'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'
							],
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
			"method": 'ir.email_alerts.late_entry_mail_alert_for_2_shift',
			"frequency": 'Cron',
			"cron_format": '0 18 * * *'
		})
		att.save(ignore_permissions=True)
  
@frappe.whitelist()
def late_entry_mail_alert_for_G_shift():
	yesterday = frappe.utils.today()
	attendance = frappe.db.sql("""
		SELECT * FROM tabAttendance
		WHERE attendance_date = %s AND (shift = '1' OR shift = 'G') AND docstatus != 2 AND late_entry = 1
		order by employee
	""", (yesterday), as_dict=True)
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
	for att in attendance:
		if att.custom_late_entry_time:
			dt = str(att.custom_late_entry_time)
			if '.' in dt:
				dt = dt.split('.')[0]
			print(dt)
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
					format_date(att.attendance_date) or ' ',dt or ' ',
						att.shift or ' ')
	staff += "</table>"
	if attendance:	
		frappe.sendmail(
				# recipients = ['amar.p@groupteampro.com', 'jenisha.p@groupteampro.com'],
				recipients = ['amar.p@groupteampro.com', 'dilek.ulu@irecambioindia.com', 'hr@irecambioindia.com',
								'prabakar@irecambioindia.com', 'deepak.krishnamoorthy@irecambioindia.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com'
							],
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
			"method": 'ir.email_alerts.late_entry_mail_alert_for_G_shift',
			"frequency": 'Cron',
			"cron_format": '30 08 * * *'
		})
		att.save(ignore_permissions=True)
 
@frappe.whitelist() 
def after_insert(doc,method):
        if doc.workflow_state == 'Pending for HOD':
            table = ''
            link = get_url_to_form("On Duty Application", doc.name)
            content="""<p>Dear Sir,<br>Kindly find the below On Duty Application from %s (%s).</p><br>"""%(doc.employee,doc.employee_name)
            for idx,emp in enumerate(doc.multi_employee):
                header = """<table class=table table-bordered><tr><td style = 'border: 1px solid black'>Serial No</td><th colspan='7' style = 'border: 1px solid black;background-color:#ffedcc;'><center>On Duty Application</center></th><tr>"""
                table += """<tr><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Employee ID</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Employee Name</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Department</th><td style = 'border: 1px solid black'>%s</td></tr>
                """%(idx+1,emp.employee_id,emp.employee_name,emp.department)
            data = """ </table><br><table class=table table-bordered><th colspan='6' style = 'border: 1px solid black;background-color:#ffedcc;'><center>On Duty Application Details</center></th><tr>
            <tr><th style = 'border: 1px solid black'>From Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Date</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>From Time</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Time</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th style = 'border: 1px solid black'>Total Number of Days</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Session</th><td style = 'border: 1px solid black'>%s</td></tr>
            <tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
            </table><br>"""%(format_datetime(doc.from_date),format_datetime(doc.to_date),format_datetime(doc.from_time),format_datetime(doc.to_time),doc.total_number_of_days,doc.from_date_session,link)
            regards = "Thanks & Regards,<br>ir"
            frappe.sendmail(
            recipients=[doc.approver],
            subject='Reg.On Duty Application Approval' ,
            message = content+header+table+data+regards)

@frappe.whitelist()             
def after_inserts(doc,method):
		if doc.workflow_state == 'Pending for HOD':
			link = get_url_to_form("Permission Request", doc.name)
			content="""<p>Dear Sir,</p>
			Kindly find the below Permission Request from %s (%s).<br>"""%(doc.employee,doc.employee_name)
			table = """<table class=table table-bordered><tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center>PERMISSION REQUEST</center></th><tr>
			<tr><th style = 'border: 1px solid black'>Employee ID</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Department</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th style = 'border: 1px solid black'>Employee Name</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Designation</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th style = 'border: 1px solid black'>Permission Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>Session</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th style = 'border: 1px solid black'>Shift</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>From Time</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th rowspan='2' style = 'border: 1px solid black'>Reason</th><td rowspan='2' style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Time</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th style = 'border: 1px solid black'>Hours</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
			</table><br>"""%(doc.employee,doc.department,doc.employee_name,doc.designation,format_datetime(doc.attendance_date),doc.session,doc.shift,doc.from_time,doc.reason,doc.to_time,doc.hours,link)
			regards = "Thanks & Regards,<br>hrPRO"
			frappe.sendmail(
			recipients=[doc.permission_approver],
			subject='Reg.Permission Request Approval' ,
			message = content+table+regards)


@frappe.whitelist()
def after_insert_shift_approval(doc,method):
		if doc.workflow_state == 'Pending for HOD':
			link = get_url_to_form("Shift Schedule", doc.name)
			filepath = get_file(doc.upload)
			pps = read_csv_content(filepath[1])
			data = ''
			# wc1,wc2,wc3,wcpp1,wcpp2,bc1,bc2,bc3,bcpp1,bcpp2,ft1,ft2,ft3,ftpp1,ftpp2,nt1,nt2,nt3,ntpp1,ntpp2,cl1,cl2,cl3,clpp1,clpp2 =0
			wc1 = 0
			wc2 = 0
			wc3 = 0
			wcpp1 = 0
			wcpp2 = 0
			bc1 = 0
			bc2 = 0
			bc3 = 0
			bcpp1 = 0
			bcpp2 = 0
			ft1 = 0
			ft2 = 0
			ft3 = 0
			ftpp1 = 0
			ftpp2 = 0
			nt1 = 0
			nt2 = 0
			nt3 = 0
			ntpp1 = 0
			ntpp2 = 0
			cl1 = 0
			cl2 = 0
			cl3 = 0
			clpp1 = 0
			clpp2 =0
			for pp in pps:
				if pp[4] == 'WC':
					if pp[4] == "1":
						wc1 +=1
					elif pp[4] == "2":
						wc2 +=1
					elif pp[4] == "3":
						wc3 +=1
					elif pp[4] == "PP1":
						wcpp1 +=1
					elif pp[4] == "PP2":
						wcpp2 +=1
				if pp[4] == 'BC':
					if pp[4] == "1":
						bc1 +=1
					elif pp[4] == "2":
						bc2 +=1
					elif pp[4] == "3":
						bc3 +=1
					elif pp[4] == "PP1":
						bcpp1 +=1
					elif pp[4] == "PP2":
						bcpp2 +=1
				if pp[4] == 'FT':
					if pp[4] == "1":
						ft1 +=1
					elif pp[4] == "2":
						ft2 +=1
					elif pp[4] == "3":
						ft3 +=1
					elif pp[4] == "PP1":
						ftpp1 +=1
					elif pp[4] == "PP2":
						ftpp2 +=1
				if pp[4] == 'NT':
					if pp[4] == "1":
						nt1 +=1
					elif pp[4] == "2":
						nt2 +=1
					elif pp[4] == "3":
						nt3 +=1
					elif pp[4] == "PP1":
						ntpp1 +=1
					elif pp[4] == "PP2":
						ntpp2 +=1
				if pp[4] == 'CL':
					if pp[4] == "1":
						cl1 +=1
					elif pp[4] == "2":
						cl2 +=1
					elif pp[4] == "3":
						cl3 +=1
					elif pp[4] == "PP1":
						clpp1 +=1
					elif pp[4] == "PP2":
						clpp2 +=1
			total = wc1+wc2+wc3+wcpp1+wcpp2+bc1+bc2+bc3+bcpp1+bcpp2+ft1+ft2+ft3+ftpp1+ftpp2+nt1+nt2+nt3+ntpp1+ntpp2+cl1+cl2+cl3+clpp1+clpp2
			data += """ <table class=table table-bordered>
				<tr><th colspan='7' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule Summary</center></th><tr>
				<tr><td style="background-color:#f0b27a; border: 1px solid black">Shift</td><td style="background-color:#f0b27a ; border: 1px solid black">1</td><td style="background-color:#f0b27a; border: 1px solid black">2</td><td style="background-color:#f0b27a; border: 1px solid black">3</td><td style="background-color:#f0b27a; border: 1px solid black">PP1</td><td style="background-color:#f0b27a; border: 1px solid black">PP2</td><td style="background-color:#f0b27a ; border: 1px solid black">Total</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>WC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>BC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>FT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>NT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>CL</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<td style="background-color:#58d68d; border: 1px solid black">Total</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr></table>"""%(wc1,wc2,wc3,wcpp1,wcpp2,(wc1+wc2+wc3+wcpp1+wcpp2),bc1,bc2,bc3,bcpp1,bcpp2,(bc1+bc2+bc3+bcpp1+bcpp2),ft1,ft2,ft3,ftpp1,ftpp2,(ft1+ft2+ft3+ftpp1+ftpp2),nt1,nt2,nt3,ntpp1,ntpp2,(nt1+nt2+nt3+ntpp1+ntpp2),cl1,cl2,cl3,clpp1,clpp2,(cl1+cl2+cl3+clpp1+clpp2),(wc1+bc1+ft1+nt1+cl1),(wc2+bc2+ft2+nt2+cl2),(wc3+bc3+ft3+nt3+cl3),(wcpp1+bcpp1+ftpp1+ntpp1+clpp1),(wcpp2+bcpp2+ftpp2+ntpp2+clpp2),total)

			content="""<p>Dear Sir,</p>
			Kindly find the below Shift Schedule Request<br>"""
			table = """<table class=table table-bordered><tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule</center></th><tr>
			<tr><th colspan='2' style = 'border: 1px solid black'>Department</th><td colspan='2' style = 'border: 1px solid black'>%s</td></tr>
			<tr><th style = 'border: 1px solid black'>From Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Date</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
			</table><br>"""%(doc.department,format_date(doc.from_date),format_date(doc.to_date),link)
			regards = "Thanks & Regards,<br>hrPRO"
			hod = frappe.db.get_value('Department',doc.department,"hod")
			# frappe.msgprint(content+table+data)
			frappe.sendmail(
				recipients=[hod],
				subject='Reg.Shift Schedule Approval',
				message = content+table+data+regards)
 
@frappe.whitelist()  
def validate_shift(doc,method):
		if doc.workflow_state == 'Pending for GM':
			link = get_url_to_form("Shift Schedule", doc.name)
			filepath = get_file(doc.upload)
			pps = read_csv_content(filepath[1])
			data = ''
			# wc1,wc2,wc3,wcpp1,wcpp2,bc1,bc2,bc3,bcpp1,bcpp2,ft1,ft2,ft3,ftpp1,ftpp2,nt1,nt2,nt3,ntpp1,ntpp2,cl1,cl2,cl3,clpp1,clpp2 =0
			wc1 = 0
			wc2 = 0
			wc3 = 0
			wcpp1 = 0
			wcpp2 = 0
			bc1 = 0
			bc2 = 0
			bc3 = 0
			bcpp1 = 0
			bcpp2 = 0
			ft1 = 0
			ft2 = 0
			ft3 = 0
			ftpp1 = 0
			ftpp2 = 0
			nt1 = 0
			nt2 = 0
			nt3 = 0
			ntpp1 = 0
			ntpp2 = 0
			cl1 = 0
			cl2 = 0
			cl3 = 0
			clpp1 = 0
			clpp2 =0
			for pp in pps:
				if pp[4] == 'WC':
					if pp[4] == "1":
						wc1 +=1
					elif pp[4] == "2":
						wc2 +=1
					elif pp[4] == "3":
						wc3 +=1
					elif pp[4] == "PP1":
						wcpp1 +=1
					elif pp[4] == "PP2":
						wcpp2 +=1
				if pp[4] == 'BC':
					if pp[4] == "1":
						bc1 +=1
					elif pp[4] == "2":
						bc2 +=1
					elif pp[4] == "3":
						bc3 +=1
					elif pp[4] == "PP1":
						bcpp1 +=1
					elif pp[4] == "PP2":
						bcpp2 +=1
				if pp[4] == 'FT':
					if pp[4] == "1":
						ft1 +=1
					elif pp[4] == "2":
						ft2 +=1
					elif pp[4] == "3":
						ft3 +=1
					elif pp[4] == "PP1":
						ftpp1 +=1
					elif pp[4] == "PP2":
						ftpp2 +=1
				if pp[4] == 'NT':
					if pp[4] == "1":
						nt1 +=1
					elif pp[4] == "2":
						nt2 +=1
					elif pp[4] == "3":
						nt3 +=1
					elif pp[4] == "PP1":
						ntpp1 +=1
					elif pp[4] == "PP2":
						ntpp2 +=1
				if pp[4] == 'CL':
					if pp[4] == "1":
						cl1 +=1
					elif pp[4] == "2":
						cl2 +=1
					elif pp[4] == "3":
						cl3 +=1
					elif pp[4] == "PP1":
						clpp1 +=1
					elif pp[4] == "PP2":
						clpp2 +=1
			total = wc1+wc2+wc3+wcpp1+wcpp2+bc1+bc2+bc3+bcpp1+bcpp2+ft1+ft2+ft3+ftpp1+ftpp2+nt1+nt2+nt3+ntpp1+ntpp2+cl1+cl2+cl3+clpp1+clpp2
			data += """ <table class=table table-bordered>
				<tr><th colspan='7' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule Summary</center></th><tr>
				<tr><td style="background-color:#f0b27a; border: 1px solid black">Shift</td><td style="background-color:#f0b27a ; border: 1px solid black">1</td><td style="background-color:#f0b27a; border: 1px solid black">2</td><td style="background-color:#f0b27a; border: 1px solid black">3</td><td style="background-color:#f0b27a; border: 1px solid black">PP1</td><td style="background-color:#f0b27a; border: 1px solid black">PP2</td><td style="background-color:#f0b27a ; border: 1px solid black">Total</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>WC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>BC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>FT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>NT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<th style = 'border: 1px solid black'>CL</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr>
				<tr>
					<td style="background-color:#58d68d; border: 1px solid black">Total</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
				</tr></table>"""%(wc1,wc2,wc3,wcpp1,wcpp2,(wc1+wc2+wc3+wcpp1+wcpp2),bc1,bc2,bc3,bcpp1,bcpp2,(bc1+bc2+bc3+bcpp1+bcpp2),ft1,ft2,ft3,ftpp1,ftpp2,(ft1+ft2+ft3+ftpp1+ftpp2),nt1,nt2,nt3,ntpp1,ntpp2,(nt1+nt2+nt3+ntpp1+ntpp2),cl1,cl2,cl3,clpp1,clpp2,(cl1+cl2+cl3+clpp1+clpp2),(wc1+bc1+ft1+nt1+cl1),(wc2+bc2+ft2+nt2+cl2),(wc3+bc3+ft3+nt3+cl3),(wcpp1+bcpp1+ftpp1+ntpp1+clpp1),(wcpp2+bcpp2+ftpp2+ntpp2+clpp2),total)

			content="""<p>Dear Sir,</p>
			Kindly find the below Shift Schedule Request<br>"""
			table = """<table class=table table-bordered><tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule</center></th><tr>
			<tr><th colspan='2' style = 'border: 1px solid black'>Department</th><td colspan='2' style = 'border: 1px solid black'>%s</td></tr>
			<tr><th style = 'border: 1px solid black'>From Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Date</th><td style = 'border: 1px solid black'>%s</td></tr>
			<tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
			</table><br>"""%(doc.department,format_date(doc.from_date),format_date(doc.to_date),link)
			regards = "Thanks & Regards,<br>hrPRO"
			gm = frappe.db.get_value('Department',doc.department,"gm")
			# frappe.msgprint(content+table+data)
			frappe.sendmail(
				recipients=[gm,'mohan.pan@thaisummit.co.in'],
				subject='Reg.Shift Schedule Approval',
				message = content+table+data+regards)
   

@frappe.whitelist()
def wrong_shift_mail_alert_hr():
	yesterday = frappe.utils.today()
	attendance = frappe.db.sql("""
		SELECT * FROM `tabAttendance`
		WHERE attendance_date = %s AND docstatus != 2
		ORDER BY employee
	""", (yesterday,), as_dict=True)
	
	staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">Wrong Shift Report</h2>
		</div>
		<table style="border-collapse: collapse; width: 100%; border: 1px solid black; font-size: 10px;">
			<tr style="border: 1px solid black;">
				<th style="padding: 4px; border: 1px solid black;">S.No</th>
				<th style="padding: 4px; border: 1px solid black;">Employee</th>
				<th style="padding: 4px; border: 1px solid black;">Employee Name</th>
				<th style="padding: 4px; border: 1px solid black;">Department</th>
				<th style="padding: 4px; border: 1px solid black;">Attendance Date</th>
				<th style="padding: 4px; border: 1px solid black;">Attended Shift</th>
				<th style="padding: 4px; border: 1px solid black;">Assigned Shift</th>
			</tr>
	"""
	no_punches = True
	i = 0
	for att in attendance:
		if att.shift:
			default_shift = frappe.get_value("Shift Assignment",{'employee':att.employee,'start_date':('>=',att.attendance_date),'end_date':('<=',att.attendance_date),'docstatus':1},['shift_type']) or ''
			if att.shift != default_shift:
				i += 1
				no_punches = False
				staff += """
				<tr style="border: 1px solid black;">
					<td style="padding: 4px; border: 1px solid black;">{6}</td>
					<td style="padding: 4px; border: 1px solid black;">{0}</td>
					<td style="padding: 4px; border: 1px solid black;">{1}</td>
					<td style="padding: 4px; border: 1px solid black;">{2}</td>
					<td style="padding: 4px; border: 1px solid black;text-align: center;">{3}</td>
					<td style="padding: 4px; border: 1px solid black;text-align: center;">{4}</td>
					<td style="padding: 4px; border: 1px solid black;text-align: center;">{5}</td>
				</tr>
				""".format(att.employee, att.employee_name, att.department,
						format_date(att.attendance_date) or ' ', att.shift or ' ',default_shift or '',i)
		
	if no_punches:
		staff = """
		<div style="text-align: center;">
			<h2 style="font-size: 16px;">No wrong shift employees for yesterday.</h2>
		</div>
		"""
	else:
		staff += "</table>"
	user = frappe.db.sql("""
					SELECT `tabUser`.name as name
					FROM `tabUser`
					LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name where `tabHas Role`.Role="HR" and `tabUser`.enabled=1
					""",as_dict=True)
	if attendance:
		for i in user:
			frappe.sendmail(
				recipients=[i.name],
				subject='Wrong Shift Report',
				message="""Dear Sir,<br><br>
						Kindly find the attached Wrong Shift Employee List for today:<br>{0}
						""".format(staff)
			)
		frappe.sendmail(
				recipients=['arockia.k@groupteampro.com','sivarenisha.m@groupteampro.com','jenisha.p@groupteampro.com','sarath.v@groupteampro.com','anil.p@groupteampro.com'],
				subject='Wrong Shift Report',
				message="""Dear Sir,<br><br>
						Kindly find the attached Wrong Shift Employee List for today:<br>{0}
						""".format(staff)
		) 
@frappe.whitelist()
def cron_job_wrong_shift_mail_alert_hr():
	job = frappe.db.exists('Scheduled Job Type', 'wrong_shift_mail_alert_hr')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.wrong_shift_mail_alert_hr',
			"frequency": 'Cron',
			"cron_format": '30 8,17 * * *'
		})
		att.save(ignore_permissions=True)
  
  
@frappe.whitelist()
def wrong_shift_mail_alert_fm_():
	yesterday = frappe.utils.today()
	attendance = frappe.db.sql("""
		SELECT * FROM `tabAttendance`
		WHERE attendance_date = %s AND docstatus != 2
		ORDER BY employee
	""", (yesterday,), as_dict=True)
	
	for att in attendance:
		if att.shift:
			default_shift = frappe.get_value("Shift Assignment",{'employee':att.employee,'start_date':('>=',att.attendance_date),'end_date':('<=',att.attendance_date),'docstatus':1},['shift_type']) or ''
			employee = frappe.db.get_value('Employee',att.employee,"custom_first_manager")
			if att.shift != default_shift:
				if default_shift:
					mess = """Dear Sir,<br><br>
							The below employee came on  Wrong Shift for today:<br><br>
							Employee ID : {0} - Attended Shift is {1}, but the assigned shift is {2}.
							""".format(att.employee,att.shift,default_shift)
				else:
					mess = """Dear Sir,<br><br>
							The below employee came on  Wrong Shift for today:<br><br>
							Employee ID : {0} - Attended Shift is {1}, but there is no shift is assigned.
							""".format(att.employee,att.shif)
				frappe.sendmail(
					recipients=[employee],
					subject='Wrong Shift Report',
					message=mess
				) 
@frappe.whitelist()
def cron_job_wrong_shift_mail_alert_fm():
	job = frappe.db.exists('Scheduled Job Type', 'wrong_shift_mail_alert_fm')
	if not job:
		att = frappe.new_doc("Scheduled Job Type")
		att.update({
			"method": 'ir.email_alerts.wrong_shift_mail_alert_fm_',
			"frequency": 'Cron',
			"cron_format": '30 8,17 * * *'
		})
		att.save(ignore_permissions=True)