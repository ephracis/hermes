""" This file contains code for performing static code analysis on APK files. """

try:
	import mallodroid
except:
	print("error: could not find Mallodroid, make sure you have downloaded it and set your python path.")
	exit(1)

def analyze(apps, filename, app):
	""" Performs a static code analysis on an app.
		
		Arguments:
		apps     -- a dictionary with all apps and their meta data where the results will be stored
		filename -- the filename of the app's apk
		app      -- the ID of the app
		"""
	try:
		_a = mallodroid.apk.APK(filename)
		_vm = mallodroid.dvm.DalvikVMFormat(_a.get_dex())
		_vmx = mallodroid.uVMAnalysis(_vm)
		_vm.create_python_export()
		_gx = mallodroid.GVMAnalysis(_vmx, None)
		
		_vm.set_vmanalysis(_vmx)
		_vm.set_gvmanalysis(_gx)
		_vm.create_dref(_vmx)
		_vm.create_xref(_vmx)
		
		_result = {'trustmanager' : [], 'hostnameverifier' : [], 'onreceivedsslerror' : []}
		_result = mallodroid._check_all(_vm, _vmx, _gx)
		
		trustmanagers = len(_result['trustmanager'])
		naive_trustmanagers = 0
		factories = len(_result['insecuresocketfactory'])
		verifiers = len(_result['customhostnameverifier'])
		naive_verifiers = 0
		allhostnames = len(_result['allowallhostnameverifier'])
		errorhandlers = len(_result['onreceivedsslerror'])
		
		if trustmanagers > 0:
			for tm in _result['trustmanager']:
				if tm['empty']:
					naive_trustmanagers += 1
		if verifiers > 0:
			for hv in _result['customhostnameverifier']:
				if hv['empty']:
					naive_verifiers += 1
		
		apps[app]['unchecked'] = False
		apps[app]['trustmanagers'] = trustmanagers
		apps[app]['naive_trustmanagers'] = naive_trustmanagers
		apps[app]['insecure_factories'] = factories
		apps[app]['custom_hostname_verifiers'] = verifiers
		apps[app]['naive_hostname_verifiers'] = naive_verifiers
		apps[app]['allow_all_hostname_verifiers'] = allhostnames
		apps[app]['ssl_error_handlers'] = errorhandlers
	
	except:
		None