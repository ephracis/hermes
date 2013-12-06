""" This file contains code for working with strings. """

import re

def fixName(category):
	""" Turn the category name into human readable form. """
	exceptions = ['a', 'an', 'of', 'the', 'is', 'and', 'with', 'by']
	fixed = title_except(re.sub('_',' ',category), exceptions)
	if fixed == "App Wallpaper":
		fixed = "Live Wallpaper"
	elif fixed == "App Widgets":
		fixed = "Widgets"
	return fixed

def fixRow(name):
	""" Escape special characters for LaTeX output. """
	name = re.sub("%", "\\%", name)
	name = re.sub("&", "\\&", name)
	return name

def title_except(s, exceptions):
	""" Titlelize a string with exceptions. """
	word_list = re.split(' ', s.lower())       #re.split behaves as expected
	final = [word_list[0].capitalize()]
	for word in word_list[1:]:
		final.append(word in exceptions and word or word.capitalize())
	return " ".join(final)

def str2float(str):
	""" convert a string to a float """
	try:
		return float(re.sub("[^0-9\.]", "", str))
	except:
		return 0