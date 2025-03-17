from io import BytesIO
import frappe

@frappe.whitelist()
def download_esi_txt(from_date,to_date):
    filename = 'PF_Text_File'
    build_txt_response(filename,from_date,to_date)

def build_txt_response(filename,from_date,to_date):
    txt_file = make_txt(from_date,to_date)
    frappe.response['filename'] = f"{filename}.txt"
    frappe.response['filecontent'] = txt_file.getvalue()
    frappe.response['type'] = 'binary'

def make_txt(from_date, to_date):
    # Create a buffer for the text content
    txt_file = BytesIO()

    # Fetch all active salary slips with related employee UAN
    salary_slips = frappe.db.get_all(
        'Salary Slip',
        filters={'docstatus': ('!=', '2'), 'custom_agency': '', 'start_date': from_date, 'end_date': to_date},
        fields=['name', 'employee_name', 'gross_pay', 'employee', 'leave_without_pay'],
    )

    # Fetch active employees' UANs
    employee_uans = frappe.db.get_all(
        'Employee',
        filters={
            'name': ['in', [slip.employee for slip in salary_slips]],
            'status': 'Active'
        },
        fields=['name', 'uan_no', 'custom_not_applicable_for_pension'],
    )

    # Create a dictionary for UAN lookup
    uan_dict = {emp['name']: emp for emp in employee_uans}

    # Write data to file
    for slip in salary_slips:
        # Fetch earnings for the current Salary Slip
        earnings = frappe.db.get_all(
            'Salary Detail',
            filters={'parent': slip.name},
            fields=['amount', 'salary_component'],
        )

        # Get employee data for UAN and custom_not_applicable_for_pension
        employee_data = uan_dict.get(slip.employee)
        uan_no = employee_data['uan_no'] if employee_data else ''
        custom_not_applicable_for_pension = employee_data['custom_not_applicable_for_pension'] if employee_data else 0

        # Get Basic Salary and PF Deduction amounts
        basic_salary = next((earning['amount'] for earning in earnings if earning['salary_component'] == 'Basic'), 0)
        pf_deduction = next((earning['amount'] for earning in earnings if earning['salary_component'] == 'Deduction PF'), 0)

        # Cap Basic Salary at 15,000
        capped_basic_salary = min(basic_salary, 15000)

        # Calculate EPS Wages and other contributions
        eps_wages = 0 if custom_not_applicable_for_pension == 1 else capped_basic_salary
        eps_contribution_remitted = round(capped_basic_salary * 0.0833, 0)
        epf_and_eps_diff_remitted = round(capped_basic_salary * 0.0367, 0) if custom_not_applicable_for_pension == 0 else 0

        # Prepare row in the required format
        row = f"{uan_no}#~#{slip.employee_name}#~#{round(slip.gross_pay, 0)}#~#{capped_basic_salary}#~#{capped_basic_salary}#~#{capped_basic_salary}#~#{eps_contribution_remitted}#~#{epf_and_eps_diff_remitted}#~#{pf_deduction}#~#{slip.leave_without_pay}#~#0"
        
        # Write row to the file
        txt_file.write((row + "\n").encode('utf-8'))

    txt_file.seek(0)  # Move the cursor to the beginning of the file
    return txt_file