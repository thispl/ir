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
        {"label": "Permission Request", "fieldname": "permission", "fieldtype": 'Link', "options": "Permission Request", "width": 180},
        {"label": "Session", "fieldname": "session", "fieldtype": "Data", "width": 180}
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
            name as permission,
            attendance_date,
            session
        FROM 
            `tabPermission Request`
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
    query += " ORDER BY attendance_date"

    # Execute the query
    permission_records = frappe.db.sql(query, query_conditions, as_dict=True)
    
    data = []
    for record in permission_records:
        data.append({
            "employee": record.employee,
            "employee_name": record.employee_name,
            "department": record.department,
            "permission": record.permission,
            "session": record.session or ''
        })
    
    return data
