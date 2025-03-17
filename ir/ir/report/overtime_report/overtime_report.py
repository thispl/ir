# Copyright (c) 2024, TEAMPROO and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days, date_diff
from math import floor
from frappe import msgprint, _
from calendar import monthrange
from datetime import date, timedelta, datetime, time

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        _("Employee ID") + ":Data:100",
        _("Employee Name") + ":Data:150",
        _("Designation") + ":Data:170",
        _("Department") + ":Data:150",
        _("Cost Center") + ":Data:150",
        _("Category") + ":Data:150",
    ]

    # Get dates and format columns dynamically
    dates = get_dates(filters.from_date, filters.to_date)
    for date in dates:
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%b')
        columns.append(_(formatted_date) + ":Float:70")

    columns.append(_("Total") + ":Float:100")  # Total OT column
    return columns

def get_data(filters):
    data = []
    dates = get_dates(filters.from_date, filters.to_date)

    # Fetch employee filter conditions
    employee_conditions = get_employees(filters)

    # Dictionary to store OT hours per employee
    ot_data = {}

    # Prepare filter dictionary
    ot_filters = {
        'ot_date': ['between', [filters.from_date, filters.to_date]],
        'docstatus': ['!=', 2],
        "normal_employee": 1
    }

    # Apply employee filters dynamically
    if employee_conditions:
        ot_filters.update(employee_conditions)

    ot_records = frappe.get_all(
        'Over Time Request',
        filters=ot_filters,
        fields=['ot_date', 'ot_hour', 'employee', 'employee_name', 'department', 'designation', 'employee_category']
    )

    for record in ot_records:
        payroll_cost_center = frappe.db.get_value("Employee", {"name": record.employee}, "payroll_cost_center")
        
        # Convert OT hours
        ot_hours = convert_hhmmss_to_hours(record.ot_hour) if record.ot_hour else 0
        
        # Convert ot_date to string format
        ot_date_str = str(record.ot_date)

        if record.employee not in ot_data:
            ot_data[record.employee] = {
                'employee': record.employee,
                'employee_name': record.employee_name,
                'designation': record.designation,
                'department': record.department,
                'cost_center': payroll_cost_center,
                'category': record.employee_category,
                'dates': {d: 0 for d in dates},  # Initialize date-wise OT tracking
                'total_ot': 0
            }

        # Ensure the key exists in the dictionary before updating
        if ot_date_str in ot_data[record.employee]['dates']:
            ot_data[record.employee]['dates'][ot_date_str] += ot_hours
            ot_data[record.employee]['total_ot'] += ot_hours

    # Convert dictionary into list format
    for employee, details in ot_data.items():
        row = [
            details['employee'],
            details['employee_name'],
            details['designation'],
            details['department'],
            details['cost_center'],
            details['category'],
        ]
        
        # Append OT hours per date
        for date in dates:
            row.append(details['dates'][date])
        
        # Append total OT
        row.append(details['total_ot'])
        data.append(row)

    return data


def get_dates(from_date, to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    return [add_days(from_date, i) for i in range(no_of_days)]

def get_employees(filters):
    conditions = {}
    if filters.get("employee"):
        conditions["employee"] = filters.employee
    if filters.get("custom_employee_category"):
        conditions["employee_category"] = filters.custom_employee_category

    return conditions

@frappe.whitelist()
def convert_hhmmss_to_hours(time_str):
    if isinstance(time_str, timedelta):
        return time_str.total_seconds() / 3600  # Convert timedelta to float hours
    elif isinstance(time_str, str):  
        try:
            h, m, s = map(int, time_str.split(':'))
            return h + m / 60 + s / 3600  # Convert HH:MM:SS to float hours
        except ValueError:
            return 0  # Return 0 if invalid format
    return 0
