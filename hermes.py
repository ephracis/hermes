#!/usr/bin/env python
# encoding: utf-8

import argparse
import os
import pickle
import sys

sys.path.insert(0, 'utilities')

from analyze import *
from output import *
from stats import *
from store import *

from filesystem import *
from lists import *
from numbers import *
from strings import *

#from google.protobuf import text_format

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
