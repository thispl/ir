app_name = "ir"
app_title = "IR"
app_publisher = "TEAMPROO"
app_description = "Customizations for IR"
app_email = "erp@groupteampro.com"
app_license = "mit"



# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ir/css/ir.css"
# app_include_js = "/assets/ir/js/ir.js"

# include js, css files in header of web template
# web_include_css = "/assets/ir/css/ir.css"
# web_include_js = "/assets/ir/js/ir.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ir/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ir/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ir.utils.jinja_methods",
# 	"filters": "ir.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ir.install.before_install"
# after_install = "ir.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ir.uninstall.before_uninstall"
# after_uninstall = "ir.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ir.utils.before_app_install"
# after_app_install = "ir.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ir.utils.before_app_uninstall"
# after_app_uninstall = "ir.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ir.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Salary Slip": "ir.overrides.CustomSalarySlip",
 	"Attendance Regularize":"ir.overrides.CustomAttendanceRegularize"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
#     "Warning":{
#         "validate":["ir.utils.new_occurrence_count"]
# 	}
    "Compensatory Off Request":{
		"validate": ["ir.ir.doctype.compensatory_off_request.compensatory_off_request.comp_off_applicable","ir.ir.doctype.compensatory_off_request.compensatory_off_request.comp_off_req","ir.ir.doctype.compensatory_off_request.compensatory_off_request.validate_comp_off_app"],
		"on_submit":["ir.ir.doctype.compensatory_off_request.compensatory_off_request.comp_off_allocation","ir.ir.doctype.compensatory_off_request.compensatory_off_request.submitted_date"],
		"on_cancel":"ir.ir.doctype.compensatory_off_request.compensatory_off_request.comp_off_revert",
	},
	"Attendance":{
		"validate":["ir.custom.update_ot_request"],
  		"on_submit":"ir.utils.compoff_for_ot",
    	"on_update":"ir.utils.update_shift"

	},
 
	"Shift Request":{
		"before_submit": "ir.utils.shift_change_req",
	},
	"Agency":{
		"validate":"ir.ir.doctype.agency.agency.salary_comp"
	},
	"Leave Application":{
		"validate": ["ir.custom.restrict_for_zero_balance","ir.custom.check_on_duty"],
	},
	# "Permission Request":{
	# 	"after_insert": ["ir.email_alerts.after_inserts"],
    #  },
    "Shift Schedule":{
		"on_cancel":["ir.ir.doctype.shift_schedule.shift_schedule.shift_cancel"],
     },
    # "Attendance":{
	# 	"on_update":["ir.utils.update_hours_alternate"]
	# },
    # "Attendance":{
	# 	"on_update":["ir.utils.update_hours"]
	# }
    
	# "On Duty Application":{
	#	"after_insert": ["ir.email_alerts.after_insert"],
	# },
	# "Miss Punch Application":{
	# 	"after_insert": ["ir.utils.validate_miss_punch"]
	# },
	
}


# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		"00 09 1 * *":[
			"ir.custom.update_earned_leave"
		],
		"*/15 * * * *":[
			"ir.mark_attendance.mark_att_process"
		]
	},
	# "all": [
	# 	"ir.tasks.all"
	# ],
	"daily": [
		"ir.tasks.daily"
	],
	# "hourly": [
	# 	"ir.tasks.hourly"
	# ],
	# "weekly": [
	# 	"ir.tasks.weekly"
	# ],
	# "monthly": [
	# 	"ir.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "ir.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ir.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ir.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ir.utils.before_request"]
# after_request = ["ir.utils.after_request"]

# Job Events
# ----------
# before_job = ["ir.utils.before_job"]
# after_job = ["ir.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ir.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

