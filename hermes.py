#!/usr/bin/env python
# encoding: utf-8

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import sys
import urlparse
import imp
import pickle
import re
import time
import operator
import os
import argparse
import math
from pprint import pprint
from google.protobuf import text_format

try:
	from googleplay import GooglePlayAPI
except:
	print("error: could not find GooglePlayAPI, make sure you have downloaded it and set your python path.")
	exit(1)

try:
	import mallodroid
except:
	print("error: could not find Mallodroid, make sure you have downloaded it and set your python path.")
	exit(1)

animation = ["-", "\\", "|", "/"]
animation_pos = 0
animation_last = time.time()

def animate():
	""" Print animation. Note: this will overwrite the previous two characters. """
	global animation_last
	global animation_pos
	# only animate every 100ms
	if time.time() - animation_last > 0.1:
		animation_last = time.time()
		animation_pos += 1
		sys.stdout.write("\b\b%s " % (animation[animation_pos % len(animation)]))
		sys.stdout.flush()

def fixName(category):
	""" Turn the category name into human readable form. """
	exceptions = ['a', 'an', 'of', 'the', 'is', 'and', 'with', 'by']
	fixed = title_except(re.sub('_',' ',category), exceptions)
	if fixed == "App Wallpaper":
		fixed = "Live Wallpaper"
	elif fixed == "App Widgets":
		fixed = "Widgets"
	return fixed

def roundUp(number):
	""" Round up an integer to the nearest power of then of the same degree.
	Exempel: 35 -> 40, 540 -> 600, 1250 -> 2000, etc """
	nearest = math.pow(10,len(str(number))-1)
	return int(math.ceil(number / nearest) * nearest)

def title_except(s, exceptions):
	""" Titlelize a string with exceptions. """
	word_list = re.split(' ', s.lower())       #re.split behaves as expected
	final = [word_list[0].capitalize()]
	for word in word_list[1:]:
		final.append(word in exceptions and word or word.capitalize())
	return " ".join(final)

def makeUnique(list):
	""" Removes duplicates from a list. """
	u = []
	for l in list:
		if not l in u:
			u.append(l)
	return u

def str2float(str):
	""" convert a string to a float """
	try:
		return float(re.sub("[^0-9\.]", "", str))
	except:
		return 0

def moreThanOne(dict, key):
	""" Checks if a key in a dictionary has a value more than one.
	
	Arguments:
	dict -- the dictionary
	key  -- the key
	
	Returns:
	True if the key exists in the dictionary and the value is at least one, otherwise false
	"""
	return key in dict and dict[key] > 0

def anyMoreThanOne(dict, keys):
	""" Checks if any of a list of keys in a dictionary has a value more than one.
	
	Arguments:
	dict -- the dictionary
	keys -- the keys
	
	Returns:
	True if any key exists in the dictionary and the value is at least one, otherwise false
	"""
	for key in keys:
		if key in dict and dict[key] > 0:
			return True
	return False

def isVulnerable(app):
	""" Checks if an app contains a vulnerability.
	
	Arguments:
	app -- dictionary with meta data of the app to check
	
	Returns:
	True if the app is vulnerable, otherwise False
	"""
	bad_properties = ['naive_trustmanagers','insecure_factories','naive_hostname_verifiers','allow_all_hostname_verifiers']
	return anyMoreThanOne(app,bad_properties)
	
def ratingRange(app):
	""" Get the rating range of an app. """
	rating = 'Unknown'
	r = app['rating']
	if r > 0 and r <= 1:
		rating = '0-1'
	elif r > 1 and r <= 2:
		rating = '1-2'
	elif r > 2 and r <= 3:
		rating = '2-3'
	elif r > 3 and r <= 4:
		rating = '3-4'
	elif r > 4 and r <= 5:
		rating = '4-5'
	return rating
	
def downloadRange(app):
	""" Get the download range of an app. """
	downloads = '0-100'
	d = int(app['downloads'])
	if d >= 100 and d < 10000:
		downloads = '100-10,000'
	elif d >= 10000 and d < 1000000:
		downloads = '10,000-1,000,000'
	elif d >= 1000000 and d < 100000000:
		downloads = '1,000,000-100,000,000'
	elif d >= 100000000:
		downloads = '100,000,000+'
	return downloads
	
def login(id, mail, password, token):
	""" Login to the Google Play Store.
	
	You can either specify the mail and password, or use
	a valid auth token.
	
	Arguments:
	id       -- the android phone ID
	mail     -- the email address of the account
	password -- the password of the account
	token    -- a valid auth token
	
	Returns:
	A Google Play API object.
	"""
	api = GooglePlayAPI(id)
	api.login(mail, password, token)
	return api

def constructLimitsOffsets(limit, offset):
	""" Create a list of limit and offset pairs for partial fetching of maximum 100 apps.
	
	Arguments:
	limit  -- the number of apps to fetch
	offset -- the offset from where to start fetching
	
	Returns:
	A list of limit,offset pairs where limit is no larger than 100
	"""
	limitOffsets = []
	while limit > 100:
		limitOffsets.append(('100', str(offset) if offset > 0 else None))
		offset += 100
		limit -= 100
	limitOffsets.append((str(limit), str(offset) if offset > 0 else None))
	return limitOffsets

def initStats(stats):
	""" Initialize a dictionary of statistics. """
	fields = ['total', 'internet', 'trustmanagers', 'naive_trustmanagers',
		'insecure_factories','custom_hostname_verifiers','naive_hostname_verifiers',
		'allow_all_hostname_verifiers','ssl_error_handlers','unchecked','vulnerable']
	for field in fields:
		if not field in stats:
			stats[field] = 0
	
def fillStats(app, meta, stats):
	""" Add an app into a collection of statistics.
	
	Arguments:
	app   -- app doc ID
	meta  -- meta data for app
	stats -- dictionary with statistics
	"""
	initStats(stats)
	stats['total'] += 1
	if meta['internet']:
		stats['internet'] += 1
		if moreThanOne(meta, 'trustmanagers'):
			stats['trustmanagers'] += 1
		if moreThanOne(meta, 'naive_trustmanagers'):
			stats['naive_trustmanagers'] += 1
		if moreThanOne(meta, 'insecure_factories'):
			stats['insecure_factories'] += 1
		if moreThanOne(meta, 'custom_hostname_verifiers'):
			stats['custom_hostname_verifiers'] += 1
		if moreThanOne(meta, 'naive_hostname_verifiers'):
			stats['naive_hostname_verifiers'] += 1
		if moreThanOne(meta, 'allow_all_hostname_verifiers'):
			stats['allow_all_hostname_verifiers'] += 1
		if moreThanOne(meta, 'ssl_error_handlers'):
			stats['ssl_error_handlers'] += 1
		if not 'trustmanagers' in meta:
			stats['unchecked'] += 1	
		if isVulnerable(meta):
			stats['vulnerable'] += 1

def calculateStatistics(apps):
	""" Calculates the statistics of apps.
	
	Arguments:
	apps -- A dictionary with apps their meta data
	
	Returns:
	A dictionary with statistics:
	 - categories: statistics per category
	 - top_apps: top most downloaded apps in sections such as "vulnerable" and "safe"
	 - downloads: statistics per range of downloads
	 - ratings: statistics per rating
	 - years: statistics per year of release
	 - total: a summary
	"""
	categories = {}
	total = {}
	top_apps = {'vulnerable':[], 'safe':[] }
	downloads = {'0-100':{}, '100-10,000':{}, '10,000-1,000,000':{}, '1,000,000-100,000,000':{}, '100,000,000+':{}}
	years = {'Unknown':{},'2008':{},'2009':{},'2010':{},'2011':{},'2012':{},'2013':{}}
	ratings = {'Unknown':{},'0-1':{},'1-2':{},'2-3':{},'3-4':{},'4-5':{}}
	
	# init some dictionaries
	for download in downloads:
		initStats(downloads[download])
	for year in years:
		initStats(years[year])
	for rating in ratings:
		initStats(ratings[rating])
	
	for app,meta in apps.iteritems():
		sec = 'vulnerable' if isVulnerable(meta) else 'safe'
		_d = "{:,}+".format(int(meta['downloads']))
		_t = meta['title']
		_a = meta['creator']
		try:
			_a = meta['creator'].encode('utf-8')
		except:
			None
		try:
			_t = meta['title'].encode('utf-8')
		except:
			None
		
		# total
		fillStats(app, meta, total)
		
		# year
		year = time.strftime("%Y", meta['date']) if meta['date'] else 'Unknown'
		fillStats(app, meta, years[year])
		
		# rating
		fillStats(app, meta, ratings[ratingRange(meta)])
		
		# downloads
		fillStats(app, meta, downloads[downloadRange(meta)])
		
		# top apps
		top_apps[sec].append((_t, _a, _d))
		
		# categories
		for cat in meta['categories']:
			category = cat[0]
			if not category in categories:
				categories[category] = {}
				categories[category]['top_apps'] = { 'safe':[], 'vulnerable':[] }
			fillStats(app, meta, categories[category])
			categories[category]['top_apps'][sec].append((_t, _a, _d))
			
	# do some sorting
	for sec in ['vulnerable', 'safe']:
		top_apps[sec] = sorted(top_apps[sec], key=lambda x: str2float(x[2]))
		top_apps[sec].reverse()
		for category in categories:
			categories[category]['top_apps'][sec] = sorted(categories[category]['top_apps'][sec], key=lambda x: str2float(x[2]))
			categories[category]['top_apps'][sec].reverse()
	
	return {
		'categories':categories,
		'top_apps':top_apps,
		'downloads':downloads,
		'years':years,
		'ratings':ratings,
		'total':total
	}

def percentage(fraction, total):
	""" Calculate the percentage without risk of division by zero
	
	Arguments:
	fraction -- the size of the subset of samples
	total    -- the total size of samples
	
	Returns:
	fraction as a percentage of total
	"""
	p = 0 if total == 0 else 100.0 * fraction / total
	return "%.2f%%" % p

def alphabetical(lst):
	""" Sorts a list of tuples in reverse alphabetical order by the first key 
	in the tuple.

	Arguments:
	lst -- the list to sort

	Returns:
	the sorted list
	"""
	return list(reversed(sorted(lst, key=lambda x: x[0])))

def printTableRow(row, widths):
	""" Print out a row from a table of data.
	
	Arguments:
	row   -- a tuple of data points
	width -- the widths of the columns
	"""
	format = ""
	for width in widths:
		format += "%%%ds" % width
	print format % tuple(map(lambda x: str(x), row))

def printTexTableRow(row, file):
	""" Print out a row from a table of data in LaTeX format.
	
	Arguments:
	row   -- a tuple of data points
	width -- the widths of the columns
	"""
	format = []
	for col in row:
		format.append("%s")
	format = " & ".join(format)
	format += " \\\\ \\hline\n"
	file.write(format % tuple(map(lambda x: re.sub("%", "\\%", str(x)), row)))

def printTexTable(table, filename, lastRowIsTotal = True):
	""" Print out a table of data in LaTeX format to a file.
	
	Arguments:
	table -- list of tuples with data points, the first row is header and the last row is total
	file  -- file to print to
	"""
	min = 3 if lastRowIsTotal else 2
	if len(table) < min:
		raise Exception("error: table need to be at least "+str(min)+" rows")
		
	file = open(filename, 'w')
	cols = len(table[0])
	
	file.write("\\begin{{tabular}}{{|l|{}|}} \n".format("|".join(['r' for i in range(cols-1)])))
	file.write("\\hline \n")
		
	printTexTableRow(map(lambda x: "\\textbf{%s}" % x, table[0]), file)
	file.write("\\hline \n")
	
	body = table[1:]
	if lastRowIsTotal:
		body = body[:-1]
	for row in body:
		printTexTableRow(row, file)
		
	if lastRowIsTotal:
		file.write("\\hline \n")
		printTexTableRow(map(lambda x: "\\textbf{%s}" % x, table[-1]), file)
	
	file.write("\\end{tabular}")
	file.close()
	
def printTable(table, lastRowIsTotal = True):
	""" Print out a table of data.
	
	Arguments:
	table -- a list of tuples with data points, the first row is header and the last row is total
	"""
	min = 3 if lastRowIsTotal else 2
	if len(table) < min:
		raise Exception("error: table need to be at least "+str(min)+" rows")
		
	# calculate column widths
	margin = 3
	widths = map(lambda col: max(map(lambda row: len(str(row[col])), table))+margin, range(len(table[0])))
	
	printTableRow(map(lambda x: x.upper(), table[0]), widths)
	print "-" * sum(widths)
	body = table[1:]
	if lastRowIsTotal:
		body = body[:-1]
	for row in body:
		printTableRow(row, widths)
	if lastRowIsTotal:
		print "-" * sum(widths)
		printTableRow(table[-1], widths)

def printTexGraph(data, filename):
	""" Print a LaTeX file with a bar graph.
	
	Arguments:
	data     -- list of 3-tuples (name, absolute number, percentage)
	filename -- filename of the latex file to print to
	"""
	file = open(filename, 'w')
	
	xmax = roundUp(max(map(lambda x: x[1], data)))
	labels = ",".join(map(lambda x: "{{{}}}".format(x[0]), data))
	
	printLine = len(data[0]) == 3
	if not printLine: # bars are percentage
		xmax = 100
		
	height = round(2.4 + 0.6 * len(data),2)
	
	file.write("\\begin{tikzpicture}\n")
	file.write("\\begin{axis}[\n")
	file.write("	xbar, xmin=0, xmax={},\n".format(xmax))
	file.write("	width=5cm, height={}cm,\n".format(height))
	file.write("	axis x line*=bottom,\n")
	file.write("	xlabel={Apps},\n")
	file.write("	symbolic y coords={{{}}},\n".format(labels))
	file.write("	ytick=data]\n")
	file.write("	\\addplot coordinates {\n")
	for d in data:
		file.write("		({},{{{}}})\n".format(d[1],d[0]))
	file.write("	};\n")
	file.write("\\end{axis}\n")
	
	if printLine:
		file.write("\\begin{axis}[\n")
		file.write("	xmin=0, xmax=100,\n")
		file.write("	width=5cm, height={}cm,\n".format(height))
		file.write("	axis x line*=top,\n")
		file.write("	axis y line*=none,\n")
		file.write("	xlabel={Percentage}, xlabel near ticks,\n")
		file.write("	symbolic y coords={{{}}},\n".format(labels))
		file.write("	ytick=data,\n")
		file.write("	yticklabels={,,}]\n")
		file.write("	\\addplot+[sharp plot] coordinates {\n")
		for d in data:
			file.write("		({},{{{}}})\n".format(d[2],d[0]))
		file.write("	};\n")
		file.write("\\end{axis}\n")
		
	file.write("\\end{tikzpicture}\n")
	file.close()

def outputResults(args, apps):
	""" Print statistics out to LaTeX files.
	
	Arguments:
	args -- command line argument object
	apps -- dictionary with apps and their meta data
	"""

	if not args.skip_generating:
		createTexFolder(args)
	
	print "calculating statistics"
	stats = calculateStatistics(apps)
	_c = stats['categories']
	_t = stats['total']
	
	top_size = 50
	
	table = map(lambda x: (fixName(x), _c[x]['total'], _c[x]['internet'], percentage(_c[x]['internet'], _c[x]['total'])), _c)
	table = sorted(table, key=lambda x: str2float(x[3]))
	table.reverse()
	table.insert(0, ('Category','Total','Internet permission','Internet permission'))
	table.append(('Total', _t['total'], _t['internet'], percentage(_t['internet'], _t['total'])))
	
	if not args.skip_generating:
		printTexTable(table, args.tex_dir + "table_internet.tex")
		data = map(lambda x: (x[0], x[2], int(str2float(x[3]))), alphabetical(table[1:-1]))
		printTexGraph(data, args.tex_dir + "graph_internet.tex")
		
	if not args.skip_printing:
		print ""
		printTable(table)
		print ""
	
	l = [
		('trustmanagers','TrustManager','naive_trustmanagers','Naive TrustManager', 'trustmanagers'),
		('custom_hostname_verifiers','HostnameVerifier','naive_hostname_verifiers','Naive HostnameVerifier', 'hostname_verifiers')
	]
	for t in l:
		table = map(lambda x: (fixName(x), _c[x][t[0]], _c[x][t[2]], percentage(_c[x][t[0]], _c[x]['internet'] - _c[x]['unchecked']), percentage(_c[x][t[2]], _c[x]['internet'] - _c[x]['unchecked'])), _c)
		table = sorted(table, key=lambda x: str2float(x[4]))
		table.reverse()
		table.insert(0, ('Category',t[1],t[3],t[1],t[3]))
		table.append(("Total", _t[t[0]], _t[t[2]], percentage(_t[t[0]], _t['internet'] - _t['unchecked']), percentage(_t[t[2]], _t['internet'] - _t['unchecked'])))
		
		if not args.skip_generating:
			printTexTable(table, args.tex_dir + 'table_' + t[4] + '.tex')
			data = map(lambda x: (x[0], x[1], int(str2float(x[3]))), alphabetical(table[1:-1]))
			printTexGraph(data, args.tex_dir + 'graph_' + t[4] + '.tex')
			data = map(lambda x: (x[0], x[2], int(str2float(x[4]))), alphabetical(table[1:-1]))
			printTexGraph(data, args.tex_dir + 'graph_' + t[2] + '.tex')
		
		if not args.skip_printing:
			printTable(table)
			print ""
	
	l = [
		('insecure_factories','Insecure SSLSocketFactory', 'ssl_socket_factories'),
		('allow_all_hostname_verifiers','AllowAllHostnameVerifier', 'allow_all_hostname_verifiers'),
		('ssl_error_handlers','onReceivedSslError', 'on_received_ssl_error_handlers'),
		('vulnerable','Vulnerable', 'vulnerable')
	]	
	for t in l:
		table = map(lambda x: (fixName(x), _c[x][t[0]], percentage(_c[x][t[0]], _c[x]['internet'] - _c[x]['unchecked'])), _c)
		table = sorted(table, key=lambda x: str2float(x[2]))
		table.reverse()
		table.insert(0, ('Category',t[1],t[1]))
		table.append(("Total", _t[t[0]], percentage(_t[t[0]], _t['internet'] - _t['unchecked'])))
		
		if not args.skip_generating:
			printTexTable(table, args.tex_dir + 'table_' + t[2] + ".tex")
			data = map(lambda x: (x[0], x[1], int(str2float(x[2]))), alphabetical(table[1:-1]))
			printTexGraph(data, args.tex_dir + 'graph_' + t[2] + '.tex')
		
		if not args.skip_printing:
			printTable(table)
			print ""
			
	# top lists
	l = ['vulnerable','safe']
	for _l in l:
		stats['top_apps'][_l].insert(0, ('Name','Developer','Downloads'))
		if not args.skip_generating:
			printTexTable(stats['top_apps'][_l][:top_size], args.tex_dir + 'table_top_apps_'+_l+'.tex', False)
		if not args.skip_printing:
			printTable(stats['top_apps'][_l][:top_size], False)
			print ""

		for c in _c:
			_c[c]['top_apps'][_l].insert(0, ('Name','Developer','Downloads'))
			if not args.skip_generating:
				printTexTable(_c[c]['top_apps'][_l][:10], args.tex_dir + 'table_top_apps_'+c+'_'+_l+'.tex', False)
			if not args.skip_printing:
				printTable(_c[c]['top_apps'][_l][:10], False)
				print ""
				
	# sections
	l = [
		('years',('Year','Vulnerable','Vulnerable'),[]),
		('downloads',('Downloads','Vulnerable','Vulnerable'),[]),
		('ratings',('Rating','Vulnerable','Vulnerable'),[])
	]
	
	# sort sections
	c = stats['years']
	_l = map(lambda x: (x, c[x]['vulnerable'], percentage(c[x]['vulnerable'], c[x]['internet'] - c[x]['unchecked'])), c)
	_l = sorted(_l, key=lambda x: str2float(x[2]))
	l[0][2].extend(_l)
	
	for x in ['0-100','100-10,000','10,000-1,000,000','1,000,000-100,000,000','100,000,000+']:
		c = stats['downloads'][x]
		l[1][2].append((x, c['vulnerable'], percentage(c['vulnerable'], c['internet']-c['unchecked'])))
		
	for x in ['0-1','1-2','2-3','3-4','4-5','Unknown']:
		c = stats['ratings'][x]
		l[2][2].append((x, c['vulnerable'], percentage(c['vulnerable'], c['internet']-c['unchecked'])))
		
	# output section tables
	for _l in l:
		c = stats[_l[0]]
		table = _l[2]
		table.insert(0, _l[1])
		if not args.skip_generating:
			printTexTable(table, args.tex_dir + 'table_'+_l[0]+'.tex', False)
			data = map(lambda x: (x[0], x[1], int(str2float(x[2]))), table[1:])
			printTexGraph(data, args.tex_dir + 'graph_' +_l[0]+'.tex')
		if not args.skip_printing:
			printTable(table, False)
			print ""
	
def download(gpAPI, path, app, version, offer):
	""" Download an app from the Google Play Store.

	Arguments:
	gpAPI      -- Google Play API object
	path       -- the category to fetch apps from
	app        -- the subcategory to fetch apps from
    version    -- the dictionary where apps with INTERNET permission are saved (detailed meta data)
	offer      -- a dictionary with all apps found (no meta data)
	
	Returns:
	True if the app was downloaded successfully, otherwise false.
	"""
	try:
		data = gpAPI.download(app, version, offer)
		f = open(path, "wb")
		f.write(data)
		f.close()
		return True
	except:
		return False

def getCategories(gpAPI):
	""" Get a list of all categories on the play store.
	
	Arguments:
	gpAPI -- Google Play API object
	
	Returns:
	A list of category IDs.
	"""
	response = gpAPI.browse()
	categories = []
	for category in response.category:
		cat_id = urlparse.parse_qs(category.dataUrl)['cat'][0].encode('utf-8')
		categories.append(cat_id)
	return categories

def getSubcategories(gpAPI, category):
	""" Get a list of all subcategories in a given category.
	
	Arguments:
	gpAPI    -- Google Play API object
	category -- the ID of the category to browse
	
	Returns:
	A list of subcategory IDs.
	"""
	subcategories = gpAPI.list(category, None, None, None)
	subcatIDs = []
	for subcat in subcategories.doc:
		subcatIDs.append(subcat.docid.encode('utf-8'))
	return subcatIDs

def getApps(gpAPI, cat, subcat, apps, limit = 500, offset = 0):
	""" Get a list of all apps in a subcategory.

	Arguments:
	gpAPI      -- Google Play API object
	cat        -- the category to fetch apps from
	subcat     -- the subcategory to fetch apps from
	apps       -- the dictionary with apps and their meta data
	limit      -- the number of apps to fetch (no more than 500)
	offset     -- the offset to start fetching from
	"""

	if limit + offset > 500:
		raise LookupError("No more than 500 apps can be fetched.")
		
	if limit < 1:
		raise LookupError("Limit cannot be less than one.")
		
	if offset < 0:
		raise LookupError("Offset cannot be less than zero.")
		
	# we can only fetch 100 apps at a time, so we need to construct
	# a list of offsets and limits
	limitsOffsets = constructLimitsOffsets(limit, offset)
	
	# will overwrite two previous characters
	animate()
	
	for limitOffset in limitsOffsets:
		limit = limitOffset[0]
		offset = limitOffset[1]
		list = gpAPI.list(cat, subcat, limit, offset)
		
		try:
			for app in list.doc[0].child:
				animate()
					
				if app.docid in apps:
					if not (cat,subcat) in apps[app.docid]['categories']:
						apps[app.docid]['categories'].append((cat, subcat))
				else:
					details = gpAPI.details(app.docid)
					meta = {
						'title':app.title.encode('utf-8'),
						'creator':app.creator.encode('utf-8'),
						'super_dev':len(app.annotations.badgeForCreator),
						'price':app.offer[0].formattedAmount,
						'downloads':re.sub("[^0-9]", "", app.details.appDetails.numDownloads),
						'version':details.docV2.details.appDetails.versionCode,
						'offer':details.docV2.offer[0].offerType,
						'rating':app.aggregateRating.starRating,
						'date':time.strptime(details.docV2.details.appDetails.uploadDate, "%b %d, %Y"),
						'unchecked':True,
						'categories':[(cat, subcat)]
					}
					internet = any("android.permission.INTERNET" in i for i in details.docV2.details.appDetails.permission)
					meta['internet'] = internet
					apps[app.docid] = meta
				apps[app.docid]['foo'] = False
		except IndexError:
			#sys.stdout.write('e')
			#sys.stdout.flush()
			break

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

def searchTitle(apps, title):
	""" Search for an app given its title. """
	for app in apps:
		if apps[app]['title'] == title:
			return app
	return None
	
def parseArgs():
	""" Parse command line arguments.
	
	Returns:
	Command line argument object
	"""
	# example for help text
	prog = os.path.basename(__file__)
	epilog = "android ID:\n\n"
	epilog+= "  in order to download apps from the Google Play Store you need\n"
	epilog+= "  to provide your android id number.\n\n"
	epilog+= "  type *#*#8255#*#* on your phone to start GTalk Monitor.\n"
	epilog+= "  your android id is shown as 'aid'.\n\n"
	epilog+= "examples:\n\n"
	epilog+= "  use mail and password:\n"
	epilog+= "  $ " + prog + " -u EMAIL -p PASS\n\n"
	epilog+= "  use token:\n"
	epilog+= "  $ " + prog + " -t TOKEN\n\n"
	epilog+= "  generate statistic files:\n"
	epilog+= "  $ " + prog + " -D -P\n\n"
	epilog+= "  print statistics:\n"
	epilog+= "  $ " + prog + " -D -G\n\n"
	
	parser = argparse.ArgumentParser(
		description='download android apps and analyze the security of their communications.',
		usage='%(prog)s [options]',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=epilog)
	
	parser.add_argument('--cache', help="file for storing cache.", dest="f_cache", type=str, metavar=('FILE'), default=".hermes-cache.p")
	parser.add_argument('--cache-pos', help="file for storing position used for resuming analyzer.", dest="f_pos", type=str, metavar=('FILE'), default=".hermes-cache-pos.p")
	
	parser.add_argument('--category', help="category to fetch apps from (default: all)", dest="category", type=str, metavar=('NAME'))
	parser.add_argument('--subcategory', help="subcategory to fetch apps from (default: all)", dest="subcategory", type=str, metavar=('NAME'))
	parser.add_argument('--limit', help="the total number of apps to fetch from each category/subcategory.", dest="limit", type=int, metavar=('NUM'), default=500)
	parser.add_argument('--offset', help="the offset from where to fetch apps in each category/subcategory.", dest="offset", type=int, metavar=('NUM'), default=0)
	
	parser.add_argument('--restore-freq', help="how often to create restore point when analyzing apps, use 0 to skip.", dest="restore_freq", type=int, metavar=('NUM'), default=10)
	parser.add_argument('--app-dir', help="directory where apps will be stored during download and analytics.", dest="app_dir", type=str, metavar=('FOLDER'), default='apps/')
	parser.add_argument('--tex-dir', help="directory where LaTeX reports will be saved.", dest="tex_dir", type=str, metavar=('FOLDER'), default='tex/')
	
	parser.add_argument('-i', help="your android ID number, see -h for more info.", dest="id", type=str, metavar=('ID'))
	parser.add_argument('-u', help="username for logging into Google Play Store.", dest="user", type=str, metavar=('GMAIL'))
	parser.add_argument('-p', help="password for logging into Google Play Store.", dest="passw", type=str, metavar=('PASS'))
	parser.add_argument('-t', help="access token for accessing Google Play Store.", dest="token", type=str, metavar=('TOKEN'))
	
	parser.add_argument('-D', '--no-download', help="skip downloading and analysing apps.", dest="skip_download", action='store_true')
	parser.add_argument('-G', '--no-generating', help="skip generating statistic files.", dest="skip_generating", action='store_true')
	parser.add_argument('-P', '--no-printing', help="skip printing statistic output.", dest="skip_printing", action='store_true')
	
	args = parser.parse_args()
	
	# validate login credentials
	if not args.skip_download:
		if (not args.token) and not (args.user and args.passw):
			print("error: you need to specify user/pass or token.")
			exit(1)
		if not args.id:
			print("error: you need to specify your android id. see -h for more info.")
			exit(1)
			
	# validate modes
	if args.skip_download and args.skip_printing and args.skip_generating:
		print("what's the point if you skip everything?")
		exit(1)
	
	return args
	
def browse(args, gpapi, apps):
	""" Browse Google Play Store and construct list of apps to analyze.
	
	Arguments:
	args  -- command line argument object
	gpapi -- Google Play API object
	apps  -- dictionary of apps and their meta data
	"""
	categories = {}
	if args.category and args.category != "all":
		categories[args.category] = []
	else:
		for category in getCategories(gpapi):
			categories[category] = []
			
	for category in categories:
		if args.subcategory and args.subcategory != "all":
			categories[category] = [args.subcategory]
		else:
			categories[category] = getSubcategories(gpapi, category)
		
	num = len([subcategory for subcategory in categories[category] for category in categories])
	i = 0
	for category in categories:
		for subcategory in categories[category]:
			i += 1
			cat_str = "%s/%s:" % (category, subcategory)
			sys.stdout.write("\rfetching app list in category {:<50} {:6.2f}% {} ".format(cat_str, 100.0 * i / num, animation[animation_pos % len(animation)]))
			sys.stdout.flush()
			getApps(gpapi, category, subcategory, apps, args.limit, args.offset)
			
	sys.stdout.write("\rdone fetching app lists\033[K\n")
	sys.stdout.flush()
	
	# save cache
	print "saving to cache"
	pickle.dump(apps, open(args.f_cache, 'wb'))
	
def createTexFolder(args):
	""" Create the folder for storing generated LaTeX reports.
	
	Arguments:
	args -- the command line arguments object
	"""
	tryCreateFolder(args.tex_dir, "storing generated reports")
		
def createAppFolder(args):
	""" Create the folder for storing downloaded apps.
	
	Arguments:
	args -- the command line arguments object
	"""
	tryCreateFolder(args.app_dir, "storing downloaded apps")
		
def tryCreateFolder(path, description):
	""" Try to create a folder and halt execution if it fails.
	
	Arguments:
	path        -- the path to create
	description -- the description of the folder (used in error msg)
	"""
	try:
		if not os.path.isdir(path):
			os.makedirs(path)
	except:
		print("error: could not create folder for " + description + ".")
		exit(1)
		
def deleteAppFolder(args):
	""" Delete the folder for storing downloaded apps.
	
	Arguments:
	args -- the command line arguments object
	"""
	try:
		if os.path.isdir(args.app_dir):
			os.removedirs(args.app_dir)
	except:
		None

def getRestorePoint(args):
	""" Get the point from where to resume app analyzing.
	
	Arguments:
	args -- the command line arguments object
	
	Returns:
	The position where to resume
	"""
	try:
		pos = pickle.load(open(args.f_pos, 'rb'))
		print "resuming from restore point at: " + str(pos)
		return pos
	except:
		return 0
		
def createRestorePoint(args, apps, pos):
	""" Create a point for resuming analyzing.
	
	Arguments:
	args -- the command line arguments object
	apps -- dictionary of apps and their meta data
	pos  -- the current position of the analyzer
	"""
	pickle.dump(apps, open(args.f_cache, 'wb'))
	pickle.dump(pos, open(args.f_pos, 'wb'))
		
def clearRestorePoint(args, apps):
	""" Remove the restoration point.
	
	Arguments:
	args -- the command line arguments object
	apps -- dictionary of apps and their meta data
	"""
	try:
		os.remove(args.f_pos)
	except:
		None
	pickle.dump(apps, open(args.f_cache, "wb"))
	
def shouldProcess(app):
	""" Check if an app should be downloaded and analyzed. """
	if not 'internet' in app:
		return False
	if not 'unchecked' in app:
		return False
	return app['internet'] and app['unchecked'] and app['price'] == u'Free'
	
def processApps(args, gpapi, apps):
	""" Download and analyze apps on the Google Play Store.
	
	Arguments:
	args       -- the command line arguments object
	gpapi      -- the Google Play API object
	total      -- the total number of apps
	categories -- dictionary of categories,subcategories and number of apps in them
	apps       -- dictionary of apps and their meta data
	"""
	createAppFolder(args)
	i = 0
	j = 0
	
	for app in apps:
		if shouldProcess(apps[app]):
			j += 1		
	print "found {:,} apps to process".format(j)
	
	pos = getRestorePoint(args)
	
	for app,meta in apps.iteritems():
			
		# we only care about apps which require INTERNET permission, we haven't checked yet, and are free
		if not shouldProcess(meta):
			continue
			
		# skip until at the position where we should resume
		i += 1
		if i < pos:
			continue
			
		# create restore point
		if i % args.restore_freq == 0 and i > 0 and args.restore_freq > 0:
			createRestorePoint(args, apps, i)
		
		# print progress
		sys.stdout.write("\rprocessing apps... %6.2f%% %10s: %s\033[K " % (100.0 * i / j, "app", app))
		sys.stdout.flush()
		
		try:
			fname = args.app_dir + app + ".apk"
			if download(gpapi, fname, app, meta['version'], meta['offer']):
				analyze(apps, fname, app)
				os.remove(fname)	
		except:
			None
	sys.stdout.write("\rdone processing apps\033[K\n")
	sys.stdout.flush()
			
	# clean up
	print "saving to cache"
	clearRestorePoint(args, apps)
	deleteAppFolder(args)

def main():
	args = parseArgs()
	print "hermes 0.1"
	print "by ephracis"
	print ""
	
	# load cache
	apps = {}
	try:
		print "looking for cache"
		apps = pickle.load(open(args.f_cache, 'rb'))
		print "loaded {:,} apps from cache".format(len(apps))
	except:
		print "no cache found"
	
	# download + analyze
	if not args.skip_download:	
		print "logging in to play store"
		api = login(args.id, args.user, args.passw, args.token)
		
		#print "constructing list of apps"
		#browse(args, api, apps)
		
		print "starting app analyzer"
		processApps(args, api, apps)

	if len(apps) == 0:
		print("error: no apps to analyze.")
		exit(1)
		
	# statistics
	if not (args.skip_generating and args.skip_printing):
		print "generating output"
		outputResults(args, apps)
		
	if args.skip_printing:
		print "done"
	
if __name__ == "__main__":
	main()
