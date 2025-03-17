# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt

import erpnext

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
employee=frappe.qb.DocType("Employee")
salary_component = frappe.qb.DocType("Salary Component")


def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips)
	columns = get_columns(earning_types, ded_types)

	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")

	doj_map = get_employee_doj_map()
	cost_center = get_employee_cost_center()
	group = get_employee_group()
	data = []
	s_no = 1
	for ss in salary_slips:
		row = {
			"S.No": s_no,
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"data_of_joining": doj_map.get(ss.employee),
			"cost_center":cost_center.get(ss.employee),
			"employee_category":ss.custom_employee_category,
			"group":group.get(ss.employee),
			# "branch": ss.branch,
			"department": ss.department,
			"designation": ss.designation,
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": flt(ss.leave_without_pay) + flt(ss.absent_days),
			"payment_days": ss.payment_days,
			"currency": currency or company_currency,
			"present_days": ss.custom_present_days_holiday,
			# "total_loan_repayment": ss.total_loan_repayment,
   			
		}
		s_no += 1


		update_column_width(ss, columns)

		for e in earning_types:
			row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e)})

		for d in ded_types:
			row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d)})

		if currency == company_currency:
			row.update(
				{
					"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
					"total_deduction": flt(ss.total_deduction) * flt(ss.exchange_rate),
					"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
				}
			)

		else:
			row.update(
				{"gross_pay": ss.gross_pay, "total_deduction": ss.total_deduction, "net_pay": ss.net_pay}
			)

		data.append(row)

	return columns, data


def get_earning_and_deduction_types(salary_slips):
	salary_component_and_type = {_("Earning"): [], _("Deduction"): []}

	for salary_compoent in get_salary_components(salary_slips):
		component_type = get_salary_component_type(salary_compoent)
		salary_component_and_type[_(component_type)].append(salary_compoent)

	return sorted(salary_component_and_type[_("Earning")]), sorted(
		salary_component_and_type[_("Deduction")]
	)


def update_column_width(ss, columns):
	# if ss.branch is not None:
	# 	columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		columns[9].update({"width": 120})


def get_columns(earning_types, ded_types):
	columns = [
		{
			"label": _("S.No"),
			"fieldname": "s_no",
			"fieldtype": "Int",
			"width": 70,
		},
  		# {
		# 	"label": _("Salary Slip ID"),
		# 	"fieldname": "salary_slip_id",
		# 	"fieldtype": "Link",
		# 	"options": "Salary Slip",
		# 	"width": 150,
		# },
		{
			"label": _("Emp No"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Emp Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
  		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 100,
		},
		{
			"label": _("Employee Category"),
			"fieldname": "employee_category",
			"fieldtype": "Data",
			"width": 80,
		},
    	{
			"label": _("Cost Center"),
			"fieldname": "cost_center",
			"fieldtype": "Data",
			"width": 80,
		},
     	{
			"label": _("Group"),
			"fieldname": "group",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Date of Joining"),
			"fieldname": "data_of_joining",
			"fieldtype": "Date",
			"width": 80,
		},
		# {
		# 	"label": _("Branch"),
		# 	"fieldname": "branch",
		# 	"fieldtype": "Link",
		# 	"options": "Branch",
		# 	"width": -1,
		# },
  		{
			"label": _("Payment Days"),
			"fieldname": "payment_days",
			"fieldtype": "Float",
			"width": 120,
		},
    	{
			"label": _("Present Days"),
			"fieldname": "present_days",
			"fieldtype": "Float",
			"width": 120,
		},
    	{
			"label": _("Leave Without Pay"),
			"fieldname": "leave_without_pay",
			"fieldtype": "Float",
			"width": 50,
		},
		# {
		# 	"label": _("Company"),
		# 	"fieldname": "company",
		# 	"fieldtype": "Link",
		# 	"options": "Company",
		# 	"width": 120,
		# },
		# {
		# 	"label": _("Start Date"),
		# 	"fieldname": "start_date",
		# 	"fieldtype": "Data",
		# 	"width": 80,
		# },
		# {
		# 	"label": _("End Date"),
		# 	"fieldname": "end_date",
		# 	"fieldtype": "Data",
		# 	"width": 80,
		# },
	]

	# Define the order of earnings and deductions
	ordered_earnings = ["Basic", "House Rent Allowance", "Travelling Allowance", "CCA","Other Earn","Other","Earning Income Tax","Salary Arrear", "Special Allowance", "OT","OT Arrear"]
	ordered_deductions = ["Deduction PF", "Deduction ESI","Other/ Advance Deduction","Professional Tax", "Tax Deducted Source", "Canteen", "Labour Welfare Fund" , "LIC"]

	# Add earnings in the specified order if they exist in earning_types
	for earning in ordered_earnings:
		if earning in earning_types:
			columns.append(
				{
					"label": earning,
					"fieldname": frappe.scrub(earning),
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120,
				}
			)
	# Add the Gross Pay column
	columns.append(
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
	)

	# Add deductions in the specified order if they exist in ded_types
	for deduction in ordered_deductions:
		if deduction in ded_types:
			columns.append(
				{
					"label": deduction,
					"fieldname": frappe.scrub(deduction),
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120,
				}
			)

	# Add remaining columns
	columns.extend(
		[
			# {
			# 	"label": _("Loan Repayment"),
			# 	"fieldname": "total_loan_repayment",
			# 	"fieldtype": "Currency",
			# 	"options": "currency",
			# 	"width": 120,
			# },
			{
				"label": _("Total Deduction"),
				"fieldname": "total_deduction",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Net Pay"),
				"fieldname": "net_pay",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Currency"),
				"fieldtype": "Data",
				"fieldname": "currency",
				"options": "Currency",
				"hidden": 1,
			},
		]
	)
	return columns



def get_salary_components(salary_slips):
	return (
		frappe.qb.from_(salary_detail)
		.where((salary_detail.amount != 0) & (salary_detail.parent.isin([d.name for d in salary_slips])))
		.select(salary_detail.salary_component)
		.distinct()
	).run(pluck=True)


def get_salary_component_type(salary_component):
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)


def get_salary_slips(filters, company_currency):
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	query = (
    frappe.qb.from_(salary_slip)
    .join(employee)
    .on(employee.name == salary_slip.employee)
    .where(
        (employee.custom_normal_employee == 1) &
        ((salary_slip.custom_agency == "") | salary_slip.custom_agency.isnull())
    )
    .select(
        salary_slip.name,
        salary_slip.employee,
        salary_slip.employee_name,
        salary_slip.gross_pay,
        salary_slip.net_pay,
        salary_slip.department,
        salary_slip.custom_agency,
        employee.employment_type,
        employee.custom_normal_employee,
        salary_slip.total_deduction,
        salary_slip.start_date,
        salary_slip.end_date,
        salary_slip.designation,
        salary_slip.company,
        salary_slip.exchange_rate,
        salary_slip.leave_without_pay,
        salary_slip.absent_days,
        salary_slip.payment_days,
        salary_slip.custom_present_days_holiday,
        salary_slip.custom_employee_category
        # salary_slip.branch,
    )
)

    
	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.start_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.end_date <= filters.get("to_date"))

	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))

	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))

	salary_slips = query.run(as_dict=1)

	return salary_slips or []


def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)

def get_employee_cost_center():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name,employee.payroll_cost_center)).run()

	return frappe._dict(result)

def get_employee_group():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name,employee.custom_group)).run()

	return frappe._dict(result)

def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
	salary_slips = [ss.name for ss in salary_slips]

	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
		)
	).run(as_dict=1)

	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map
