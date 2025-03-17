# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import money_in_words

class AgencyInvoice(Document):
	pass

#Total amount has been changed as words
@frappe.whitelist()
def get_total_amount_in_words(total_amount):
        total_amt = float(total_amount)
        if total_amt > 0:
            return money_in_words(total_amt)
    # except ValueError:
    #     return "Invalid amount"

    
@frappe.whitelist()
def get_md(agency, start_date, end_date, designation):
    gross_salary = frappe.get_value("Employee", {"designation": designation, "custom_agency_name": agency}, "custom_gross") or 0
    mdr = frappe.get_value('Agency Wages', {'designation': designation, 'parent': agency}, 'gross')
    tar = frappe.get_value('Agency Wages', {'designation': designation, 'parent': agency}, 'travel_allowance_rate')

    man_days = frappe.db.sql("""
        SELECT SUM(payment_days) AS total_payment_days 
        FROM `tabSalary Slip` 
        WHERE docstatus != 2 AND custom_agency = %s AND start_date = %s AND end_date = %s AND designation = %s
    """, (agency, start_date, end_date, designation), as_dict=True)[0]

    overtime = frappe.db.sql("""
        SELECT SUM(custom_overtime) AS total_overtime 
        FROM `tabSalary Slip` 
        WHERE docstatus != 2 AND custom_agency = %s AND start_date = %s AND end_date = %s AND designation = %s
    """, (agency, start_date, end_date, designation), as_dict=True)[0]
    
    total_working_days_data = frappe.db.sql("""
        SELECT SUM(total_working_days) AS total_working 
        FROM `tabSalary Slip` 
        WHERE docstatus != 2 AND custom_agency = %s AND start_date = %s AND end_date = %s AND designation = %s
    """, (agency, start_date, end_date, designation), as_dict=True)[0]

  
    total_working_days = total_working_days_data.get("total_working", 0) or 0

    # one_hour_ot_amount = float(gross_salary / (total_working_days * 8)) if total_working_days > 0 else 0.0
    
    one_hour_ot_amount = frappe.db.sql("""
        SELECT overtime 
        FROM `tabAgency Wages` 
        WHERE parent = %s 
        AND designation = %s
    """, (agency, designation), as_dict=True)
    
    ot_amount = float(one_hour_ot_amount[0]["overtime"]) if one_hour_ot_amount else 0.0


    total_overtime = float(overtime.get("total_overtime", 0) or 0)
    earnings = total_overtime * ot_amount
    
    # earnings = frappe.db.sql("""
    #     SELECT salary_component, SUM(amount) AS total_amount
    #     FROM `tabSalary Detail` 
    #     WHERE parent IN (
    #         SELECT name FROM `tabSalary Slip` 
    #         WHERE salary_component ='OT' AND docstatus != 2 AND custom_agency = %s AND start_date = %s AND end_date = %s AND designation = %s
    #     )
    
    # """, (agency, start_date, end_date, designation), as_dict=True)[0]
    
    canteen = frappe.db.sql("""
        SELECT salary_component, SUM(amount) AS de_total_amount
        FROM `tabSalary Detail` 
        WHERE parent IN (
            SELECT name FROM `tabSalary Slip` 
            WHERE salary_component ='Canteen' AND docstatus != 2 AND custom_agency = %s AND start_date = %s AND end_date = %s AND designation = %s
        )
        
    """, (agency, start_date, end_date, designation), as_dict=True)[0]
    
    attndance_bounus = frappe.db.sql("""
        SELECT salary_component, SUM(amount) AS canteen_total_amount
        FROM `tabSalary Detail` 
        WHERE parent IN (
            SELECT name FROM `tabSalary Slip` 
            WHERE salary_component ='Attendance Bonus' AND docstatus != 2 AND custom_agency = %s AND start_date = %s AND end_date = %s AND designation = %s
        )
    """, (agency, start_date, end_date, designation), as_dict=True)[0]


    return (
        man_days.get('total_payment_days', 0) or 0, 
        mdr, 
        tar, 
        overtime.get('total_overtime', 0) or 0,
        earnings or 0,
        one_hour_ot_amount[0]['overtime'] if one_hour_ot_amount else 0,
        canteen.get('de_total_amount',0) or 0,
        attndance_bounus.get('canteen_total_amount',0) or 0
    )
