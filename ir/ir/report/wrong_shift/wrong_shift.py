import frappe
from frappe.utils import add_days, format_date

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
        {"label": "Attended Shift", "fieldname": "attended_shift", "fieldtype": 'Data', "width": 180},
        {"label": "Assigned Shift", "fieldname": "assigned_shift", "fieldtype": 'Data', "width": 180}
    ]

def get_data(filters):
    # Get filters from the report
    from_date = filters.get("from_date") or add_days(frappe.utils.today(), -7)  # Default to last 7 days if not specified
    to_date = filters.get("to_date") or frappe.utils.today()
    employee = filters.get("employee")

    # Constructing the base query with date range
    query = """
        SELECT 
            employee, 
            employee_name, 
            department, 
            name as attendance,
            attendance_date,
            shift as attended_shift
        FROM 
            `tabAttendance`
        WHERE 
            attendance_date BETWEEN %s AND %s
            AND docstatus != 2 and shift !=%s
    """
    query_conditions = [from_date, to_date,'']

    # Adding employee filter if specified
    if employee:
        query += " AND employee = %s"
        query_conditions.append(employee)

    # Execute the query
    records = frappe.db.sql(query, query_conditions, as_dict=True)
    
    data = []
    for record in records:
        # Fetch assigned shift
        assigned_shift = frappe.get_value(
            "Shift Assignment",
            {
                'employee': record.employee,
                'start_date': ('<=', record.attendance_date),
                'end_date': ('>=', record.attendance_date),
                'docstatus': 1
            },
            ['shift_type']
        ) or ''
        
        # Check if shift is wrong
        if record.attended_shift != assigned_shift:
            data.append({
                "employee": record.employee,
                "employee_name": record.employee_name,
                "department": record.department,
                "attendance": record.attendance,
                "attendance_date": record.attendance_date,
                "attended_shift": record.attended_shift,
                "assigned_shift": assigned_shift
            })
    
    return data
