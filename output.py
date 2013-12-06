""" This file contains code for outputting results to both stdout and LaTeX files. """

import sys
import time

from stats import *
from filesystem import *

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
	file.write(format % tuple(map(lambda x: fixRow(str(x)), row)))

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