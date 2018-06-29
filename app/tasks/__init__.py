import os, tabulator, itertools, requests, json, re, zipfile, shutil
import subprocess
from datetime import datetime
from pathlib import Path
from jsonschema import validate, FormatChecker

# For various solutions to dealing with ObjectID, see
# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
# If speed becomes an issue: https://github.com/mongodb-labs/python-bsonjs
from bson import BSON, Binary, json_util
JSON_UTIL = json_util.default

from jsonschema import validate, FormatChecker
from flask import Blueprint, render_template, request, url_for, current_app, send_file
from werkzeug.utils import secure_filename

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections" 
client = MongoClient('mongodb://mongodb:27017')
db = client.we1s
projects_db = db.Projects
corpus_db = db.Corpus

tasks = Blueprint('tasks', __name__, template_folder='tasks')

# from app.tasks.helpers import methods as methods

#----------------------------------------------------------------------------#
# Constants.
#----------------------------------------------------------------------------#

ALLOWED_EXTENSIONS = ['zip']

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@tasks.route('/')
def index():
	"""Tasks index page. The index.html template 
	needs some further conversion from Angular.
	`tasks.js` has been created, but it needs to be 
	converted from Angular."""
	scripts = [] # E.g. ['js/tasks/tasks.js']
	styles = [] # E.g. ['css/tasks/tasks.css']
	breadcrumbs = [{'link': '/tasks', 'label': 'Manage Tasks'}]
	tasks = [
		{'task_name': 'A collection', 'task_id': 'a_collection', 
		'task_result': 'pending', 'task_status': 3}
	]
	# The PySiQ queue handling has been put in a function below.
	queue_needs_handling = False
	if queue_needs_handling:
		handle_queue()
	return render_template('tasks/index.html', scripts=scripts, styles=styles, 
			breadcrumbs=breadcrumbs, tasks=tasks)

def handle_queue():
	"""The code from test_2.py in the PySiQ GitHub repo.
	Print statements have been fixed for Python 3. The PySiQ
	script may need further conversion."""
	import os.path, sys
	sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

	from time import sleep
	from app.tasks import PySiQ
	# from PySiQ import Queue

	# ************************************************************************
	# Initialize queue
	# ************************************************************************

	N_WORKERS = 2

	queue_instance = Queue()
	queue_instance.start_worker(N_WORKERS)

	#NOTE: Uncomment this line to enable verbose queuing
	#queue_instance.enableStdoutLogging()

	# ************************************************************************
	# Queue tasks
	# ************************************************************************

	def foo(task_id, file_path, delay):
		print("Task " +  str(task_id) + " started...")
		file = open(file_path,"a")
		file.write("This is task " + str(task_id) + ". I'm safely writing in this file.\n")
		sleep(delay)
		file.close()
		print("Task " + str(task_id) + " finished")

	queue_instance.enqueue(
		fn=foo,
		args=(1, "/tmp/test_pysiq.log", 10),
		task_id= 1
	)

	queue_instance.enqueue(
		fn=foo,
		args=(2, "/tmp/test_pysiq.log", 5),
		task_id= 2,
		incompatible = ["foo"]
	)

	queue_instance.enqueue(
		fn=foo,
		args=(3, "/tmp/test_pysiq.log", 5),
		task_id= 3,
		depend= [2]
	)