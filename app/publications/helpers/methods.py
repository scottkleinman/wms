import os, tabulator, itertools, requests, json, re, zipfile, shutil
from datetime import datetime
from jsonschema import validate, FormatChecker
from tabulator import Stream
import pandas as pd
from tableschema_pandas import Storage

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections" 
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
publications_db = db.Publications

#----------------------------------------------------------------------------#
# General Helper Functions
#----------------------------------------------------------------------------#

def allowed_file(filename):
	"""Tests whether a filename contains an allowed extension.

	Returns a Boolean.
	"""
	return '.' in filename and \
			filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


def check_date_format(dates):
	"""Ensures that a date is correctly formatted 
	and that start dates precede end dates.
	
	Takes a list of dates and returns a list of dates
	and a list of errors.
	"""
	errors = []
	log = []
	for item in dates:
		if ',' in item:
			range = item.replace(' ', '').split(',')
			try:
				assert range[1] > range[0]
				log = log + range
			except:
				msg = 'Your end date <code>' + range[1] + '</code> must be after your start date <code>' + range[0] + '</code>.'
				errors.append(msg)
		else:
			log.append(item)
	for item in log:
		if len(item) > 10:
			format = '%Y-%m-%dT%H:%M:%S'
		else:
			format = '%Y-%m-%d'
		try:
			item != datetime.strptime(item, format).strftime(format)
		except:
			msg = 'The date value <code>' + item + '</code> is in an incorrect format. Use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:MM:SS</code>.'
			errors.append(msg)
	new_dates = process_dates(dates)
	return new_dates, errors


def get_page(pages, page):
	"""Takes a list of paginated results form `paginate()` and returns a single page from the list.
	"""
	try:
		return pages[page-1]
	except:
		print('The requested page does not exist.')


def make_dir(folder):
	"""Checks for the existence of directory at the specified file 
	path and creates one if it does not exist.
	"""
	folder = folder.replace('\\', '/')
	if not os.path.exists(folder):
		os.makedirs(folder)


def NestedDictValues(d):
	""" Yields all values in a multilevel dict. Returns a generator
	from which can be cast as a list.
	"""
	for v in d.values():
		if isinstance(v, list):
			yield from NestedDictValues(v[0])
			break
		if isinstance(v, dict):
			yield from NestedDictValues(v)
		else:
			yield v


def paginate(iterable, page_size):
	"""Returns a generator with a list sliced into pages by the designated size. If 
	the generator is converted to a list called `pages`, and individual page can 
	be called with `pages[0]`, `pages[1]`, etc.
	"""
	while True:
		i1, i2 = itertools.tee(iterable)
		iterable, page = (itertools.islice(i1, page_size, None), 
			list(itertools.islice(i2, page_size)))
		if len(page) == 0:
			break
		yield page


def process_dates(dates):
	"""Transforms a string from an HTML textarea into an
	array that validates against the WE1S schema.
	"""
	new_dates = []
	d = {}
	# Determine if the dates are a mix of normal and precise dates
	contains_precise = []
	for item in dates:
		if ',' in item:
			start, end = item.replace(' ', '').split(',')
			if len(start) > 10 or len(end) > 10:
				contains_precise.append('precise')
			else:
				contains_precise.append('normal')
		elif len(item) > 10:
			contains_precise.append('precise')
		else:
			contains_precise.append('normal')
		# Handle a mix of normal and precise dates
		if 'normal' in contains_precise and 'precise' in contains_precise:
			d['normal'] = []
			d['precise'] = []
			for item in date:
				if ',' in item:
					start, end = item.replace(' ', '').split(',')
					if len(start) > 10 or len(end) > 10:
						d['precise'].append({'start': start, 'end': end})
					else:
						d['normal'].append({'start': start, 'end': end})
				else:
					if len(item) > 10:
						d['precise'].append(item)
					else:
						d['normal'].append(item)
					new_dates.append(d)
		# Handle only precise dates
		elif 'precise' in contains_precise:
			d['precise'] = []
			for item in dates:
				if ',' in item:
					start, end = item.replace(' ', '').split(',')
					d['precise'].append({'start': start, 'end': end})
				else:
					d['precise'].append(item)
			new_dates.append(d)
		# Handle only normal dates
		else:
			for item in dates:
				if ',' in item:
					start, end = item.replace(' ', '').split(',')
					new_dates.append({'start': start, 'end': end})
				else:
					new_dates.append(item)
	return new_dates


def reshape_query_props(temp_query, temp_show_properties):   
	"""Converts the user input from the search form to 
	a dict of properties.

	Takes strings for the query and show properties fields.
	Returns dicts of keywords and values for both.
	"""
	query_props = {}
	for item in temp_query.split('\n'):
		prop, val = item.split(':')
		prop = prop.strip().strip('"').strip("'")
		val = val.strip().strip('"').strip("'")
		query_props[prop] = val
	# Convert the properties to show to a list
	show_props = temp_show_properties.split('\n')
	if show_props == ['']:
		show_props = None
	return query_props, show_props


def validate_manifest(manifest):
	"""Validates a manifest against the WE1S schema on GitHub.

	Takes a manifest dict and returns a Boolean.
	"""
	schema_file = 'https://raw.githubusercontent.com/whatevery1says/manifest/master/schema/Publications/Publications.json'
	schema = json.loads(requests.get(schema_file).text)
	try:
		validate(manifest, schema, format_checker=FormatChecker())
		return True
	except:
		return False


def zipfolder(source_dir, output_filename):
	"""Creates a zip archive of a source directory.

	Takes file paths for both the source directory
	and the output file.

	Note that the output filename should not have the 
	.zip extension; it is added here.
	"""
	# Output filename should be passed to this function without the .zip extension           
	zipobj = zipfile.ZipFile(output_filename + '.zip', 'w', zipfile.ZIP_DEFLATED)
	rootlen = len(source_dir) + 1
	for base, dirs, files in os.walk(source_dir):
		for file in files:
			fn = os.path.join(base, file)
			zipobj.write(fn, fn[rootlen:])


#----------------------------------------------------------------------------#
# Database Functions
#----------------------------------------------------------------------------#

def create_record(manifest):
	""" Creates a new manifest record in the database.

	Takes a manifest dict and returns a list of errors if any.
	"""
	errors = []
	if validate_manifest(manifest) == True:
		try:
			assert manifest['_id'] not in publications_db.distinct('_id')
			publications_db.insert_one(manifest)
		except:
			msg = 'The <code>_id</code> <strong>' + manifest['_id'] + '</strong> already exists in the database.'
			errors.append(msg)
	else:
		errors.append('Unknown Error: Could not produce a valid manifest.')
	return errors


def delete_publication(id):
	"""
	Deletes a publication manifest based on _id.

	Returns 'success' or an error message string.
	"""
	result = publications_db.delete_one({'_id': id})
	if result.deleted_count != 0:
		return 'success'
	else:
		return 'Unknown error: The document could not be deleted.'


def import_manifests(source_files):
	"""
	Loops through the source files and streams them into a dataframe, then converts
	the dataframe to a list of manifest dicts.
	"""
	# Set up the storage functions for pandas dataframes
	storage = Storage()
	storage.create('data', {
		'primaryKey': '_id',
		'fields': [
			{'name': '_id', 'type': 'string'},
			{'name': 'publication', 'type': 'string'},
			{'name': 'description', 'type': 'string'},
			{'name': 'publisher', 'type': 'string'},
			{'name': 'date', 'type': 'string'},
			{'name': 'edition', 'type': 'string'},
			{'name': 'contentType', 'type': 'string'},
			{'name': 'language', 'type': 'string'},
			{'name': 'country', 'type': 'string'},
			{'name': 'authors', 'type': 'string'},
			{'name': 'title', 'type': 'string'},
			{'name': 'altTitle', 'type': 'string'},
			{'name': 'label', 'type': 'string'},
			{'name': 'notes', 'type': 'string'}
		]
	})
	path = os.path.join('app', current_app.config['UPLOAD_FOLDER'])
	error_list = []
	for item in source_files:
		if item.endswith('.xlsx') or item.endswith('.xls'):
			options = {'format': 'xlsx', 'sheet': 1, 'headers': 1}
		else:
			options = {'headers': 1}
		filepath = os.path.join(path, item)
		with tabulator.Stream(filepath, **options) as stream:
			try:
				stream.headers == ['_id', 'publication', 'description', 'publisher', 'date', 'edition', 'contentType', 'language', 'country', 'authors', 'title', 'altTitle', 'label', 'notes']				
			except:
				col_order = '_id, publication, description, publisher, date, edition, contentType, language, country, authors, title, altTitle, label, notes'
				error_list.append('Error: The table headings in ' + item + ' do not match the Publications schema. Please use the headings ' + col_order + ' in that order.')
		with tabulator.Stream(filepath, **options) as stream:
			try:
				storage.write('data', stream)
			except:
				error_list.append('Error: Could not stream tabular data.')
	os.remove(filepath)
	manifests = []
	properties = {}
	data_dict = storage['data'].to_dict('index')
	for key, values in data_dict.items():
		properties = {k: v for k, v in values.items() if v is not None}
		properties = {k: v.replace('\\n', '\n') for k, v in properties.items()}
		properties['_id'] = key
		properties['namespace'] = 'we1sv1.1'
		properties['path'] = ',Publications,'
		if validate_manifest(properties) == True:
			manifests.append(properties)
		else:
			error_list.append('Could not produce a valid manifest for <code>' + key + '</code>.')
	# Now we're ready to insert into the database
	for manifest in manifests:
		db_errors = create_record(manifest)
		error_list = error_list + db_errors
	return manifests, error_list


def search_publications(values):
	"""Queries the database from the search form.

	Takes a list of values from the form and returns the search results.
	"""
	page_size = 10
	errors = []
	if len(list(publications_db.find())) > 0:
		query_properties, show_properties = reshape_query_props(values['query'], values['properties'])
		if values['regex'] == True:
			query = {}
			for k, v in query_properties.items():
			    REGEX = re.compile(v)
			    query[k] = {'$regex': REGEX}
		else:
			query = query_properties
		result = list(publications_db.find(
			query,
			limit=int(values['limit']),
			projection=show_properties)
		)
		pages = list(paginate(result, page_size=page_size))
		num_pages = len(pages)
		page = get_page(pages, int(values['page']))
		return result, num_pages, errors
	else:
		errors.append('The Publications database is empty.')
		return [], 1, errors


def update_record(manifest):
	""" Updates a manifest record in the database.

	Takes a manifest dict and returns a list of errors if any.
	"""
	errors = []
	if validate_manifest(manifest) == True:
		try:
			id = manifest.pop('_id')
			publications_db.update_one({'_id': id}, {'$set': manifest}, upsert=False)
		except:
			msg = 'Unknown Error: The record for <code>_id</code> <strong>' + manifest['_id'] + '</strong> could not be updated.'
			errors.append(msg)
	else:
		errors.append('Unknown Error: Could not produce a valid manifest.')
	return errors


#----------------------------------------------------------------------------#
# Currently Unused Functions
#----------------------------------------------------------------------------#

def list_publications(page_size=10, page=1):
	"""
	Prints a list of all publications.
	"""
	if len(list(publications.find())) > 0:
		result = list(publications.find())
		pages = list(paginate(result, page_size=page_size))
		page = get_page(pages, page)
	else:
		print('The Publications database is empty.')
