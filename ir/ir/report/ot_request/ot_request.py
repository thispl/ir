import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Emp No", "fieldname": "emp_no", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": "Emp Name", "fieldname": "emp_name", "fieldtype": "Data", "width": 180},
        {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 180},
        {"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Data", "width": 180},
        {"label": "OT Hours", "fieldname": "ot_hours", "fieldtype": "Float", "width": 180},
        {"label": "OT Amount", "fieldname": "ot_amount", "fieldtype": "Currency", "width": 180},
    ]

def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    employee = filters.get("employee")
    department = filters.get("department")

    query = """
    SELECT
        ot.employee AS emp_no,
        ot.employee_name AS emp_name,
        ot.department,ot.normal_employee,
        emp.payroll_cost_center AS cost_center,
        SUM(TIME_TO_SEC(ot.ot_hour)) / 3600 AS ot_hours,  -- Convert to hours
        ROUND((emp.custom_basic / 26 / 8) * (SUM(TIME_TO_SEC(ot.ot_hour)) / 3600) * 2, 2) AS ot_amount
    FROM `tabOver Time Request` AS ot
    LEFT JOIN `tabEmployee` AS emp ON emp.name = ot.employee
    WHERE ot.workflow_state != 'Rejected' AND ot.normal_employee =1
        AND ot.docstatus != 2
        AND ot.ot_date BETWEEN %s AND %s 
    """
    
    conditions = [from_date, to_date]

    if employee:
        query += " AND ot.employee = %s"
        conditions.append(employee)
        
    if department:
        query += " AND ot.department = %s"
        conditions.append(department)
     
     

    query += """
    GROUP BY ot.employee, ot.employee_name, ot.department, emp.payroll_cost_center, emp.custom_basic
    """

    sql_results = frappe.db.sql(query, tuple(conditions), as_dict=True)

    return sql_results
