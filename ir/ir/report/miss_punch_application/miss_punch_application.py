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
        {"label": "Attendance Date", "fieldname": "attendance_date", "fieldtype": 'Date', "width": 180},
        {"label": "Attendance", "fieldname": "attendance", "fieldtype": 'Link',"options":"Attendance", "width": 180},
        {"label": "In Time", "fieldname": "in_time", "fieldtype": "Time", "width": 100},
        {"label": "Out Time", "fieldname": "out_time", "fieldtype": "Time", "width": 100},
        {"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    # Default dates if not provided
    from_date = filters.get("from_date") or add_days(frappe.utils.today(), -1)
    to_date = filters.get("to_date") or frappe.utils.today()
    employee = filters.get("employee")

    # Constructing the base query
    query = """
        SELECT 
            employee, 
            employee_name, 
            department, 
            attendance_date,
            name as attendance, 
            in_time, 
            out_time, 
            shift 
        FROM 
            `tabAttendance`
        WHERE 
            attendance_date BETWEEN %s AND %s 
            AND docstatus != 2
    """

    query_conditions = [from_date, to_date]

    # Adding employee filter if specified
    if employee:
        query += " AND employee = %s"
        query_conditions.append(employee)

    # Adding order by clause
    query += " ORDER BY attendance_date, shift"

    # Execute the query
    attendance_records = frappe.db.sql(query, query_conditions, as_dict=True)
    
    data = []
    for record in attendance_records:
        if not record.in_time and record.out_time:
            data.append({
                "employee": record.employee,
                "employee_name": record.employee_name,
                "department": record.department,
                "attendance_date": record.attendance_date,
                "attendance": record.attendance,  	
                "in_time": record.in_time or '',
                "out_time": record.out_time or '',
                "shift": record.shift or ''
            })
        if record.in_time and not record.out_time:
            data.append({
                "employee": record.employee,
                "employee_name": record.employee_name,
                "department": record.department,
                "attendance_date": record.attendance_date,
                "attendance": record.attendance,  	
                "in_time": record.in_time or '',
                "out_time": record.out_time or '',
                "shift": record.shift or ''
            })
    
    return data
