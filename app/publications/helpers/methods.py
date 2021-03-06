import os, tabulator, itertools, requests, json, re, zipfile, shutil
from flask import current_app
from bson import BSON
from bson import json_util
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
			assert manifest['name'] not in publications_db.distinct('name')
			publications_db.insert_one(manifest)
		except:
			msg = 'The <code>name</code> <strong>' + manifest['name'] + '</strong> already exists in the database.'
			errors.append(msg)
	else:
		errors.append('Unknown Error: Could not produce a valid manifest.')
	return errors


def delete_publication(name):
	"""
	Deletes a publication manifest based on name.

	Returns 'success' or an error message string.
	"""
	result = publications_db.delete_one({'name': name})
	if result.deleted_count != 0:
		return 'success'
	else:
		return 'Unknown error: The document could not be deleted.'


def import_manifests(source_files):
	"""
	Loops through the source files and streams them into a dataframe, then converts
	the dataframe to a list of manifest dicts.
	"""
	print('Impoooorrrrtttinng')
	# Set up the storage functions for pandas dataframes
	storage = Storage()
	storage.create('data', {
		'primaryKey': 'name',
		'fields': [
			{'name': 'name', 'type': 'string'},
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
	print('source_files')
	print(source_files)
	for item in source_files:
		if item.endswith('.xlsx') or item.endswith('.xls'):
			options = {'format': 'xlsx', 'sheet': 1, 'headers': 1}
		else:
			options = {'headers': 1}
		filepath = os.path.join(path, item)
		with tabulator.Stream(filepath, **options) as stream:
			try:
				stream.headers == ['name', 'publication', 'description', 'publisher', 'date', 'edition', 'contentType', 'language', 'country', 'authors', 'title', 'altTitle', 'label', 'notes']				
			except:
				col_order = 'name, publication, description, publisher, date, edition, contentType, language, country, authors, title, altTitle, label, notes'
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
	print(data_dict)
	for key, values in data_dict.items():
		properties = {k: v for k, v in values.items() if v is not None}
		properties = {k: v.replace('\\n', '\n') for k, v in properties.items()}
		properties['name'] = key
		properties['namespace'] = 'we1sv1.2'
		properties['path'] = ',Publications,'
		if validate_manifest(properties) == True:
			manifests.append(properties)
		else:
			error_list.append('Could not produce a valid manifest for <code>' + key + '</code>.')
	# Now we're ready to insert into the database
	print(manifests)
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
			name = manifest.pop('name')
			publications_db.update_one({'name': name}, {'$set': manifest}, upsert=False)
		except:
			msg = 'Unknown Error: The record for <code>name</code> <strong>' + manifest['name'] + '</strong> could not be updated.'
			errors.append(msg)
	else:
		errors.append('Unknown Error: Could not produce a valid manifest.')
	return errors


#----------------------------------------------------------------------------#
# Currently Unused Functions
#----------------------------------------------------------------------------#

def textarea2dict(fieldname, textarea, main_key, valid_props):
    """Converts a textarea string to a dict containing a list of 
	properties for each line. Multiple properties should be 
	formatted as key: value pairs. The key must be separated 
    from the value by a space. If ": " occurs in the value, 
	the entire value can be put in quotes. Where there is only 
	one value, the key can be omitted, and it will be supplied
    from main_key. A list of valid properties is supplied in 
	valid_props. If any property is invalid the function 
	returns a dict with only the error key and a list of errors.
    """
    import yaml
    lines = textarea.split('\n')
    all_lines = []
    errors = []

    for line in lines:
        opts = {}
        pattern = ', (' +'[a-z]+: ' + ')' # Assumes no camel case in the property name
        # There are no options, and the main_key is present
        main = main_key + '|[\'\"]' + main_key + '[\'\"]'
        if re.search('^' + main + ': .+$', line):
            opts[main_key] = re.sub('^' + main + ': ', '', line.strip())
        # There are no options, and the main_key is omitted
        elif re.search(pattern, line) == None: 
            opts[main_key] = line.strip()
        # Parse the options
        else:
            line = re.sub(pattern, '\n\\1', line) # Could be improved to handle more variations
            opts = yaml.load(line.strip())
            for k, v in opts.items():
                if k not in valid_props:
                    errors.append('The ' + fieldname + ' field is incorrectly formatted or ' + k + ' is not a valid property for the field.')
        all_lines.append(opts)
    if errors == []:
        d = {fieldname: all_lines}
    else:
        d = {'errors' : errors}
    return d

import re
import dateutil.parser
from datetime import datetime

def testformat(s):
    """Parses date and returns a dict with the date string, format,
    and an error message if the date cannot be parsed.
    """
    error = ''
    try:
        d = datetime.strptime(s, '%Y-%m-%d')
        dateformat = 'date'
    except:
        try:
            d = datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
            dateformat = 'datetime'
        except:
            dateformat = 'unknown'
    if dateformat == 'unknown':
        try:
            d = dateutil.parser.parse(s)
            s = d.strftime("%Y-%m-%dT%H:%M:%SZ")
            dateformat = 'datetime'
        except:
            error = 'Could not parse date "' + s + '" into a valid format.'
    if error == '':
        return {'text': s, 'format': dateformat}
    else:
        return {'text': s, 'format': 'unknown', 'error': error}


def textarea2datelist(textarea):
    """Converts a textarea string into a list of date dicts.
    """

    lines = textarea.replace('-\n', '- \n').split('\n')
    all_lines = []
    for line in lines:
        line = line.replace(', ', ',')
        dates = line.split(',')
        for item in dates:
            if re.search(' - ', item): # Check for ' -'
                d = {'range': {'start': ''}}
                range = item.split(' - ')
                start = testformat(range[0])
                end = testformat(range[1])
                # Make sure start date precedes end date
                try:
                    if end['text'] == '':
                        d['range']['start'] = start
                    else:
                        assert start['text'] < end['text']
                        d['range']['start'] = start
                        d['range']['end'] = end
                except:
                    d = {'error': 'The start date "' + start['text'] + '" must precede the end date "' + end['text'] + '".'}
                else:
                      d['range']['start'] = start
            else:
                d = testformat(item)
            all_lines.append(d)
    return all_lines


def flatten_datelist(all_lines):
    """Flattens the output of textarea2datelist() by removing 'text' and 'format' properties
    and replacing their container dicts with a simple date string.
    """
    flattened = []
    for line in all_lines:
        if 'text' in line:
            line = line['text']
        if 'range' in line:
            line['range']['start'] = line['range']['start']['text']
            if 'end' in line['range'] and line['range']['end'] == '':
                line['range']['end'] = line['range']['end']['text']
            elif 'end' in line['range'] and line['range']['end'] != '':
                line['range']['end'] = line['range']['end']['text']
        flattened.append(line)
    return flattened


def serialize_datelist(flattened_datelist):
    """Converts the output of flatten_datelist() to a line-delimited string suitable for
    returning to the UI as the value of a textarea.
    """
    dates = []
    for item in flattened_datelist:
        if isinstance(item, dict) and 'error' not in item:
            start = item['range']['start'] + ' - '
            if 'end' in item['range']:
                end = item['range']['end']
                dates.append(start + end)
            else:
                dates.append(start)
        else:
            dates.append(str(item)) # error dict is cast as a string
    return '\n'.join(dates)


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
