'''
This module contains the information that configures all the parameters
required to transfer data from Dryad to Dataverse.

"Constants" may be a bit strong, but the only constant is the
presence of change.
'''

import os

#used in dryad2dataverse.serializer
DRYURL = 'https://datadryad.org'
TMP = '/tmp'

#used in dryad2dataverse.transfer
DVURL = 'https://dataverse.scholarsportal.info'
APIKEY = None
MAX_UPLOAD = 3221225472 #Max 3GB upload
DV_CONTACT_EMAIL = None
DV_CONTACT_NAME = None
NOTAB = ['.sav', '.por', '.zip', '.csv', '.tsv', '.dta', '.rdata', '.xslx']

#used in dryad2dataverse.monitor
HOME = os.path.expanduser('~')
DBASE = HOME + os.sep + 'dryad_dataverse_monitor.sqlite3'
