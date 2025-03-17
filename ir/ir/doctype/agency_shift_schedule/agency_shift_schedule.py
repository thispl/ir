# -*- coding: utf-8 -*-
# Copyright (c) 2021, TEAMPRO and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
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

class AgencyShiftSchedule(Document):
    # shift assignment has been created from on ubmission of shift schedule
    @frappe.whitelist()
    def on_submit(self):
        ss = self.name
        fd = self.from_date
        td = self.to_date
        file = self.upload
        workflow_state = self.workflow_state
        enqueue(self.enqueue_submit_schedule, queue='default', timeout=6000, event='enqueue_submit_schedule'
        ,ss=ss,fd=fd,td=td,file=file,workflow_state=workflow_state)

    @frappe.whitelist()
    def enqueue_submit_schedule(self,ss,workflow_state,fd,td,file):
        if workflow_state == "Approved":
            filepath = get_file(file)
            pps = read_csv_content(filepath[1])
            no_of_days = date_diff(add_days(td, 1), fd)
            dates = [add_days(fd, i) for i in range(0, no_of_days)]
            # for pp in pps:
            # 	if pp[4] and pp[4] != 'Shift':
            # 		for date in dates:
            # 			if frappe.db.exists("Shift Assignment", {'employee': pp[0], 'start_date': date, 'end_date': date, 'docstatus': ['in', [0, 1]]}):
            # 				
            for pp in pps:
                if pp[4] and pp[4] != 'Shift':
                    for date in dates:
                        if not frappe.db.exists("Shift Assignment", {'employee': pp[0], 'start_date': date, 'end_date': date, 'docstatus': ['in', [0, 1]]}):
                            doc = frappe.new_doc("Shift Assignment")
                            doc.employee = pp[0]
                            doc.department = pp[2]
                            doc.custom_employee_category = pp[3]
                            doc.shift_type = pp[4]
                            doc.start_date = date
                            doc.end_date = date
                            doc.custom_agency_shift_schedule = ss
                            doc.save(ignore_permissions=True)
                            doc.submit()
                            frappe.db.commit()
                            
                        else:
                            continue
                            # frappe.throw(_("Employee {0} already has assigned Shift for {1}").format(frappe.bold(pp[0]), frappe.bold(date)))
                    # frappe.db.set_value('Employee', pp[0], "default_shift", pp[4])
            frappe.msgprint('Shift Schedule uploaded successfully')
            sas = frappe.get_all("Shift Assignment",{'custom_agency_shift_schedule':ss,'docstatus':'0'})
            for sa in sas:
                doc = frappe.get_doc('Shift Assignment',sa.name)
                doc.submit()
                frappe.db.commit()
            frappe.msgprint('Shift Schedule Approved Successfully')
            
        elif workflow_state == "Rejected":
            sas = frappe.get_all("Shift Assignment",{'custom_agency_shift_schedule':ss,'docstatus':'0'})
            for sa in sas:
                frappe.delete_doc('Shift Assignment',sa.name)
            frappe.msgprint('Shift Schedule Rejected Successfully')


    # def after_insert(self):
    #     if self.workflow_state == 'Pending for HOD':
    #         link = get_url_to_form("Agency Shift Schedule", self.name)
    #         filepath = get_file(self.upload)
    #         pps = read_csv_content(filepath[1])
    #         data = ''
    #         # wc1,wc2,wc3,wcpp1,wcpp2,bc1,bc2,bc3,bcpp1,bcpp2,ft1,ft2,ft3,ftpp1,ftpp2,nt1,nt2,nt3,ntpp1,ntpp2,cl1,cl2,cl3,clpp1,clpp2 =0
    #         wc1 = 0
    #         wc2 = 0
    #         wc3 = 0
    #         wcpp1 = 0
    #         wcpp2 = 0
    #         bc1 = 0
    #         bc2 = 0
    #         bc3 = 0
    #         bcpp1 = 0
    #         bcpp2 = 0
    #         ft1 = 0
    #         ft2 = 0
    #         ft3 = 0
    #         ftpp1 = 0
    #         ftpp2 = 0
    #         nt1 = 0
    #         nt2 = 0
    #         nt3 = 0
    #         ntpp1 = 0
    #         ntpp2 = 0
    #         cl1 = 0
    #         cl2 = 0
    #         cl3 = 0
    #         clpp1 = 0
    #         clpp2 =0
    #         for pp in pps:
    #             if pp[4] == 'WC':
    #                 if pp[4] == "1":
    #                     wc1 +=1
    #                 elif pp[4] == "2":
    #                     wc2 +=1
    #                 elif pp[4] == "3":
    #                     wc3 +=1
    #                 elif pp[4] == "PP1":
    #                     wcpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     wcpp2 +=1
    #             if pp[4] == 'BC':
    #                 if pp[4] == "1":
    #                     bc1 +=1
    #                 elif pp[4] == "2":
    #                     bc2 +=1
    #                 elif pp[4] == "3":
    #                     bc3 +=1
    #                 elif pp[4] == "PP1":
    #                     bcpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     bcpp2 +=1
    #             if pp[4] == 'FT':
    #                 if pp[4] == "1":
    #                     ft1 +=1
    #                 elif pp[4] == "2":
    #                     ft2 +=1
    #                 elif pp[4] == "3":
    #                     ft3 +=1
    #                 elif pp[4] == "PP1":
    #                     ftpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     ftpp2 +=1
    #             if pp[4] == 'NT':
    #                 if pp[4] == "1":
    #                     nt1 +=1
    #                 elif pp[4] == "2":
    #                     nt2 +=1
    #                 elif pp[4] == "3":
    #                     nt3 +=1
    #                 elif pp[4] == "PP1":
    #                     ntpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     ntpp2 +=1
    #             if pp[4] == 'CL':
    #                 if pp[4] == "1":
    #                     cl1 +=1
    #                 elif pp[4] == "2":
    #                     cl2 +=1
    #                 elif pp[4] == "3":
    #                     cl3 +=1
    #                 elif pp[4] == "PP1":
    #                     clpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     clpp2 +=1
    #         total = wc1+wc2+wc3+wcpp1+wcpp2+bc1+bc2+bc3+bcpp1+bcpp2+ft1+ft2+ft3+ftpp1+ftpp2+nt1+nt2+nt3+ntpp1+ntpp2+cl1+cl2+cl3+clpp1+clpp2
    #         data += """ <table class=table table-bordered>
    #             <tr><th colspan='7' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Agency Shift Schedule Summary</center></th><tr>
    #             <tr><td style="background-color:#f0b27a; border: 1px solid black">Shift</td><td style="background-color:#f0b27a ; border: 1px solid black">1</td><td style="background-color:#f0b27a; border: 1px solid black">2</td><td style="background-color:#f0b27a; border: 1px solid black">3</td><td style="background-color:#f0b27a; border: 1px solid black">PP1</td><td style="background-color:#f0b27a; border: 1px solid black">PP2</td><td style="background-color:#f0b27a ; border: 1px solid black">Total</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>WC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>BC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>FT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>NT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>CL</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <td style="background-color:#58d68d; border: 1px solid black">Total</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr></table>"""%(wc1,wc2,wc3,wcpp1,wcpp2,(wc1+wc2+wc3+wcpp1+wcpp2),bc1,bc2,bc3,bcpp1,bcpp2,(bc1+bc2+bc3+bcpp1+bcpp2),ft1,ft2,ft3,ftpp1,ftpp2,(ft1+ft2+ft3+ftpp1+ftpp2),nt1,nt2,nt3,ntpp1,ntpp2,(nt1+nt2+nt3+ntpp1+ntpp2),cl1,cl2,cl3,clpp1,clpp2,(cl1+cl2+cl3+clpp1+clpp2),(wc1+bc1+ft1+nt1+cl1),(wc2+bc2+ft2+nt2+cl2),(wc3+bc3+ft3+nt3+cl3),(wcpp1+bcpp1+ftpp1+ntpp1+clpp1),(wcpp2+bcpp2+ftpp2+ntpp2+clpp2),total)

    #         content="""<p>Dear Sir,</p>
    #         Kindly find the below Shift Schedule Request<br>"""
    #         table = """<table class=table table-bordered><tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule</center></th><tr>
    #         <tr><th colspan='2' style = 'border: 1px solid black'>Department</th><td colspan='2' style = 'border: 1px solid black'>%s</td></tr>
    #         <tr><th style = 'border: 1px solid black'>From Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Date</th><td style = 'border: 1px solid black'>%s</td></tr>
    #         <tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
    #         </table><br>"""%(self.department,format_date(self.from_date),format_date(self.to_date),link)
    #         regards = "Thanks & Regards,<br>hrPRO"
    #         hod = frappe.db.get_value('Department',self.department,"hod")
    #         # frappe.msgprint(content+table+data)
    #         frappe.sendmail(
    #             recipients=[hod],
    #             subject='Reg.Shift Schedule Approval',
    #             message = content+table+data+regards)

    # def validate(self):
    #     if self.workflow_state == 'Pending for GM':
    #         link = get_url_to_form("Agency Shift Schedule", self.name)
    #         filepath = get_file(self.upload)
    #         pps = read_csv_content(filepath[1])
    #         data = ''
    #         # wc1,wc2,wc3,wcpp1,wcpp2,bc1,bc2,bc3,bcpp1,bcpp2,ft1,ft2,ft3,ftpp1,ftpp2,nt1,nt2,nt3,ntpp1,ntpp2,cl1,cl2,cl3,clpp1,clpp2 =0
    #         wc1 = 0
    #         wc2 = 0
    #         wc3 = 0
    #         wcpp1 = 0
    #         wcpp2 = 0
    #         bc1 = 0
    #         bc2 = 0
    #         bc3 = 0
    #         bcpp1 = 0
    #         bcpp2 = 0
    #         ft1 = 0
    #         ft2 = 0
    #         ft3 = 0
    #         ftpp1 = 0
    #         ftpp2 = 0
    #         nt1 = 0
    #         nt2 = 0
    #         nt3 = 0
    #         ntpp1 = 0
    #         ntpp2 = 0
    #         cl1 = 0
    #         cl2 = 0
    #         cl3 = 0
    #         clpp1 = 0
    #         clpp2 =0
    #         for pp in pps:
    #             if pp[4] == 'WC':
    #                 if pp[4] == "1":
    #                     wc1 +=1
    #                 elif pp[4] == "2":
    #                     wc2 +=1
    #                 elif pp[4] == "3":
    #                     wc3 +=1
    #                 elif pp[4] == "PP1":
    #                     wcpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     wcpp2 +=1
    #             if pp[4] == 'BC':
    #                 if pp[4] == "1":
    #                     bc1 +=1
    #                 elif pp[4] == "2":
    #                     bc2 +=1
    #                 elif pp[4] == "3":
    #                     bc3 +=1
    #                 elif pp[4] == "PP1":
    #                     bcpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     bcpp2 +=1
    #             if pp[4] == 'FT':
    #                 if pp[4] == "1":
    #                     ft1 +=1
    #                 elif pp[4] == "2":
    #                     ft2 +=1
    #                 elif pp[4] == "3":
    #                     ft3 +=1
    #                 elif pp[4] == "PP1":
    #                     ftpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     ftpp2 +=1
    #             if pp[4] == 'NT':
    #                 if pp[4] == "1":
    #                     nt1 +=1
    #                 elif pp[4] == "2":
    #                     nt2 +=1
    #                 elif pp[4] == "3":
    #                     nt3 +=1
    #                 elif pp[4] == "PP1":
    #                     ntpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     ntpp2 +=1
    #             if pp[4] == 'CL':
    #                 if pp[4] == "1":
    #                     cl1 +=1
    #                 elif pp[4] == "2":
    #                     cl2 +=1
    #                 elif pp[4] == "3":
    #                     cl3 +=1
    #                 elif pp[4] == "PP1":
    #                     clpp1 +=1
    #                 elif pp[4] == "PP2":
    #                     clpp2 +=1
    #         total = wc1+wc2+wc3+wcpp1+wcpp2+bc1+bc2+bc3+bcpp1+bcpp2+ft1+ft2+ft3+ftpp1+ftpp2+nt1+nt2+nt3+ntpp1+ntpp2+cl1+cl2+cl3+clpp1+clpp2
    #         data += """ <table class=table table-bordered>
    #             <tr><th colspan='7' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule Summary</center></th><tr>
    #             <tr><td style="background-color:#f0b27a; border: 1px solid black">Shift</td><td style="background-color:#f0b27a ; border: 1px solid black">1</td><td style="background-color:#f0b27a; border: 1px solid black">2</td><td style="background-color:#f0b27a; border: 1px solid black">3</td><td style="background-color:#f0b27a; border: 1px solid black">PP1</td><td style="background-color:#f0b27a; border: 1px solid black">PP2</td><td style="background-color:#f0b27a ; border: 1px solid black">Total</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>WC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>BC</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d ; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>FT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>NT</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <th style = 'border: 1px solid black'>CL</th><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr>
    #             <tr>
    #                 <td style="background-color:#58d68d; border: 1px solid black">Total</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td><td style="background-color:#58d68d; border: 1px solid black">%s</td>
    #             </tr></table>"""%(wc1,wc2,wc3,wcpp1,wcpp2,(wc1+wc2+wc3+wcpp1+wcpp2),bc1,bc2,bc3,bcpp1,bcpp2,(bc1+bc2+bc3+bcpp1+bcpp2),ft1,ft2,ft3,ftpp1,ftpp2,(ft1+ft2+ft3+ftpp1+ftpp2),nt1,nt2,nt3,ntpp1,ntpp2,(nt1+nt2+nt3+ntpp1+ntpp2),cl1,cl2,cl3,clpp1,clpp2,(cl1+cl2+cl3+clpp1+clpp2),(wc1+bc1+ft1+nt1+cl1),(wc2+bc2+ft2+nt2+cl2),(wc3+bc3+ft3+nt3+cl3),(wcpp1+bcpp1+ftpp1+ntpp1+clpp1),(wcpp2+bcpp2+ftpp2+ntpp2+clpp2),total)

    #         content="""<p>Dear Sir,</p>
    #         Kindly find the below Shift Schedule Request<br>"""
    #         table = """<table class=table table-bordered><tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center>Shift Schedule</center></th><tr>
    #         <tr><th colspan='2' style = 'border: 1px solid black'>Department</th><td colspan='2' style = 'border: 1px solid black'>%s</td></tr>
    #         <tr><th style = 'border: 1px solid black'>From Date</th><td style = 'border: 1px solid black'>%s</td><th style = 'border: 1px solid black'>To Date</th><td style = 'border: 1px solid black'>%s</td></tr>
    #         <tr><th colspan='4' style = 'border: 1px solid black;background-color:#ffedcc;'><center><a href='%s'>VIEW</a></center></th></tr>
    #         </table><br>"""%(self.department,format_date(self.from_date),format_date(self.to_date),link)
    #         regards = "Thanks & Regards,<br>hrPRO"
    #         gm = frappe.db.get_value('Department',self.department,"gm")
    #         # frappe.msgprint(content+table+data)
    #         frappe.sendmail(
    #             recipients=[gm,'mohan.pan@thaisummit.co.in'],
    #             subject='Reg.Shift Schedule Approval',
    #             message = content+table+data+regards)

    @frappe.whitelist()
    def validate_employees(self):
        err_list = ""
        filepath = get_file(self.upload)
        pps = read_csv_content(filepath[1])
        dates = self.get_dates()
        emp_list = []
        for pp in pps:
            if pp[0] != 'ID':
                emp_list.append(pp[0])
        # limit = frappe.db.get_value('Department',self.department,"limit")
        # if limit != 0:
        # 	if limit < len(emp_list):
        # 		err_list += '<li> Maximum manpower limit for <b>%s</b> is <font color="red"> %s</font>. </li>'%(self.department,limit)
        # 		if err_list:
        # 			return err_list
        shift_assignment = frappe.db.sql("""select name from `tabShift Assignment` where department = '%s' and start_date between '%s' and '%s' and shift_request ='%s' """%(self.department,self.from_date,self.to_date,''),as_dict=True)
        if shift_assignment:
            self.upload = ''
            return 'Shift Schedule already submitted for the selected date'
        for pp in pps:
            if emp_list.count(pp[0]) > 1:
                err_list += '<li> Employee ID - <font color="red"> %s</font> appears multiple times in the list. </li>'%pp[0]
        if err_list:
            return err_list
        for pp in pps:
            if pp[0] != 'ID':
                if pp[0]:
                    if not pp[1]:
                        err_list +='<li>Employe Name should not be Empty. </li>'
                    if not pp[2]:
                        err_list +='<li>Department should not be Empty. </li>'
                    # if not pp[3]:
                    # 	err_list +='<li>Department Code should not be Empty. </li>'
                    # if not pp[4]:
                    # 	err_list +='<li>Employee Type should not be Empty. </li>'
                    # if not pp[4]:
                    # 	err_list +='<li>Shift should not be Empty. </li>'
                    # if not pp[7]:
                    #     err_list +='<li>Boarding Point should not be Empty. </li>'
                    if not frappe.db.exists("Employee",{'name':pp[0],'status':'Active'}):
                        err_list +='<li><font color="red"><b>%s</b></font> is not an Active Employee. </li>'%(pp[0])
                    else:
                        if self.department != frappe.db.get_value("Employee",pp[0],"department"):
                            err_list += '<li><font color="red"><b>%s</b></font> doesnot belongs to <b>%s</b> department. </li>'%(pp[0],self.department)
                        else:
                            if pp[3]:
                                for date in dates:
                                    sa = frappe.db.exists('Shift Assignment',{'employee':pp[0],'start_date':date,'docstatus':['!=','2']})
                                    if sa:
                                        err_list += '<li>%s department have already allocated shift for <font color="red"><b>%s</b></font> for the date %s </li>'%(frappe.db.get_value("Shift Assignment",sa,"department"),pp[0],date)
                            else:
                                err_list += '<li>Shift value missing for <font color="red"><b>%s</b></font> in the upload sheet.</li>'%(pp[0])
                else:
                    li = [pp[1],pp[2],pp[3]]
                    if len(li) != 7:
                        err_list += '<li>ID should not be Empty.</li>'

        return err_list

    def get_dates(self):
        """get list of dates in between from date and to date"""
        no_of_days = date_diff(add_days(self.to_date, 1), self.from_date)
        dates = [add_days(self.from_date, i) for i in range(0, no_of_days)]
        return dates

    @frappe.whitelist()
    def show_csv_data(self):
        filepath = get_file(self.upload)
        pps = read_csv_content(filepath[1])
        data_list = ''
        for pp in pps:
            if pp[0] == 'ID':
                data_list += "<tr><td style='background-color:#f0b27a; border: 1px solid black'>%s</td><td style='background-color:#f0b27a; border: 1px solid black'>%s</td><td style='background-color:#f0b27a; border: 1px solid black'>%s</td><td style='background-color:#f0b27a; border: 1px solid black'>%s</td></tr>"%(pp[0],pp[1],pp[2],pp[3])
            else:
                # boarding_point = frappe.db.get_value('Employee',{'employee':pp[0]},['boarding_point'])
                data_list += "<tr><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td><td style = 'border: 1px solid black'>%s</td></tr>"%(pp[0],pp[1],pp[2],pp[3])
        return data_list

    @frappe.whitelist()
    def show_summary(self):
        filepath = get_file(self.upload)
        pps = read_csv_content(filepath[1])
        data = ''
        wc1 = wc2 = wc3 = wcpp1 = 0
        bc1 = bc2 = bc3 = bcpp1 = 0
        ft1 = ft2 = ft3 = ftpp1 = 0

        for pp in pps:
           
            if pp[3] == "1":
                wc1 += 1
            elif pp[3] == "2":
                wc2 += 1
            elif pp[3] == "G":
                wc3 += 1
            elif pp[3] == "3":
                wcpp1 += 1

        total = wc1 + wc2 + wc3 + wcpp1
        data += """
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="background-color:#f0b27a; border: 1px solid black">Shift</td>
                    <td style="background-color:#f0b27a; border: 1px solid black">1</td>
                    <td style="background-color:#f0b27a; border: 1px solid black">2</td>
                    <td style="background-color:#f0b27a; border: 1px solid black">G</td>
                    <td style="background-color:#f0b27a; border: 1px solid black">3</td>
                    <td style="background-color:#f0b27a; border: 1px solid black">Total</td>
                </tr>
                <tr>
                    <td style="background-color:#58d68d; border: 1px solid black">Total</td>
                    <td style="background-color:#58d68d; border: 1px solid black">{}</td>
                    <td style="background-color:#58d68d; border: 1px solid black">{}</td>
                    <td style="background-color:#58d68d; border: 1px solid black">{}</td>
                    <td style="background-color:#58d68d; border: 1px solid black">{}</td>
                    <td style="background-color:#58d68d; border: 1px solid black">{}</td>
                </tr>
            </table>
        """.format(
            wc1, wc2, wc3, wcpp1, wc1 + wc2 + wc3 + wcpp1,
        )

        return data

@frappe.whitelist()
def enqueue_shift_assignment(file,from_date,to_date,name):
    enqueue(create_shift_assignment, queue='default', timeout=6000, event='create_shift_assignment',
                    file=file,from_date=from_date,to_date=to_date,name=name)
    
@frappe.whitelist()
def create_shift_assignment(file,from_date,to_date,name):
    filepath = get_file(file)
    pps = read_csv_content(filepath[1])
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    # for pp in pps:
    # 	if pp[4] and pp[4] != 'Shift':
    # 		for date in dates:
    # 			if frappe.db.exists("Shift Assignment", {'employee': pp[0], 'start_date': date, 'end_date': date, 'docstatus': ['in', [0, 1]]}):
    # 				
    for pp in pps:
        if pp[4] and pp[4] != 'Shift':
            for date in dates:
                if not frappe.db.exists("Shift Assignment", {'employee': pp[0], 'start_date': date, 'end_date': date, 'docstatus':("!=",2)}):
                    if not frappe.db.exists("Shift Request", {'employee': pp[0], 'from_date': date, 'to_date': date, 'docstatus':("!=",2)}):
                        doc = frappe.new_doc("Shift Assignment")
                        doc.employee = pp[0]
                        doc.department = pp[2]
                        doc.custom_employee_category = pp[3]
                        doc.shift_type = pp[4]
                        doc.start_date = date
                        doc.end_date = date
                        doc.custom_agency_shift_schedule = name
                        doc.insert(ignore_permissions=True)
                        doc.save(ignore_permissions=True)
                    else:
                        frappe.throw(_("Employee {0} already has assigned Shift for {1}").format(frappe.bold(pp[0]), frappe.bold(date)))
            # frappe.db.set_value('Employee', pp[0], "default_shift", pp[4])
    frappe.db.commit()
    frappe.msgprint('Shift Schedule uploaded successfully')

@frappe.whitelist()
def get_template():
    args = frappe.local.form_dict

    if getdate(args.from_date) > getdate(args.to_date):
        frappe.throw(_("To Date should be greater than From Date"))

    w = UnicodeWriter()
    w = add_header(w)

    w = add_data(w, args)

    # write out response as a type csv
    frappe.response['result'] = cstr(w.getvalue())
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Shift Assignment"

@frappe.whitelist()
def add_header(w):
    w.writerow(["ID", "Name", "Department", "Employee Category", "Shift"])
    return w

@frappe.whitelist()
def add_data(w, args):
    data = get_data(args)
    writedata(w, data)
    return w

@frappe.whitelist()
def get_data(args):
    employees = get_active_employees(args)
    data = []
    for employee in employees:
        row = [
            employee.name, employee.employee_name, employee.department or '',employee.custom_employee_category,employee.default_shift
        ]
        data.append(row)
    return data

@frappe.whitelist()
def writedata(w, data):
    for row in data:
        w.writerow(row)

@frappe.whitelist()
def get_active_employees(args):
    employees = frappe.db.get_all('Employee',
        fields=['name', 'employee_name', 'department', 'date_of_joining', 'company', 'relieving_date','custom_employee_category','default_shift'],
        filters={
            'docstatus': ['<', 2],
            'status': 'Active',
            'department': (args["department"]).replace("5","&"),
            'employment_type':["=","Agency"]
        }
    )
    return employees

@frappe.whitelist()
def shift_wise_count(doc):
    employee_type = ["White Collar","Blue Collar","Grey Collar"]
    data = "<table class='table table-bordered'><tr><td colspan='2' style='background-color:#f0b27a'><center>Shift 1</center></td><td colspan='2' style='background-color:#f0b27a'><center>Shift 2</center></td><td colspan='2' style='background-color:#f0b27a'><center>Shift 3</center></td><td colspan='2' style='background-color:#f0b27a'><center>Shift PP1</center></td><td colspan='2' style='background-color:#f0b27a'><center>Shift PP2</center></td><td colspan='2' style='background-color:#f0b27a'><center>Total Head Count</center></td></tr>"
    for emp_type in employee_type:
        s1 = 0
        s2 = 0
        s3 = 0
        spp1 = 0
        spp2 = 0
        shift1 = frappe.db.sql("select count(*) as count from `tabShift Assignment` where shift_type = '1' and docstatus != 2 and start_date = '%s' and custom_employee_category = '%s' and department = '%s' "%(doc.from_date,emp_type,doc.department),as_dict=True)
        shift2 = frappe.db.sql("select count(*) as count from `tabShift Assignment` where shift_type = '2' and docstatus != 2 and start_date = '%s' and custom_employee_category = '%s' and department = '%s' "%(doc.from_date,emp_type,doc.department),as_dict=True)
        shift3 = frappe.db.sql("select count(*) as count from `tabShift Assignment` where shift_type = 'G' and docstatus != 2 and start_date = '%s' and custom_employee_category = '%s' and department = '%s' "%(doc.from_date,emp_type,doc.department),as_dict=True)		
        if shift1:
            s1 = shift1[0].count
        if shift2:
            s2 = shift2[0].count
        if shift3:
            s3 = shift3[0].count
        total = s1+s2+s3
        data += '<tr><td style="background-color:#58d68d">%s</td><td>%s</td><td style="background-color:#58d68d">%s</td><td>%s</td><td style="background-color:#58d68d">%s</td><td>%s</td><td style="background-color:#58d68d">%s</td><td>%s</td><td style="background-color:#58d68d">%s</td><td>%s</td><td style="background-color:#58d68d">%s</td><td>%s</td></tr>'%(emp_type,s1,emp_type,s2,emp_type,s3,emp_type,spp1,emp_type,spp2,emp_type,total)
    sf1 = frappe.db.sql("select count(*) as count from `tabShift Assignment` where shift_type = '1' and docstatus != 2 and start_date = '%s' and department = '%s' "%(doc.from_date,doc.department),as_dict=True)
    sf2 = frappe.db.sql("select count(*) as count from `tabShift Assignment` where shift_type = '2' and docstatus != 2 and start_date = '%s' and department = '%s' "%(doc.from_date,doc.department),as_dict=True)
    sf3 = frappe.db.sql("select count(*) as count from `tabShift Assignment` where shift_type = '3' and docstatus != 2 and start_date = '%s' and department = '%s' "%(doc.from_date,doc.department),as_dict=True)
    data += '<tr><td style="background-color:#f0b27a">Total</td><td>%s</td><td style="background-color:#f0b27a">Total</td><td>%s</td><td style="background-color:#f0b27a">Total</td><td>%s</td><td style="background-color:#f0b27a">Total</td><td>%s</td><td style="background-color:#f0b27a">Total</td><td>%s</td><td style="background-color:#f0b27a">Total</td><td>%s</td></tr>'%(sf1[0].count,sf2[0].count,sf3[0].count,sfpp1[0].count,sfpp2[0].count,sf1[0].count+sf2[0].count+sf3[0].count+sfpp1[0].count+sfpp2[0].count)
    data = data + '</table>' 
    return data


@frappe.whitelist()
def shift_employees(doc,shift):
    shift_emp = frappe.db.sql("select employee,employee_name from `tabShift Assignment` where shift_type = '%s' and docstatus != 2 and start_date = '%s' and department = '%s' "%(shift,doc.from_date,doc.department),as_dict=True)
    data = "<table class='table table-bordered'><tr><td style='background-color:#f0b27a'><center>S.No</center></td><td colspan='2' style='background-color:#f0b27a'><center>Shift %s</center></td></tr>"%(shift)
    if shift_emp:
        i = 1
        for s in shift_emp:
            data += '<tr><td style="background-color:#f0b27a">%s</td><td style="background-color:#58d68d">%s</td><td>%s</td></tr>'%(i,s.employee,s.employee_name)
            i += 1
    else:
        data += '<tr><td></td><td></td></tr>'
    data = data + '</table>'
    return data


@frappe.whitelist()
def shift_cancel(doc,method):
    sas = frappe.get_all("Shift Assignment", filters={'custom_agency_shift_schedule': doc.name, 'docstatus': 1}, fields=['name'])
    for sa in sas:
        doc = frappe.get_doc('Shift Assignment', sa.name)
        doc.cancel()
    frappe.msgprint('Shift Schedule Rejected Successfully')
 
from datetime import datetime
@frappe.whitelist()
def shift_schedule_upload(posting, fdate, tdate):
    posting = datetime.strptime(posting, "%Y-%m-%d")
    fdate = datetime.strptime(fdate, "%Y-%m-%d")
    tdate = datetime.strptime(tdate, "%Y-%m-%d")
    day_of_posting = posting.weekday()
    from_day = fdate.weekday()
    to_day = tdate.weekday()
    fromdate = add_days(posting, 3)
    todate = add_days(posting, 8)
    if day_of_posting == 4 and from_day == 0 and to_day == 5:
        if fdate==fromdate and tdate==todate:
            return 'True'
    else:
        return 'False'


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