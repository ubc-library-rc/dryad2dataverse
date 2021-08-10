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
    os.path.dirname(__file__), 'dryad2dataverse', '__init__.py')

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
REQUIRES = [req.strip().replace('==',' >= ') for req in
            open('requirements.txt').readlines()]

# NAME to project name
CONFIG = {
    'description': 'Dryad to Dataverse Migrator',
    'author': 'Paul Lesack',
    'license': 'MIT',
    'url': 'https://ubc-library-rc.github.io/dryad2dataverse/',
    'download_url': 'https://github.com/ubc-library-rc/dryad2dataverse',
    'author_email': 'paul.lesack@ubc.ca',
    'classifiers' : ['Development Status :: 4 - Beta',
                     'Intended Audience :: Education',
                     'License :: OSI Approved :: MIT License'
                     'Programming Language :: Python :: 3.6',
                     'Programming Language :: Python :: 3.7',
                     'Programming Language :: Python :: 3.8',
                     'Programming Language :: Python :: 3.9',
                     'Programming Language :: Python :: 3.10',
                     'Topic :: Education'],
    'project_urls' : {'Documentation': 'https://ubc-library-rc.github.io/dryad2dataverse',
                      'Source': 'https://github.com/ubc-library-rc/dryad2dataverse',
                      'Tracker': 'https://github.com/ubc-library-rc/dryad2dataverse/issues'},
    'keywords' : ['Dryad', 'Dataverse', 'datadryad.org', 'dataverse.org'],
    'version' : PKG_VERSION,
    'python_requires': '>=3.6',
    'install_requires': REQUIRES,
    'packages': ['dryad2dataverse'],
    'scripts':['scripts/dryadd.py'],
    'name': 'dryad2dataverse'
}

setup(**CONFIG)
