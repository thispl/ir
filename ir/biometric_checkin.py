import frappe
@frappe.whitelist(allow_guest=True)
def mark_checkin(**args):
	if frappe.db.exists('Employee',{'attendance_device_id':args['employee'],'status':'Active'}):
		emp=frappe.get_doc("Employee",{'attendance_device_id':args['employee'],'status':'Active'})
		if not frappe.db.exists('Employee Checkin',{'employee':emp.name,'time':args['time']}):
			ec = frappe.new_doc('Employee Checkin')
			ec.employee = emp.name
			ec.time = args['time']
			ec.device_id = args['device_id']
			if args['logtype']=='Walk-IN' or args['logtype']=='Bike-IN':
				ec.log_type = 'IN'
			else:
				ec.log_type ='OUT'
			ec.save(ignore_permissions=True)
			frappe.db.commit()
			return "Checkin Marked"
	else:
		if not frappe.db.exists('Unregistered Employee Checkin',{'biometric_pin':args['employee'],'biometric_time':args['time']}):
			ec = frappe.new_doc('Unregistered Employee Checkin')
			ec.biometric_pin = args['employee'].upper()
			ec.biometric_time = args['time']
			ec.locationdevice_id = args['device_id']
			if args['device_id'] == 'IN':
				ec.log_type = 'IN'
			else: 
				ec.log_type = 'OUT'
			ec.save(ignore_permissions=True)
			frappe.db.commit()
			return "Checkin Marked" 
		else:
			return "Checkin Marked"	
	
