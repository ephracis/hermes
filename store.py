""" This file contains code for accessing the Google Play Store. """

import pickle
import time
import urlparse

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

try:
	from googleplay import GooglePlayAPI
except:
	print("error: could not find GooglePlayAPI, make sure you have downloaded it and set your python path.")
	#exit(1)

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