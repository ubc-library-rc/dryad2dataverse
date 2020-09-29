try:
    from setuptools import setup
except ImportError:
    from distutils.core mport setup
# NAME to project name
config = {
    'description': 'Dryad to Dataverse Migrator',
    'author': 'Paul Lesack',
    'license': 'MIT'
    'url': 'https://researchcommons.library.ubc.ca',
    'download_url': 'http://actual.download.example.com',
    'author_email': 'paul.lesack@ubc.ca',
    'version' : '0.1',
    'install_requires': ['nose222'],
    'packages': ['dryad2dataverse'], 
    'scripts':[],
    'name': 'dryad2dataverse'
}

setup(**config)
