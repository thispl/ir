import frappe
from frappe.utils import add_days

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # {"label": "S.No", "fieldname": "serial_no", "fieldtype": "Int", "width": 50},
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 180},
        {"label": "On Duty Application", "fieldname": "on_duty", "fieldtype": "Link", "options": "On Duty Application", "width": 180},
        {"label": "Session", "fieldname": "from_date_session", "fieldtype": "Data", "width": 180}
    ]

def get_data(filters):
   
    from_date = filters.get("from_date") or add_days(frappe.utils.today(), -1)
    to_date = filters.get("to_date") or frappe.utils.today()
    employee = filters.get("employee")

    
    query = """
        SELECT 
            `tabOn Duty Application`.employee, 
            `tabOn Duty Application`.employee_name, 
            `tabOn Duty Application`.department, 
            `tabOn Duty Application`.name as on_duty, 
            `tabOn Duty Application`.from_date_session
        FROM 
            `tabOn Duty Application`
        WHERE 
            `tabOn Duty Application`.from_date BETWEEN %s AND %s 
            AND `tabOn Duty Application`.docstatus = 1
    """
    query_conditions = [from_date, to_date]

    
    if employee:
        query += " AND `tabOn Duty Application`.employee = %s"
        query_conditions.append(employee)

    employees = frappe.db.sql(query, query_conditions, as_dict=True)
    
    data = []
    for emp in employees:
        data.append({
            # "serial_no": idx,
            "employee": emp.employee,  
            "employee_name": emp.employee_name,
            "department": emp.department,
            "on_duty": emp.on_duty,
            "from_date_session": emp.from_date_session or ''
        })
    
    return data
