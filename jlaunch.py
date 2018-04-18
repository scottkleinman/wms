# import subprocess
# file = 'NotebookTest.ipynb'
# command = 'jupyter nbconvert --execute --inplace --to notebook ' + file
# args = [
#     "jupyter", 
#     "nbconvert", 
#     "--execute", 
#     "--inplace", 
#     "to", 
#     "notebook", 
#     file
# ]
# subprocess.run(args, stdout=subprocess.PIPE)

file = 'NotebookTest.ipynb'
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

with open(file) as f:
    nb = nbformat.read(f, as_version=4)

ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
# ep.preprocess(nb, {'metadata': {'path': 'notebooks/'}})
ep.preprocess(nb, {})

   