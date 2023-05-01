'''
Bulk release script for Dataverse.

Very useful if you've just imported a bunch of Dryad studies.
'''

import argparse
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


RETRY_STRATEGY = Retry(total=10,
                       status_forcelist=[429, 500, 502, 503, 504],
                       method_whitelist=['HEAD', 'GET', 'OPTIONS',
                                         'POST', 'PUT'],
                       backoff_factor=1)

VERSION = (0, 1, 0)
__version__ = '.'.join([str(x) for x in VERSION])

def argp():
    '''
    Parses the arguments from the command line.

    Returns arparse.ArgumentParser
    '''
    description = ('Bulk file releaser for unpublished Dataverse files. Either releases individual '
                   'studies or all unreleased files in a single dataverse.')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--url', default='https://borealisdata.ca',
                        help='Dataverse base URL')
    parser.add_argument('-k', '--key', required=True,
                        help='API key')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Manually confirm each release')
    parser.add_argument('--time', '-t', help='Time between release attempts in seconds. Default 10',
                        default=10, type=int, dest='stime')
    parser.add_argument('-v', help='Verbose mode', action='store_true', dest='verbose')
    parser.add_argument('-r', '--dry-run',
                        help='Only output a list of studies to be released',
                        action='store_true', dest='dryrun')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--dv', help='Short name of Dataverse to process (eg: UBC_DRYAD)')
    group.add_argument('-p', '--pid',
                       help=('Handles or DOIs to delete in format hdl:11272.1/FK2/12345 '
                             'or doi:10.80240/FK2/NWRABI. Multiple values OK'),
                       nargs='+')
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__,
                        help='Show version number and exit')
    return parser

class Dverse():
    '''
    An object representing a Dataverse
    '''
    def __init__(self, dvurl, apikey, dvs):
        '''
        Intializes Dataverse object.

        :param dvurl: str. URL to base Dataverse (eg. 'https://dataverse.scholarsportal.info')
        :param apikey: str. API key for Dataverse
        :param dv: str. Short name of target dataverse (eg. 'UBC_DRYAD')
        '''
        self.dvurl = dvurl.strip('/')
        self.apikey = apikey
        self.dvs = dvs
        self.hdl = None
        self.sess = requests.Session()
        self.sess.mount('https://', HTTPAdapter(max_retries=RETRY_STRATEGY))
        self.protocol = None

    @property
    def study_list(self) -> list:
        '''
        Returns a list of all studies (published or not) in the dataverse
        '''
        slist = self.sess.get(f'{self.dvurl}/api/dataverses/{self.dvs}/contents',
                              headers={'X-Dataverse-key':self.apikey})
        data = slist.json()['data']
        self.hdl = data[-1]['protocol']
        return [x['storageIdentifier'].replace('file://', f'{self.hdl}:') for x in data
                if x['type'] == 'dataset']

    @property
    def unreleased(self, all_stud: list = None) -> list:
        '''
        Finds only unreleased studies from a list of studies
        :param all_stud: list. List of Dataverse studies. Defaults to output of
                   Dverse.get_study_list()
        '''
        if not all_stud:
            all_stud = self.study_list
        unreleased = []
        for stud in all_stud:
            data = self.sess.get(f'{self.dvurl}/api/datasets/:persistentId/versions',
                                 params={'persistentId':stud},
                                 headers={'X-Dataverse-key':self.apikey})
            most_recent = data.json()['data'][-1]
            if most_recent['versionState'] == 'DRAFT':
                unreleased.append(most_recent['datasetPersistentId'])
        return unreleased

class Study():
    '''Instance representing a Dataverse study'''
    def __init__(self, **kwargs):
        '''
        :kwarg dvurl: str. Base URL for Dataverse instance
        :kwarg apikey: str. API key for Dataverse instance
        :kwarg pid: str. Persistent identifier for study
        :kwarg stime: int. Time between file lock checks. Default 10
        :kwarg verbose: Verbose output. Default False
        '''
        #super().__init__(kwargs['dvurl'], kwargs['apikey'], kwargs['dv'])

        self.dvurl = kwargs.get('dvurl')
        self.apikey = kwargs.get('apikey')
        self.pid = kwargs.get('pid')
        self.stime = kwargs.get('stime', 10)
        self.verbose = kwargs.get('verbose', False)
        self.sess = requests.Session()
        self.sess.mount('https://', HTTPAdapter(max_retries=RETRY_STRATEGY))
        self.status = None

    def status_ok(self):
        '''
        Checks to see if study has a lock. Returns True if OK to continue, else False.
        
        '''
        if self.verbose:
            print(f'Validating no lock status for {self.pid}')

        lock = self.sess.get(f'{self.dvurl}/api/datasets/:persistentId/locks',
                             params={'persistentId':self.pid},
                             headers={'X-Dataverse-key':self.apikey})
        if self.verbose:
            lock_stat = lock.json()['data']
            if lock_stat:
                print(f'Lock status for {self.pid}: {lock.json()["data"]}')
            else:
                print('No study locks')
        if not lock.json()['data']:
            return True
        return False

    def release_me(self, interactive=False):
        '''
        Releases study and waits until it's unlocked before returning to the function

        :params interactive: bool. Manually confirm each release
        '''
        if interactive:
            relme = input(f'Release {self.pid} (y/n)? ')
            if relme.lower().strip() != 'y':
                return

        release = self.sess.post(f'{self.dvurl}/api/datasets/:persistentId/actions/:publish',
                                 params={'persistentId':self.pid, 'type':'major'},
                                 headers={'X-Dataverse-key': self.apikey})
        self.status = release.json()

        if self.verbose:
            print(f'Releasing {self.pid}')
            print(self.status['status'])
            if self.status['status'] != 'OK':
                print(self.status['message'])
        while not self.status_ok():
            time.sleep(self.stime)
        if self.verbose:
            print(f'Released: {self.dvurl}/dataset.xhtml?persistentId={self.pid}')

def main():
    '''
    The primary function. Will release all unreleased studies in the
    the target dataverse, or selected studies as required.
    '''
    parser = argp()
    args = parser.parse_args()
    #print(args)
    if args.dv:
        the_dv = Dverse(args.url, args.key, args.dv)
        un_rel = the_dv.unreleased
    else:
        un_rel = args.pid
    if args.dryrun:
        for stud in un_rel:
            print(f'{args.url.strip("/")}/dataset.xhtml?persistentId={stud}&version=DRAFT')
        return
    for stud in un_rel:
        studobj = Study(pid=stud, dvurl=args.url,
                        apikey=args.key,
                        verbose=args.verbose)
        studobj.release_me(args.interactive)
        if stud != un_rel[-1]:
            time.sleep(args.stime)

if __name__ == '__main__':
    main()
