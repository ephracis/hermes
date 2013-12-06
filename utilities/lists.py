""" This file contains code for working on lists and dictionaries. """

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

def makeUnique(list):
	""" Removes duplicates from a list. """
	u = []
	for l in list:
		if not l in u:
			u.append(l)
	return u

def alphabetical(lst):
	""" Sorts a list of tuples in reverse alphabetical order by the first key
		in the tuple.
		
		Arguments:
		lst -- the list to sort
		
		Returns:
		the sorted list
		"""
	return list(reversed(sorted(lst, key=lambda x: x[0])))