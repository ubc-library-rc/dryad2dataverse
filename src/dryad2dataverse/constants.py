'''
This module contains the information that configures all the parameters
required to transfer data from Dryad to Dataverse.

"Constants" may be a bit strong, but the only constant is the
presence of change.
'''
import logging
import pathlib
import importlib.resources
import sys

from typing import Union

#from requests.packages.urllib3.util.retry import Retry
#Above causes Pylint error. WHY?
#Because it's a fake path and just a pointer. See requests source
from urllib3.util import Retry
import yaml

LOGGER = logging.getLogger(__name__)
#Requests session retry strategy in case of bad connections
#See :https://findwork.dev/blog/
#advanced-usage-python-requests-timeouts-retries-hooks/#retry-on-failure
#also
#https://stackoverflow.com/questions/15431044/
#can-i-set-max-retries-for-requests-request
RETRY_STRATEGY = Retry(total=10,
                       status_forcelist=[429, 500, 502, 503, 504],
                       allowed_methods=['HEAD', 'GET', 'OPTIONS',
                                         'POST', 'PUT'],
           backoff_factor=1)

#Variable listings from previous versions of this file
#that are now included in Constants
#
##used in dryad2dataverse.serializer
#DRYURL = 'https://datadryad.org'
#TMP = '/tmp'
#
##used in dryad2dataverse.transfer
#DVURL = 'https://borealisdata.ca'
#APIKEY = None
#MAX_UPLOAD = 3221225472 #Max 3GB upload
#DV_CONTACT_EMAIL = None
#DV_CONTACT_NAME = None
#NOTAB = ['.sav', '.por', '.zip', '.csv', '.tsv', '.dta',
#         '.rdata', '.xslx', '.xls']
#
##used in dryad2dataverse.monitor
#HOME = os.path.expanduser('~')
#DBASE = pathlib.Path(HOME, 'dryad_dataverse_monitor.sqlite3')

class Config(dict):
    '''
    Holds all the information about dryad2dataverse parameters
    '''
    def __init__(self, cpath: Union[pathlib.Path, str]=None,
                 fname:str=None,
                 force:bool=False):
        '''
        Initalize

        Parameters
        ----------
        force : bool
            Force writing a new config file
        '''
        self.cpath = cpath
        self.fname = fname
        self.force = force
        self.default_locations = {'ios': '~/.config/dryad2dataverse',
                     'linux' : '~/.config/dryad2dataverse',
                     'darwin': '~/Library/Application Support/dryad2dataverse',
                     'win32' : 'AppData/Roaming/dryad2dataverse',
                     'cygwin' : '~/.config/dryad2dataverse'}

        #Use read() instead of yaml.safe_load.read_text() so that
        #comments are preserved
        with open(importlib.resources.files(
                    'dryad2dataverse.data').joinpath(
                    'dryad2dataverse_config.yml'), mode='r',
                    encoding='utf-8') as w:
            self.template  = w.read()

        if not self.cpath:
            self.cpath = self.default_locations[sys.platform]
        if not self.fname:
            self.fname = 'dryad2dataverse_config.yml'
        self.configfile = pathlib.Path(self.cpath, self.fname).expanduser()

        if self.make_config_template():
            self.load_config()
        else:
            raise FileNotFoundError(f'Can\'t find {self.configfile}')

    def make_config_template(self):
        '''
        Make a default config if one does not exist
        Returns
        -------
        True if created
        False if not
        '''
        if self.configfile.exists() and not self.force:
            return 1
        if not self.configfile.parent.exists():
            self.configfile.parent.mkdir(parents=True)
        with open(self.configfile, 'w', encoding='utf-8') as f:
            f.write(self.template)
        if self.configfile.exists():
            return 1
        return 0

    def load_config(self):
        '''
        Loads the config to a dict
        '''
        try:
            with open(self.configfile, 'r', encoding='utf-8') as f:
                self.update(yaml.safe_load(f))
        except yaml.ParserError as e:
            LOGGER.exception('Unable to load config file, %s', e)
            print('Unable to load configuration file', file=sys.stderr)

    def overwrite(self):
        '''
        Overwrite the config file with current contents.

        Note that this will remove the comments from the YAML file.
        '''
        with open(self.configfile, 'w', encoding='utf-8') as w:
            yaml.safe_dump(self, w)

    def validate(self):
        '''
        Ensure all keys have values
        '''
        can_be_false = ['force_unlock', 'test_mode']
        badkey = [k for k, v in self.items() if not v]
        for rm in can_be_false:
            badkey.remove(rm)#It can be false
        listkeys = {k:v for k,v in self.items() if isinstance(v, list)}
        for k, v in listkeys.items():
            for sub_v in v:
                if not sub_v:
                    badkey.append(k)
                    break
        if badkey:
            raise ValueError('Null values in configuration. '
                             f'See:\n{"\n".join([str(_) for _ in badkey])}')
