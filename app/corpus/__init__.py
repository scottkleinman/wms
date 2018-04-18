import os, tabulator, itertools, requests, json, re, zipfile, shutil
import subprocess
import yaml

# For various solutions to dealing with ObjectID, see
# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
# If speed becomes an issue: https://github.com/mongodb-labs/python-bsonjs
from bson import BSON
from bson import json_util
JSON_UTIL = json_util.default

# from datetime import datetime
from jsonschema import validate, FormatChecker
# from tabulator import Stream
# import pandas as pd
# from tableschema_pandas import Storage
from flask import Blueprint, render_template, request, url_for, current_app, send_file
from werkzeug.utils import secure_filename

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections" 
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
corpus_db = db.Corpus

corpus = Blueprint('corpus', __name__, template_folder='corpus')

from app.corpus.helpers import methods as methods

#----------------------------------------------------------------------------#
# Constants.
#----------------------------------------------------------------------------#

ALLOWED_EXTENSIONS = ['xlsx']

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@corpus.route('/')
def index():
	"""Corpus index page."""
	scripts = ['js/corpus/corpus.js']
	return render_template('corpus/index.html', scripts=scripts)


@corpus.route('/create', methods=['GET', 'POST'])
def create():
	"""Create manifest page."""
	scripts = ['js/parsley.min.js', 'js/corpus/corpus.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/create', 'label': 'Create Collection'}]
	with open("app/templates/corpus/template_config.yml", 'r') as stream:
		templates = yaml.load(stream)
	return render_template('corpus/create.html', scripts=scripts, templates=templates, breadcrumbs=breadcrumbs)


@corpus.route('/create-manifest', methods=['GET', 'POST'])
def create_manifest():
	""" Ajax route for creating manifests."""
	errors = []
	data = request.json
	# data['namespace'] = 'we1sv2.0'
	# Set name and path by branch
	if data['nodetype'] == 'collection':
		try:
			assert data['metapath'] == 'Corpus'
		except:
			errors.append('The <code>metapath</code> for a collection must be "Corpus".')
	elif data['nodetype'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
		data['name'] = data['nodetype']
	else:
		pass
	if not data['metapath'].startswith('Corpus'):
		data['metapath'] = 'Corpus,' + data['metapath']
	data['metapath'] = data['metapath'].strip(',')
	# if not data['metapath'].endswith(','):
	# 	data['path'] += ','
	# Remove empty values
	manifest = {}
	for key, value in data.items():
		if value != '':
			manifest[key] = value
	# Handle dates
	# if 'date' in manifest.keys():
	# 	dates = manifest['date'].splitlines()
	# 	dates = [x.strip() for x in dates]
	# 	new_dates, error_list = methods.check_date_format(dates)
	# 	errors = errors + error_list
	# 	if new_dates  != []:
	# 		manifest['date'] = dates
	if 'created' in manifest.keys():
		created = methods.flatten_datelist(methods.textarea2datelist(manifest['created']))
		if isinstance(created, list) and len(created) == 1:
			created = created[0]

	if 'updated' in manifest.keys():
		updated = methods.flatten_datelist(methods.textarea2datelist(manifest['updated']))
		if isinstance(updated, list) and len(updated) == 1:
			updated = updated[0]

	# Handle other textarea strings
	list_props = ['sources', 'contributors', 'queryterms', 'processes', 'notes', 'keywords', 'licenses']
	prop_keys = {
		'sources': { 'main_key': 'title', 'valid_props': ['title', 'path', 'email'] },
		'contributors': { 'main_key': 'title', 'valid_props': ['title', 'email', 'path', 'role', 'group', 'organization'] },
		'licenses': { 'main_key': 'name', 'valid_props': ['name', 'path', 'title'] },
		'queryterms': { 'main_key': '', 'valid_props': [] },
		'processes': { 'main_key': '', 'valid_props': [] },
		'notes': { 'main_key': '', 'valid_props': [] },
		'keywords': { 'main_key': '', 'valid_props': [] }
	}
	for item in list_props:
		if item in manifest and manifest[item] != '':
			all_lines = methods.textarea2dict(item, manifest[item], prop_keys[item]['main_key'], prop_keys[item]['valid_props'])
			if all_lines[item] != []:
				manifest[item] = all_lines[item]
	nodetype = manifest.pop('nodetype', None)
	if 'OCR' in manifest.keys() and manifest['OCR'] == "on":
		manifest['OCR'] = True
	# Validate the resulting manifest
	if methods.validate_manifest(manifest, nodetype) == True:
		database_errors = methods.create_record(manifest)
		errors = errors + database_errors
	else:
		msg = '''A valid manifest could not be created with the 
		data supplied. Please check your entries against the 
		<a href="/schema" target="_blank">manifest schema</a>.''' 
		errors.append(msg)

	manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
	if len(errors) > 0:
		error_str = '<ul>'
		for item in errors:
			error_str += '<li>' + item + '</li>'
		error_str += '</ul>'
	else:
		error_str = ''
	response = {'manifest': manifest, 'errors': error_str}
	return json.dumps(response)


@corpus.route('/display/<name>')
def display(name):
	""" Page for displaying Corpus manifests."""
	scripts = ['js/parsley.min.js', 'js/corpus/corpus.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/display', 'label': 'Display Collection'}]
	errors = []
	manifest = {}
	result = corpus_db.find_one({'name': name})
	try:
		result = corpus_db.find_one({'name': name})
		assert result != None
		for key, value in result.items():
			if isinstance(value, list):
				textarea = methods.dict2textarea(value)
				manifest[key] = textarea
			# if isinstance(value, list):
			# 	manifest[key] = []
			# 	for element in value:
			# 		if isinstance(element, dict):
			# 			l = list(methods.NestedDictValues(element))
			# 			s = ', '.join(l)
			# 			manifest[key].append(s)
			# 		else:
			# 			manifest[key].append(element)
			# 	manifest[key] = '\n'.join(manifest[key])
			else:
				manifest[key] = str(value)
		if manifest['metapath'] == 'Corpus':
			nodetype = 'collection'
		elif manifest['name'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
			nodetype = manifest['name'].lower()
		else:
			nodetype = 'branch'
		with open("app/templates/corpus/template_config.yml", 'r') as stream:
			templates = yaml.load(stream)
	except:
		errors.append('Unknown Error: The manifest does not exist or could not be loaded.')
	return render_template('corpus/display.html', scripts=scripts,
		breadcrumbs=breadcrumbs, manifest=manifest, errors=errors,
		nodetype=nodetype, templates=templates)


@corpus.route('/update-manifest', methods=['GET', 'POST'])
def update_manifest():
	""" Ajax route for updating manifests."""
	errors = []
	data = request.json
	# data['namespace'] = 'we1sv2.0'
	# Set name and path by branch
	if data['metapath'] == 'Corpus':
		data['nodetype'] = 'collection'
	elif data['name'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
		data['nodetype'] = data['name']
		data['metapath'] = 'Corpus,' + data['metapath']
	else:
		data['nodetype'] = 'branch'
		data['metapath'] = 'Corpus,' + data['metapath']
	data['metapath'] =  data['metapath'].replace('Corpus,Corpus,', 'Corpus,').strip(',')
	# Remove empty values
	manifest = {}
	for key, value in data.items():
		if value != '':
			manifest[key] = value
	# Handle dates
	# if 'date' in manifest.keys():
	# 	ls = manifest['date'].splitlines()
	# 	dates = [x.strip() for x in ls]
	# 	new_dates, error_list = methods.check_date_format(dates)
	# 	errors = errors + error_list
	# 	manifest['date'] = new_dates
	if 'created' in manifest.keys():
		created = methods.flatten_datelist(methods.textarea2datelist(manifest['created']))
		if isinstance(created, list) and len(created) == 1:
			created = created[0]
		manifest['created'] = created
		print('Created')
		print(created)

	if 'updated' in manifest.keys():
		updated = methods.flatten_datelist(methods.textarea2datelist(manifest['updated']))
		if isinstance(updated, list) and len(updated) == 1:
			updated = updated[0]
		manifest['updated'] = created

	# Handle other textarea strings
	# Handle other textarea strings
	list_props = ['sources', 'contributors', 'queryterms', 'processes', 'notes', 'keywords', 'licenses']
	prop_keys = {
		'sources': { 'main_key': 'title', 'valid_props': ['title', 'path', 'email'] },
		'contributors': { 'main_key': 'title', 'valid_props': ['title', 'email', 'path', 'role', 'group', 'organization'] },
		'licenses': { 'main_key': 'name', 'valid_props': ['name', 'path', 'title'] },
		'queryterms': { 'main_key': '', 'valid_props': [] },
		'processes': { 'main_key': '', 'valid_props': [] },
		'notes': { 'main_key': '', 'valid_props': [] },
		'keywords': { 'main_key': '', 'valid_props': [] }
	}
	for item in list_props:
		if item in manifest and manifest[item] != '':
			all_lines = methods.textarea2dict(item, manifest[item], prop_keys[item]['main_key'], prop_keys[item]['valid_props'])
			if all_lines[item] != []:
				manifest[item] = all_lines[item]

	# list_props = ['publications', 'collectors', 'queryterms', 'processes', 'notes']
	# for item in list_props:
	# 	if item in manifest:
	# 		ls = manifest[item].splitlines()
	# 		manifest[item] = [x.strip() for x in ls]
	nodetype = manifest.pop('nodetype', None)
	if 'OCR' in manifest.keys() and manifest['OCR'] == "on":
		manifest['OCR'] = True

	# Validate the resulting manifest
	if methods.validate_manifest(manifest, nodetype) == True:
		database_errors = methods.update_record(manifest)
		errors = errors + database_errors
	else:
		msg = '''A valid manifest could not be created with the 
		data supplied. Please check your entries against the 
		<a href="/schema" target="_blank">manifest schema</a>.''' 
		errors.append(msg)

	manifest = json.dumps(manifest, indent=2, sort_keys=False)
	if len(errors) > 0:
		error_str = '<ul>'
		for item in errors:
			error_str += '<li>' + item + '</li>'
		error_str += '</ul>'
	else:
		error_str = ''
	response = {'manifest': manifest, 'errors': error_str}
	return json.dumps(response)


@corpus.route('/send-export', methods=['GET', 'POST'])
def send_export():
	""" Ajax route to process user export options and write 
	the export files to the temp folder.
	"""
	data = request.json
	# The user only wants to print the manifest
	if data['exportoptions'] == ['manifestonly']:
		query = {'name': data['name'], 'metapath': data['metapath']}
		try:
			result = corpus_db.find_one(query)
			assert result != None
			manifest = {}
			for key, value in result.items():
				if value != '' and value != []:
					manifest[key] = value
			manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
			filename = data['name'] + '.json'
			doc = filename
			methods.make_dir('app/temp')
			filepath = os.path.join('app/temp', filename)
			with open(filepath, 'w') as f:
				f.write(manifest)
		except:
			print('Could not find the manifest in the database.')
	# The user wants a zip of multiple data documents
	else:
		# Get the exportoptions with the correct case
		methods.make_dir('app/temp/Corpus')
		name = data['name']
		metapath = data['metapath']
		# Ensures that there is a Corpus and collection folder with a collection manifest
		methods.make_dir('app/temp/Corpus')
		if metapath == 'Corpus':
			collection = name
		else:
			collection = path.split(',')[2]
		methods.make_dir('app/temp/Corpus/' + collection)
		# result = corpus_db.find_one({'metapath': metapath, 'name': collection})
		result = corpus_db.find_one({'metapath': metapath})
		# assert result != None
		manifest = {}
		for key, value in result.items():
			if value != '' and value != []:
				manifest[key] = value
		manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
		filename = name + '.json'
		filepath = os.path.join('app/temp/Corpus', filename)
		with open(filepath, 'w') as f:
			f.write(manifest)
		exportoptions = []
		exportopts = [x.replace('export', '') for x in data['exportoptions']]
		exclude = []
		options = ['Corpus', 'RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']
		if not metapath.startswith('Corpus,'):
			metapath = 'Corpus,' + metapath
		for option in options:
			if option.lower() in exportopts:
				exportoptions.append(option)
			else:
				exclude.append('Corpus' + ',' + name + ',' + option + ',.*')
		# We have a path and a list of metapaths to exclude
		excluded = '|'.join(exclude)
		excluded = re.compile(excluded)
		regex_path = re.compile(metapath + name + ',.*')
		result = corpus_db.find(
			{'metapath': {
				'$regex': regex_path,
				'$not': excluded
			}}
		)
		for item in list(result):
			# Handle schema node manifests
			path = item['metapath'].replace(',', '/')
			if item['name'] in exportoptions:
				folder_path = os.path.join(path, item['name'])
				methods.make_dir('app/temp' + folder_path)
				folder = 'app/temp' + path
				doc = item['name'] + '.json'
			# Handle data and branches
			else:
				# If the document has content, just give it a filename
				try:
					assert item['content']
					doc = item['name'] + '.json'
					folder = 'app/temp' + path
					methods.make_dir(folder)
				# Otherwise, use it to create a folder with a manifest file
				except:
					path = os.path.join(path, item['name'])
					folder = 'app/temp' + path
					methods.make_dir(folder)
					doc = item['name'] + '.json'
			filepath = os.path.join(folder, doc)
			output = json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL)
			with open(filepath, 'w') as f:
				f.write(output)
		# Zip up the file structure
		try:
			source_dir = 'app/temp/Corpus'
			doc = 'Corpus.zip'
			methods.zipfolder(source_dir, source_dir)
		except:
			print('Could not make zip archive.')
	return json.dumps({'filename': doc})


@corpus.route('/download-export/<filename>', methods=['GET', 'POST'])
def download_export(filename):
	""" Ajax route to trigger download and empty the temp folder."""
	from flask import make_response
	filepath = os.path.join('app/temp', filename)
	# Can't get Firefox to save the file extension by any means
	with open(filepath, 'rb') as f:
		response = make_response(f.read())
	os.remove(filepath)
	response.headers['Content-Type'] = 'application/octet-stream'
	response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
	# As a precaution, empty the temp folder
	shutil.rmtree('app/temp')
	methods.make_dir('app/temp')
	return response


@corpus.route('/search1', methods=['GET', 'POST'])
def search():
	""" Page for searching Corpus manifests."""
	scripts = ['js/parsley.min.js', 'js/jquery.twbsPagination.min.js', 'js/corpus/corpus.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/search', 'label': 'Search Collections'}]
	if request.method == 'GET':
		return render_template('corpus/search.html', scripts=scripts, breadcrumbs=breadcrumbs)
	if request.method == 'POST':
		result, num_pages, errors = methods.search_collections(request.json)
		if result == []:
			errors.append('No records were found matching your search criteria.')
		return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors})


@corpus.route('/search', methods=['GET', 'POST'])
def search2():
	""" Experimental Page for searching Corpus manifests."""
	scripts = ['js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/corpus/corpus.js', 'js/jquery-sortable-min.js', 'js/corpus/search.js']
	styles = ['css/query-builder.default.css']	
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/search', 'label': 'Search Collections'}]
	if request.method == 'GET':
		return render_template('corpus/search2.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)
	if request.method == 'POST':
		query = request.json['query']
		page = int(request.json['page'])
		limit = int(request.json['advancedOptions']['limit'])
		sorting = []
		if request.json['advancedOptions']['show_properties'] != []:
			show_properties = request.json['advancedOptions']['show_properties']
		else:
			show_properties = ''
		paginated = True
		sorting = []
		for item in request.json['advancedOptions']['sort']:
			if item[1] == 'ASC':
				opt = (item[0], pymongo.ASCENDING)
			else:
				opt = (item[0], pymongo.DESCENDING)
			sorting.append(opt)
		result, num_pages, errors = methods.search_corpus(query, limit, paginated, page, show_properties, sorting)
		if result == []:
			errors.append('No records were found matching your search criteria.')
		return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)

@corpus.route('/export-search', methods=['GET', 'POST'])
def export_search():
	""" Ajax route for exporting search results."""
	if request.method == 'POST':
		query = request.json['query']
		page = 1
		limit = int(request.json['advancedOptions']['limit'])
		sorting = []
		if request.json['advancedOptions']['show_properties'] != []:
			show_properties = request.json['advancedOptions']['show_properties']
		else:
			show_properties = ''
		paginated = False
		sorting = []
		for item in request.json['advancedOptions']['sort']:
			if item[1] == 'ASC':
				opt = (item[0], pymongo.ASCENDING)
			else:
				opt = (item[0], pymongo.DESCENDING)
			sorting.append(opt)
		result, num_pages, errors = methods.search_corpus(query, limit, paginated, page, show_properties, sorting)
		if len(result) == 0:
			errors.append('No records were found matching your search criteria.')
		# Need to write the results to temp folder
		for item in result:
			filename = item['name'] + '.json'
			filepath = os.path.join('app/temp', filename)
			with open(filepath, 'w') as f:
				f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
		# Need to zip up multiple files
		if len(result) > 1:
			filename = 'search_results.zip'
			methods.zipfolder('app/temp', 'search_results')
		return json.dumps({'filename': filename, 'errors': errors}, default=JSON_UTIL)


@corpus.route('/delete-manifest', methods=['GET', 'POST'])
def delete_manifest():
	""" Ajax route for deleting manifests."""
	errors = []
	msg = methods.delete_collection(request.json['name'])
	if msg  != 'success':
		errors.append(msg)
	return json.dumps({'errors': errors})


@corpus.route('/import', methods=['GET', 'POST'])
def import_data():
	""" Page for importing manifests."""
	scripts = [
	'js/corpus/dropzone.js',
	'js/parsley.min.js', 
	'js/corpus/corpus.js',
	'js/corpus/upload.js'
	]
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/import', 'label': 'Import Collection Data'}]
	return render_template('corpus/import.html', scripts=scripts, breadcrumbs=breadcrumbs)


@corpus.route('/remove-file', methods=['GET', 'POST'])
def remove_file():
	"""Ajax route triggered when a file is deleted from the file
	uploads table. This function ensures that it is removed from
	both the database and the uploads folder.
	"""
	if request.method == 'POST':
		# Delete the record (if it exists) from the database
		collection = request.json['collection']
		if collection.startswith(',Corpus,'):
			collection = collection.replace(',Corpus,', '')
		path = ',Corpus,' + collection + ',' + request.json['category'] + ','
		if request.json['branch'] != '':
			path = path + request.json['branch'] + ','
		filename = request.json['filename'] 
		name = filename.strip('.json')
		corpus_db.delete_one({'path': path, 'name': name})
		# Now delete the file (if it exists) in the uploads folder
		mydir = os.path.join('app', current_app.config['UPLOAD_FOLDER'])
		myfile = os.path.join(mydir, filename)
		# The removal should only fail if there is no DB entry or file to remove.
		# So no need to handle errors.
		return json.dumps({'response': 'success'})


@corpus.route('/save-upload', methods=['GET', 'POST'])
def save_upload():
	""" Ajax route to create a manifest for each uploaded file  
	and insert it in the database.
	"""
	if request.method == 'POST':
		errors = []
		# Handle the form data
		exclude = ['branch', 'category', 'collection']
		node_metadata = {}
		for key, value in request.json.items():
			if key not in exclude and value != '' and value != []:
				node_metadata[key] = value
		# Set the name and metapath
		if request.json['collection'].startswith('Corpus,'):
			collection = request.json['collection']
		else:
			collection = 'Corpus,' + request.json['collection']
		try:
			result = list(corpus_db.find({'metapath': 'Corpus', 'name': request.json['collection']}))
			assert result != []
			# Set the name and path for the new manifest
			node_metadata = {}
			if request.json['branch'] != '':
				node_metadata['name'] = request.json['branch']
				node_metadata['metapath'] = collection + ',' + request.json['category']
			else:
				node_metadata['name'] = request.json['category']
				node_metadata['metapath'] = collection
			mydir = os.path.join('app', current_app.config['UPLOAD_FOLDER'])
			# Make sure files exist in the uploads folder
			if len(os.listdir(mydir)) > 0:
				# If the category or branch node does not exist, create it
				"""
				This section has the effect of forcing unique names, so it
				will have to be changed.
				"""
				# parent = list(corpus_db.find({'name': node_metadata['name'], 'path': node_metadata['path']}))
				# if len(parent) == 0:
				# 	try:					
				# 		corpus_db.insert_one(node_metadata)
				# 	except:
				# 		print('Could not create a RawData node.')
				# Now start creating a data manifest for each file and inserting it
				for filename in os.listdir(mydir):
					filepath = os.path.join(mydir, filename)
					metapath = node_metadata['metapath'] + ',' + node_metadata['name'] + ','
					manifest = {'name': os.path.splitext(filename)[0], 'namespace': 'we1sv2.0', 'metapath': metapath}
					try:
						with open(filepath, 'rb') as f:
							doc = json.loads(f.read())
							for key, value in doc.items():
								if key not in ['name', 'namespace', 'metapath']:
									manifest[key] = value
					except:
						errors.append('The file <code>' + filename + '</code> could not be loaded or it did not have a <code>content</code> property.')
					schema_file = 'https://raw.githubusercontent.com/whatevery1says/manifest/master/schema/v2.0/Corpus/Data.json'
					schema = json.loads(requests.get(schema_file).text)
					try:
						methods.validate(manifest, schema, format_checker=FormatChecker())
						result = methods.create_record(manifest)
						errors = errors + result
					except:
						print('Could not validate manifest for ' + filename)
						errors.append('A valid manifest could not be created from the file <code>' + filename + '</code> or the manifest could not be added to the database due to an unknown error.')
				# We're done. Empty the uploads folder.
				mydir = os.path.join('app', current_app.config['UPLOAD_FOLDER'])
				list(map(os.unlink, (os.path.join(mydir,f) for f in os.listdir(mydir))))
			else:
				print('There were no files in the uploads directory.')
		except:
			errors.append('The specified collection does not exist in the database. Check your entry or <a href="/corpus/create">create a collection</a> before importing data.')
		if errors == []:			
			response = {'response': 'Manifests created successfully.'}
		else:
			response = {'errors': errors}
		return json.dumps(response)


@corpus.route('/upload', methods=['GET', 'POST'])
def upload():
	"""Ajax route saves each file uploaded by the import function
	to the uploads folder.
	"""
	if request.method == 'POST':
		errors = []
		for file in request.files.getlist('file'):
			# Accept only json files for now...
			if file.filename.endswith('.json'):
				try:
					filename = secure_filename(file.filename)
					file_to_save = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
					file_to_save = os.path.join('app', file_to_save)
					file.save(file_to_save)
				except:
					errors.append('<p>Unknown Error: Could not save the file <code>' + filename + '</code>.</p>')
			else:
				errors.append('<p>The file <code>' + file.filename + '</code> has an invalid file type.</p>')					
		if errors == []:			
			response = {'response': 'file(s) saved successfully'}
		else:
			response = {'errors': errors}
		return json.dumps(response)					


@corpus.route('/clear')
def clear():
	""" Going to this page will quickly empty the datbase.
	Disable this for production.
	"""
	corpus_db.delete_many({})
	return 'success'



@corpus.route('/launch-jupyter', methods=['GET', 'POST'])
def launch_jupyter():
	""" Experimental Page to launch a Jupyter notebook."""
	if request.method == 'POST':
		try:
			query = request.json['query']
			limit = int(request.json['advancedOptions']['limit'])
			sorting = []
			if request.json['advancedOptions']['show_properties'] != []:
				show_properties = request.json['advancedOptions']['show_properties']
			else:
				show_properties = '\'\''
			sorting = []
			for item in request.json['advancedOptions']['sort']:
				if item[1] == 'ASC':
					opt = (item[0], pymongo.ASCENDING)
				else:
					opt = (item[0], pymongo.DESCENDING)
				sorting.append(opt)
			sorting = "[('name', pymongo.ASCENDING)]"
			q = 'result = list(corpus_db.find(' + str(query) + ', '
			q += 'limit=' + str(limit) + ', '
			q += 'projection=' + str(show_properties) + ')'
			if sorting != []:
				q += '.sort(' + str(sorting) + ')'
			q += ')'
			template_path = os.path.join('app', 'jupyter_notebook_template.ipynb')
			with open(template_path, 'r') as f:
				doc = f.read()
			doc = doc.replace('USER_QUERY', q)
			file_path = os.path.join('app', 'WMS_query.ipynb')
			with open(file_path, 'w') as f:
				f.write(doc)
			# This works but breaks the Flask process, even with shell=True
			# subprocess.call(['jupyter', 'notebook'], shell=False)
			subprocess.run(['nbopen', file_path], stdout=subprocess.PIPE)
			return 'success'
		except:
			return 'error'
