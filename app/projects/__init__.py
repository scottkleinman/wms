import os, tabulator, itertools, requests, json, re, zipfile, shutil
from pathlib import Path
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
projects_db = db.Projects
corpus_db = db.Corpus

projects = Blueprint('projects', __name__, template_folder='projects')

from app.projects.helpers import methods as methods

#----------------------------------------------------------------------------#
# Constants.
#----------------------------------------------------------------------------#

ALLOWED_EXTENSIONS = ['zip']

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@projects.route('/')
def index():
	"""Projects index page."""
	scripts = ['js/projects/projects.js']
	with open("app/templates/projects/template_config.yml", 'r') as stream:
		templates = yaml.load(stream)
	return render_template('projects/index.html', scripts=scripts)


@projects.route('/create', methods=['GET', 'POST'])
def create():
	"""Create manifest page."""
	scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery-sortable-min.js', 'js/projects/search.js']
	styles = ['css/query-builder.default.css']	
	breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/create', 'label': 'Create Project'}]
	with open('app/templates/projects/template_config.yml', 'r') as stream:
		templates = yaml.load(stream)
	return render_template('projects/create.html', scripts=scripts, styles=styles, templates=templates, breadcrumbs=breadcrumbs)


@projects.route('/test-query', methods=['GET', 'POST'])
def test_query():
	"""Tests whether the project query returns results 
	from the Corpus."""
	query = json.loads(request.json['db-query'])
	result = corpus_db.find(query)
	if len(list(result)) > 0:
		response = """Your query successfully found records in the Corpus database. 
		If you wish to view the results, please use the 
		<a href="/corpus/search">Corpus search</a> function."""
	else:
		response = """Your query did not return any records in the Corpus database. 
		Try the <a href="/corpus/search">Corpus search</a> function to obtain a 
		more accurate query."""
	if len(list(corpus_db.find())) == 0:
		response = 'The Corpus database is empty.'
	return response

# @projects.route('/create-manifest', methods=['GET', 'POST'])
# def create_manifest():
# 	""" Ajax route for creating manifests."""
# 	manifest = {}
# 	errors = []
# 	data = request.json
# 	response = {'manifest': manifest, 'errors': error_str}
# 	return json.dumps(response)


@projects.route('/display/<name>')
def display(name):
	""" Page for displaying Project manifests."""
	scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery-sortable-min.js', 'js/projects/search.js']
	styles = ['css/query-builder.default.css']	
	breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/display', 'label': 'Display Project Manifest'}]
	errors = []
	manifest = {}
	try:
		result = projects_db.find_one({'name': name})
		assert result != None
		for key, value in result.items():
			if key == 'content':
				pass
			elif isinstance(value, list):
				textarea = methods.dict2textarea(value)
				manifest[key] = textarea
			else:
				manifest[key] = str(value)
		print(manifest)
		with open('app/templates/projects/template_config.yml', 'r') as stream:
			templates = yaml.load(stream)
	except:
		errors.append('Unknown Error: The manifest does not exist or could not be loaded.')
	return render_template('projects/display.html', scripts=scripts,
		breadcrumbs=breadcrumbs, manifest=manifest, errors=errors,
		templates=templates)


@projects.route('/update-manifest', methods=['GET', 'POST'])
def update_manifest():
	""" Ajax route for updating manifests."""
	errors = []
	data = request.json
	manifest = {}
	for key, value in data.items():
		if value != '':
			manifest[key] = value
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
	# Might be an issue here -- what are "resources". Is that in the schema?
	list_props = ['resources', 'contributors', 'notes', 'keywords', 'licenses']
	prop_keys = {
		'resources': { 'main_key': 'title', 'valid_props': ['title', 'path', 'email'] },
		'contributors': { 'main_key': 'title', 'valid_props': ['title', 'email', 'path', 'role', 'group', 'organization'] },
		'licenses': { 'main_key': 'name', 'valid_props': ['name', 'path', 'title'] },
		'notes': { 'main_key': '', 'valid_props': [] },
		'keywords': { 'main_key': '', 'valid_props': [] }
	}
	for item in list_props:
		if item in manifest and manifest[item] != '':
			all_lines = methods.textarea2dict(item, manifest[item], prop_keys[item]['main_key'], prop_keys[item]['valid_props'])
			if all_lines[item] != []:
				manifest[item] = all_lines[item]

	# Validate the resulting manifest
	if methods.validate_manifest(manifest) == True:
		# errors = ['The manifest validated.']
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


@projects.route('/export-project', methods=['GET', 'POST'])
def export_project():
	""" Ajax route to process user export options and write 
	the export files to the temp folder.
	"""
	errors = []
	# Remove empty form values and form builder parameters
	data = {}
	for k, v in request.json['data'].items():
		if v != '' and not k.startswith('builder_'):
			data[k] = v

	# Add the resources property 
	resources = []
	for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
		resources.append({'path': '/' + folder})
	data['resources'] = resources

	# Remove the query so the data dict is a valid datapackage.
	# This could be left in if people wanted it for the record.
	query = json.loads(data.pop('db-query'))

	# Define a project name
	project_name = data['name']
	zipfilename = project_name + '.zip'

	# Create the project folder and save the datapackage to it
	temp_folder = os.path.join('app', current_app.config['TEMP_FOLDER'])
	project_dir = os.path.join(temp_folder, project_name)
	Path(project_dir).mkdir(parents=True, exist_ok=True)
	# Make the standard folders
	for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
		new_folder = Path(project_dir) / folder
		Path(new_folder).mkdir(parents=True, exist_ok=True)
	# Write the datapackage
	datapackage = os.path.join(project_dir, 'datapackage.json')
	with open(datapackage, 'w') as f:
		f.write(json.dumps(data, indent=2, sort_keys=False, default=JSON_UTIL))

	# Query the database
	result = list(corpus_db.find(query))
	if len(result) == 0:
		errors.append('No records were found matching your search criteria.')
	else:
		for item in result:
			# Make sure every metapath is a directory
			path = Path(project_dir) / item['metapath'].replace(',', '/')
			Path(path).mkdir(parents=True, exist_ok=True)
			
			# Write a file for every manifest -- only handles json
			if 'content' in item:
				filename = item['name'] + '.json'
				filepath = path / filename
				with open(filepath, 'w') as f:
					f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
		# Zip the project_dir to the temp folder and send the file
		methods.zipfolder(project_dir, project_name)

	# Return the filename so that the browser can retrieve it
	return json.dumps({'filename': zipfilename, 'errors': errors}, default=JSON_UTIL)

@projects.route('/download-export/<filename>', methods=['GET', 'POST'])
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


@projects.route('/search', methods=['GET', 'POST'])
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


@projects.route('/export-search', methods=['GET', 'POST'])
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


@projects.route('/delete-manifest', methods=['GET', 'POST'])
def delete_manifest():
	""" Ajax route for deleting manifests."""
	errors = []
	name = request.json['name']
	metapath = request.json['metapath']
	msg = methods.delete_project(name, metapath)
	if msg  != 'success':
		errors.append(msg)
	return json.dumps({'errors': errors})


@projects.route('/import', methods=['GET', 'POST'])
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


@projects.route('/remove-file', methods=['GET', 'POST'])
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


@projects.route('/save-upload', methods=['GET', 'POST'])
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


@projects.route('/upload', methods=['GET', 'POST'])
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


@projects.route('/clear')
def clear():
	""" Going to this page will quickly empty the datbase.
	Disable this for production.
	"""
	corpus_db.delete_many({})
	return 'success'



@projects.route('/launch-jupyter', methods=['GET', 'POST'])
def launch_jupyter():
	""" Experimental Page to launch a Jupyter notebook."""
	try:
		notebook = request.json['notebook']
		query = request.json['data']['db-query']
		querystring = 'result = list(corpus_db.find(' + str(query) + '))'
		manifest = {}
		manifest_props = [
			'name', 'metapath', 'namespace', 'title', 'contributors', 
			'created', 'id', '_id', 'description', 'version', 
			'shortTitle', 'label', 'notes', 'keywords', 'image', 
			'updated', 'licenses'
		]
		for k, v in request.json['data'].items():
			if k in manifest_props and v != '':
				manifest[k] = v
		m = str(manifest)
		querystring = querystring.replace('"', '\\"')
		m = 'manifest = ' + m.replace('\'', '\\"')
		template_path = os.path.join('app', 'new_topic_browser_project.ipynb')
		with open(template_path, 'r') as f:
			doc = f.read()
		doc = doc.replace('MANIFEST', m)
		doc = doc.replace('USER_QUERY', querystring)
		filename = manifest['name'] + '.ipynb'
		file_path = os.path.join('app', filename)
		with open(file_path, 'w') as f:
			f.write(doc)
		subprocess.run(['nbopen', file_path], stdout=subprocess.PIPE)
		return 'success'
	except:
		return 'error'
