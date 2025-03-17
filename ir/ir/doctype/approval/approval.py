# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

#All the below lines based on change workflow state
class Approval(Document):
    @frappe.whitelist(allow_guest=True)
    def submit_leave_doc(self,doctype,name,workflow_state):
        frappe.log_error(doctype,workflow_state)
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            doc.status = 'Approved'
            doc.flags.ignore_permissions = 1
            doc.workflow_state = workflow_state
            doc.save(ignore_permissions=True)
            doc.submit()
        elif workflow_state == 'Rejected' and doctype=='Leave Application':
            doc.workflow_state = workflow_state
            doc.status='Rejected'
            doc.save(ignore_permissions=True) 
            doc.submit()          
        else:
            if workflow_state == 'SM Pending':
                if not doc.custom_second_manager:
                    doc.workflow_state = 'HR Pending'
                    doc.save(ignore_permissions=True)
                else:
                    doc.workflow_state = workflow_state
                    doc.save(ignore_permissions=True)
            else:
                doc.workflow_state = workflow_state
                doc.save(ignore_permissions=True)
        return "ok"

    @frappe.whitelist(allow_guest=True)
    def submit_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            doc.workflow_state = 'Approved'
            doc.save(ignore_permissions=True)
            doc.submit()
        else:
            if workflow_state == 'FM Pending':
                doc.workflow_state = 'HR Pending'
                
                doc.save(ignore_permissions=True)
                # if not doc.custom_second_manager and doctype == "Over Time Request":
                #     doc.workflow_state = 'Pending for Plant Manager'
                #     doc.save(ignore_permissions=True)
                # else:
                #     doc.workflow_state = workflow_state
                #     doc.save(ignore_permissions=True)
            else:
                doc.workflow_state = workflow_state
                doc.save(ignore_permissions=True)
        return "ok"

    @frappe.whitelist(allow_guest=True)
    def submit_miss_punch_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            doc.save(ignore_permissions=True)
            doc.submit()
        if workflow_state == 'Rejected':
            doc.workflow_state = 'Rejected'
            doc.save(ignore_permissions=True)
            doc.submit()
        return "ok"
    @frappe.whitelist(allow_guest=True)
    def submit_coff_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Rejected':
            doc.workflow_state = 'Rejected'
            doc.save(ignore_permissions=True)
            doc.submit()
        if workflow_state == 'FM Pending':
            doc.workflow_state = 'HR Pending'
            doc.save(ignore_permissions=True)
        if workflow_state == 'SM Pending':
            doc.workflow_state = 'HR Pending'
            doc.save(ignore_permissions=True)
        if workflow_state == 'HR Pending':
            doc.workflow_state = 'Approved'
            doc.save(ignore_permissions=True)
            doc.submit()
        return "ok"

    @frappe.whitelist(allow_guest=True)
    def submit_shift_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            doc.status = 'Approved'
            doc.workflow_state = workflow_state
            doc.save(ignore_permissions=True)
            doc.submit()
        else:
            if workflow_state == 'FM Pending':
                if not doc.custom_first_manager:
                    doc.workflow_state = 'HR Pending'
                    doc.save(ignore_permissions=True)
                else:
                    doc.workflow_state = workflow_state
                    doc.save(ignore_permissions=True)
            else:
                doc.workflow_state = workflow_state
                doc.save(ignore_permissions=True)
        return "ok"
    
