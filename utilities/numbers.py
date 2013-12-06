""" This file contains code for working with numbers. """

import math

def roundUp(number):
	""" Round up an integer to the nearest power of then of the same degree.
		Exempel: 35 -> 40, 540 -> 600, 1250 -> 2000, etc """
	nearest = math.pow(10,len(str(number))-1)
	return int(math.ceil(number / nearest) * nearest)

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