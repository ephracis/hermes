""" This file contains code for generating statistics from raw data. """

import time

from lists import *
from numbers import *
from strings import *

def verifierType(app):
	""" Gets the type of certificate verifier the app is using. """
	if isNaive(app):
		return 'naive'
	if isCustom(app):
		return 'custom'
	return 'native'

def isNaive(app):
	""" Checks if an app contains a naive verifier.
		
		Arguments:
		app -- dictionary with meta data of the app to check
		
		Returns:
		True if the app contains naive verifiers, otherwise False
		"""
	properties = ['naive_trustmanagers','insecure_factories','naive_hostname_verifiers','allow_all_hostname_verifiers']
	return anyMoreThanOne(app,properties)

def isCustom(app):
	""" Checks if an app contains a custom verifier.
		
		Arguments:
		app -- dictionary with meta data of the app to check
		
		Returns:
		True if the app contains a custom verifier, otherwise False
		"""
	properties = ['custom_trustmanagers','custom_hostname_verifiers']
	return anyMoreThanOne(app,properties)

def initStats(stats):
	""" Initialize a dictionary of statistics. """
	fields = ['total', 'internet', 'trustmanagers', 'naive_trustmanagers',
			  'insecure_factories','custom_hostname_verifiers','naive_hostname_verifiers',
			  'allow_all_hostname_verifiers','ssl_error_handlers','unchecked','custom', 'naive']
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
		if isCustom(meta):
			stats['custom'] += 1
		if isNaive(meta):
			stats['naive'] += 1

def calculateStatistics(apps):
	""" Calculates the statistics of apps.
		
		Arguments:
		apps -- A dictionary with apps their meta data
		
		Returns:
		A dictionary with statistics:
		- categories: statistics per category
		- top_apps: top most downloaded apps in sections such as "native", "custom" and "naive" describing their verifiers
		- downloads: statistics per range of downloads
		- ratings: statistics per rating
		- years: statistics per year of release
		- total: a summary
		"""
	categories = {}
	total = {}
	top_apps = {'naive':[], 'custom':[], 'native':[] }
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
		sec = verifierType(meta)
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
		tup = (_t, _a, _d)
		if meta['internet'] and not tup in top_apps[sec]:
			top_apps[sec].append(tup)
		
		# categories
		for cat in meta['categories']:
			category = cat[0]
			if not category in categories:
				categories[category] = {}
				categories[category]['top_apps'] = { 'native':[], 'custom':[], 'naive':[] }
			fillStats(app, meta, categories[category])
			if meta['internet'] and not tup in categories[category]['top_apps'][sec]:
				categories[category]['top_apps'][sec].append(tup)
	
	# do some sorting
	for sec in ['naive', 'custom', 'native']:
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