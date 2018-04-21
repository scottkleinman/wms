# Import nbformat
import nbformat as nbf
nb = nbf.v4.new_notebook()


# Helper functions
def markdown_cell(cell):
    return nbf.v4.new_markdown_cell(cell)

def code_cell(cell):
    return nbf.v4.new_code_cell(cell)


# Cell Definitions
"""
Each cell is a string variable beginning c1, c2, etc. The letter "m" is added
for a Markdown cell and "c" for a code cell. This is just for easy reference.
"""

c1m = """\
# New Topic Browser Project
Create a new Jupyter project for dfr browser generation.
_This notebook is read-only. It may be customized and run, but settings will only be saved in the newly generated projects._"""



c2m = """\
-  v0.1 2016-10-07
-  v0.2 2016-10-07 adapted to Jupyter notebook
-  v0.3 2016-10-13 Jupyter correctly working with mallet
-  v0.4 2016-10-18 Link generation and cleanup, documentation, read only.
-  v0.5 2016-10-19 Incorporate scrubbing script, text_files_clean folder.
-  v0.6 2016-10-19 split off most of project generation into project sub-notebooks
-  v0.7 2016-10-28 add timedate stamps to project names for rapid exploration
-  v0.8 2017-11-02 change to Python3
-  v0.9 2017-11-03 strip template checkpoints and cache on copy (switch to shutil.copytree)"""


c3c = """\
## INFO

__author__    = 'Jeremy Douglass'
__copyright__ = 'copyright 2017, The WE1S Project'
__license__   = 'GPL'
__version__   = '0.6'
__email__     = 'jeremydouglass@gmail.com'"""



c4c = """\
## IMPORT

# from distutils.dir_util import copy_tree
from shutil import copytree, ignore_patterns
import os
import datetime"""


c5c = """\
## AUTO-GENERATED VARIABLES

MANIFEST

USER_QUERY

project_name = manifest['title']"""


c6m = """\
## VARIABLES -- FILL OUT"""


c7c = """\
## VARIABLES

## Customize these to specific project name and data

# project_name        = manifest['title']

template_directory  = 'templates/topic_browser_template'
dt = datetime.datetime.today().strftime('%Y%m%d_%H%M_')
project_directory   = 'projects/' + dt + project_name
print(project_directory)

## DOCKER UPDATE NOTES
## updated server from UTC to PST at command line with: (chose America / Los Angeles):
#  dpkg-reconfigure tzdata"""


c8c = """\
## COPY TEMPLATE TO NEW PROJECT

## Initialize new project folder with default template contents
## -- this includes empty folders, stopwords, scripts
## Clean copy -- ignore any checkpoints or pycache in the template folder

copytree(template_directory, project_directory, ignore=ignore_patterns('.ipynb_checkpoints', '__pycache__'))"""


c9c = """\
!ls -la {project_directory}"""


c10m = """\
## NEXT"""


c11c = """\
## NEXT
## Generate a link to the next notebook

from IPython.display import display, HTML
browser_link_html = HTML('<p>A new <strong>'+ template_directory +'</strong> has been set up:<br><strong>'+ project_directory + '</strong></p><h2><a href="' + project_directory + '/1_import_data.ipynb" target="top">Next: Import Data.</h2>')
display(browser_link_html)"""


c12m = """\
----------"""


# List return values of helper functions for each cell and assign the list
# to the notebook's cells object.
nb['cells'] = [
    markdown_cell(c1m),
    markdown_cell(c2m),
    code_cell(c3c),
    code_cell(c4c),
    code_cell(c5c),    
    markdown_cell(c6m),    
    code_cell(c7c),    
    code_cell(c8c),    
    code_cell(c9c),    
    markdown_cell(c10m),    
    code_cell(c11c),    
    markdown_cell(c12m),    
]

# Write the notebook to a file
# nbf.write(nb, 'new_topic_browser.ipynb')
nbf.write(nb, 'test.ipynb')