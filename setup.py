'''
dryad2dataverse

This module:

* Serializes metadata from the Dryad data repository at https://datadryad.org to Dataverse JSON

* Transferse the data from Dryad studies to a Dataverse reepository

* Implements persistent tracking of changes via a SQLite database.

'''

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
# NAME to project name
CONFIG = {
    'description': 'Dryad to Dataverse Migrator',
    'author': 'Paul Lesack',
    'license': 'MIT',
    'url': 'https://researchcommons.library.ubc.ca',
    'download_url': 'http://actual.download.example.com',
    'author_email': 'paul.lesack@ubc.ca',
    'version' : '0.1',
    'install_requires': ['nose', 'requests_toolbelt'],
    'packages': ['dryad2dataverse'],
    'scripts':['scripts/sample_loop.py'],
    'name': 'dryad2dataverse'
}

setup(**CONFIG)