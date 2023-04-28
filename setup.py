'''
dryad2dataverse

This module:

* Serializes metadata from the Dryad data repository at https://datadryad.org to Dataverse JSON

* Transferse the data from Dryad studies to a Dataverse reepository

* Implements persistent tracking of changes via a SQLite database.

'''
from setuptools import setup

REQUIRES = [req.strip().replace('==',' >= ') for req in
            open('requirements.txt').readlines()]

#setup( {'requires':REQUIRES})
setup() 
