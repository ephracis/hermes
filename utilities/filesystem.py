""" This file contains code for working with the local filesystem. """

import os
import pickle

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