import frappe
from frappe.utils import add_days

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 180},
        {"label": "Attendance", "fieldname": "attendance", "fieldtype": "Link", "options": "Attendance", "width": 180},
        {"label": "Attendance Date", "fieldname": "attendance_date", "fieldtype": 'Date', "width": 180},
        {"label": "Reason", "fieldname": "reason", "fieldtype": 'Data', "width": 180},
    ]

def get_data(filters):
    # Default dates if not provided
    from_date = filters.get("from_date") or add_days(frappe.utils.today(), -7)  # Default to last 7 days if not specified
    to_date = filters.get("to_date") or frappe.utils.today()
    employee = filters.get("employee")

    # Constructing the base query
    query = """
        SELECT 
            a.employee, 
            a.employee_name, 
            a.department, 
            a.name as attendance,
            a.attendance_date,
            b.employee,
            b.shift_type,
            b.start_date,
            b.name,
            CASE 
                WHEN a.in_time IS NULL OR a.out_time IS NULL THEN 'Absent'
                WHEN a.shift != b.shift_type THEN 'Wrong Shift'
                ELSE  'Absent'
                
            END AS reason
        FROM 
            `tabAttendance` as a
            JOIN `tabShift Assignment` as b
            ON
                a.employee = b.employee and a.attendance_date = b.start_date
        WHERE 
            a.attendance_date BETWEEN %s AND %s
            AND a.status = 'Absent'
            AND a.docstatus=b.docstatus < 2
    """
    query_conditions = [from_date, to_date]

    # Adding employee filter if specified
    if employee:
        query += " AND a.employee = %s"
        query_conditions.append(employee)

    # Adding order by clause
    query += " ORDER BY a.attendance_date"

    # Execute the query
    records = frappe.db.sql(query, query_conditions, as_dict=True)
    
    data = []
    for record in records:
        data.append({
            "employee": record.employee,
            "employee_name": record.employee_name,
            "department": record.department,
            "attendance": record.attendance,
            "attendance_date": record.attendance_date,
            "reason": record.reason
        })
    
    return data
