'''
This module contains the information that configures all the parameters
required to transfer data from Dryad to Dataverse.

"Constants" may be a bit strong, but the only constant is the
presence of change.
'''

import os
import pathlib

#from requests.packages.urllib3.util.retry import Retry
#Above causes Pylint error. WHY?
#Because it's a fake path and just a pointer. See requests source
from urllib3.util import Retry


#Requests session retry strategy in case of bad connections
#See :https://findwork.dev/blog/
#advanced-usage-python-requests-timeouts-retries-hooks/#retry-on-failure
#also
#https://stackoverflow.com/questions/15431044/
#can-i-set-max-retries-for-requests-request
RETRY_STRATEGY = Retry(total=10,
                       status_forcelist=[429, 500, 502, 503, 504],
                       method_whitelist=['HEAD', 'GET', 'OPTIONS',
                                         'POST', 'PUT'],
                       backoff_factor=1)

#used in dryad2dataverse.serializer
DRYURL = 'https://datadryad.org'
TMP = '/tmp'

#used in dryad2dataverse.transfer
DVURL = 'https://borealisdata.ca'
APIKEY = None
MAX_UPLOAD = 3221225472 #Max 3GB upload
DV_CONTACT_EMAIL = None
DV_CONTACT_NAME = None
NOTAB = ['.sav', '.por', '.zip', '.csv', '.tsv', '.dta',
         '.rdata', '.xslx', '.xls']

#used in dryad2dataverse.monitor
HOME = os.path.expanduser('~')
DBASE = pathlib.Path(HOME, 'dryad_dataverse_monitor.sqlite3')
