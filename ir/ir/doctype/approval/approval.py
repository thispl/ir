# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Approval(Document):
    @frappe.whitelist()
    def submit_leave_doc(self,doctype,name,workflow_state):
        frappe.errprint(workflow_state)
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            doc.status = 'Approved'
            doc.workflow_state = workflow_state
            doc.save(ignore_permissions=True)
            doc.submit()
        else:
            if workflow_state == 'SM Pending':
                if not doc.custom_second_manager:
                    doc.workflow_state = 'HR Pending'
                    frappe.errprint(doc.workflow_state)
                    doc.save(ignore_permissions=True)
                else:
                    doc.workflow_state = workflow_state
                    doc.save(ignore_permissions=True)
            else:
                doc.workflow_state = workflow_state
                doc.save(ignore_permissions=True)
        return "ok"

    @frappe.whitelist()
    def submit_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            frappe.errprint(doc.workflow_state)
            doc.save(ignore_permissions=True)
            doc.submit()
        # else:
        #     if workflow_state == 'SM Pending':
        #         if not doc.custom_second_manager and not doctype == "Over Time Request":
        #             doc.workflow_state = 'HR Pending'
        #             frappe.errprint(doc.workflow_state)
        #             doc.save(ignore_permissions=True)
        #         if not doc.custom_second_manager and doctype == "Over Time Request":
        #             doc.workflow_state = 'Pending for Plant Manager'
        #             frappe.errprint(doc.workflow_state)
        #             doc.save(ignore_permissions=True)
        #         else:
        #             doc.workflow_state = workflow_state
        #             doc.save(ignore_permissions=True)
        else:
            doc.workflow_state = workflow_state
            doc.save(ignore_permissions=True)
        return "ok"

    @frappe.whitelist()
    def submit_miss_punch_doc(self,doctype,name,workflow_state):
        doc = frappe.get_doc(doctype,name)
        if workflow_state == 'Approved':
            doc.save(ignore_permissions=True)
            doc.submit()
        return "ok"

    @frappe.whitelist()
    def submit_shift_doc(self,doctype,name,workflow_state):
        frappe.errprint(workflow_state)
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
                    frappe.errprint(doc.workflow_state)
                    doc.save(ignore_permissions=True)
                else:
                    doc.workflow_state = workflow_state
                    doc.save(ignore_permissions=True)
            else:
                doc.workflow_state = workflow_state
                doc.save(ignore_permissions=True)
        return "ok"