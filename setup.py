'''
dryad2dataverse

This module:

* Serializes metadata from the Dryad data repository at https://datadryad.org to Dataverse JSON

* Transferse the data from Dryad studies to a Dataverse reepository

* Implements persistent tracking of changes via a SQLite database.

'''
import os
import ast

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

init = os.path.join(
    os.path.dirname(__file__), '__init__.py')

version_line = list(
    filter(lambda l: l.startswith('VERSION'), open(init)))[0].strip()

def get_version(version_tuple):
    '''Get version from module'''
    if not isinstance(version_tuple[-1], int):
        return '.'.join(
            map(str, version_tuple[:-1])
        ) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))


PKG_VERSION = get_version(ast.literal_eval(version_line.split('=')[-1].strip()))



# NAME to project name
CONFIG = {
    'description': 'Dryad to Dataverse Migrator',
    'author': 'Paul Lesack',
    'license': 'MIT',
    'url': 'https://ubc-library-rc.github.io/dryad2dataverse/',
    'download_url': 'https://github.com/ubc-library-rc/dryad2dataverse',
    'author_email': 'paul.lesack@ubc.ca',
    'version' : PKG_VERSION,
    'install_requires': ['requests_toolbelt'],
    'packages': ['dryad2dataverse'],
    'scripts':['scripts/dryadd.py'],
    'name': 'dryad2dataverse'
}

setup(**CONFIG)
