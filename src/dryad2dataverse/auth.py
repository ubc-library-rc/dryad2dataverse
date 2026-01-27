'''
Handles authentication and bearer tokens using
Dryad's application ID and secret
'''
import datetime
import logging
import requests
from dryad2dataverse import USERAGENT

LOGGER = logging.getLogger(__name__)

class Token:
    '''
    Self updating bearer token generator
    '''
    def __init__(self, **kwargs):
        '''
        Obtain bearer token

        Parameters
        ----------
        **kwargs
            Must include required keyword arguments as below
        dry_url : str
            Dryad base url (eg: https://datadryad.org)
        app_id : str
            Dryad application ID
        secret : str
            Application secret

        Other parameters
        ----------------
        timeout : int
            timeout in seconds

        '''
        self.kwargs = kwargs
        self.path = '/oauth/token'
        self.data = {'client_id': kwargs['app_id'],
                     'client_secret' : kwargs['secret'],
                     'grant_type': 'client_credentials'}
        self.headers = {'User-agent': USERAGENT,
                        'charset' : 'UTF-8'}
        self.timeout = kwargs.get('timeout', 100)
        self.expiry_time = None
        self.__token_info = None

    def get_bearer_token(self):
        '''
        Obtain a brand new bearer token
        '''
        try:
            tokenr = requests.post(f"{self.kwargs['dry_url']}{self.path}",
                                   headers=self.headers,
                                   data=self.data,
                                   timeout=self.timeout)
            tokenr.raise_for_status()
            self.__token_info = tokenr.json()

        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException) as err:
            LOGGER.exception('HTTP Error:, %s', err)
            raise err

    def check_token_valid(self)->bool:
        '''
        Checks to see if token is still valid
        '''
        expiry_time = (datetime.datetime.fromtimestamp(self.__token_info['created_at']) +
                       datetime.timedelta(seconds=self.__token_info['expires_in']))
        self.expiry_time = expiry_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        if datetime.datetime.now() > expiry_time:
            return False
        return True

    @property
    def token(self)->str:
        '''
        Return only a valid token
        '''
        if not self.__token_info:
            self.get_bearer_token()
        if not self.check_token_valid():
            self.get_bearer_token()
        return self.__token_info['access_token']

    @property
    def auth_header(self)->dict:
        '''
        Return valid authorization header
        '''
        return {'Accept' : 'application/json',
                'Content-Type' : 'application/json',
                'Authorization' : f'Bearer {self.token}'}
