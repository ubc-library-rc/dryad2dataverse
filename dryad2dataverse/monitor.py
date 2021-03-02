'''
Dryad/Dataverse status tracker. Monitor creates a singleton object which
writes to a SQLite database. Methods will (generally) take either a
dryad2dataverse.serializer.Serializer instance or
dryad2dataverse.transfer.Transfer instance

The monitor's primary function is to allow for state checking
for Dryad studies so that files and studies aren't downloaded
unneccessarily.
'''

import copy
import logging
import json
import sqlite3
import datetime

from dryad2dataverse import constants
from dryad2dataverse import exceptions

LOGGER = logging.getLogger(__name__)

class Monitor():
    '''
    The Monitor object is a tracker and database updater, so that
    Dryad files can be monitored and updated over time. Monitor is a singleton,
    but is not thread-safe.
    '''
    __instance = None

    def __new__(cls, dbase=None, *args, **kwargs):
        '''
        Creates a new singleton instance of Monitor

        Also creates a database if existing database is not present

        ----------------------------------------
        Parameters:

        dbase : str
            Path to sqlite3 database.
            /path/to/file.sqlite3
        ----------------------------------------
        '''
        if cls.__instance is None:
            cls.__instance = super(Monitor, cls).__new__(cls)
            cls.__instance.__initialized = False
            cls.dbase = dbase
            if not cls.dbase:
                cls.dbase = constants.DBASE
            cls.conn = sqlite3.Connection(cls.dbase)
            cls.cursor = cls.conn.cursor()
            create = ['CREATE TABLE IF NOT EXISTS dryadStudy \
                      (uid INTEGER PRIMARY KEY AUTOINCREMENT, \
                      doi TEXT, lastmoddate TEXT, dryadjson TEXT, \
                      dvjson TEXT);',
                      'CREATE TABLE IF NOT EXISTS dryadFiles \
                      (dryaduid INTEGER REFERENCES dryadStudy (uid), \
                      dryfilesjson TEXT);',
                      'CREATE TABLE IF NOT EXISTS dvStudy \
                      (dryaduid INTEGER references dryadStudy (uid), \
                      dvpid TEXT);',
                      'CREATE TABLE IF NOT EXISTS dvFiles \
                      (dryaduid INTEGER references dryadStudy (uid), \
                      dryfid INT, \
                      drymd5 TEXT, dvfid TEXT, dvmd5 TEXT, \
                      dvfilejson TEXT);',
                      'CREATE TABLE IF NOT EXISTS lastcheck \
                      (checkdate TEXT);']
            for line in create:
                cls.cursor.execute(line)
            cls.conn.commit()
            LOGGER.info('Using database %s', cls.dbase)

        return cls.__instance

    def __init__(self, dbase=None, *args, **kwargs):
        # remove args and kwargs when you find out how init interacts with new.
        '''
        Initialize the Monitor instance if not instantiated already (ie, Monitor
        is a singleton.)

        ----------------------------------------
        Parameters:

        dbase : str
            Complete path to desired location of tracking database
            (eg: /tmp/test.db)

            Defaults to dryad2dataverse.constants.DBASE
        ----------------------------------------
        '''
        if self.__initialized:
            return
        self.__initialized = True
        if not dbase:
            self.dbase = constants.DBASE
        else:
            self.dbase = dbase


    def __del__(self):
        '''
        Commits all database transactions on object deletion and closes database.
        '''
        self.conn.commit()
        self.conn.close()

    @property
    def lastmod(self):
        '''
        Returns last modification date from monitor.dbase
        '''
        self.cursor.execute('SELECT checkdate FROM lastcheck ORDER BY rowid DESC;')
        last_mod = self.cursor.fetchall()
        if last_mod:
            return last_mod[0][0]
        return None

    def status(self, serial):
        '''
        Returns a dictionary with keys 'status' and 'dvpid' where
            status: one of 'new', 'unchanged', 'updated' or 'filesonly'

                'new' is a completely new file
                'unchanged' is no changes at all
                'updated' is changes to lastModificationDate AND metadata changes
                'filesonly' is changes to lastModificationDate only
                (which presumably indicates a file change.

            dvpid: dataverse persistent identifier.
            None in the case of status='new'

        ----------------------------------------
        Parameters:

        serial : dryad2dataverse.serializerinstance
        ----------------------------------------
        '''
        # Last mod date is indicator of change.
        # From email w/Ryan Scherle 10 Nov 2020
        doi = serial.dryadJson['identifier']
        # lastMod = serial.dryadJson['lastModificationDate']
        self.cursor.execute('SELECT * FROM dryadStudy WHERE doi = ?',
                            (doi,))
        result = self.cursor.fetchall()

        if not result:
            return {'status': 'new', 'dvpid': None}
        # dvjson = json.loads(result[-1][4])
        # Check the fresh vs. updated jsons for the keys
        try:
            dryaduid = result[-1][0]
            self.cursor.execute('SELECT dvpid from dvStudy WHERE \
                                 dryaduid = ?', (dryaduid,))
            dvpid = self.cursor.fetchall()[-1][0]
            serial.dvpid = dvpid
        except TypeError:
            try:
                raise exceptions.DatabaseError
            except exceptions.DatabaseError as e:
                LOGGER.error('Dryad DOI : %s. Error finding Dataverse PID', doi)
                LOGGER.exception(e)
                raise

        newfile = copy.deepcopy(serial.dryadJson)
        testfile = copy.deepcopy(json.loads(result[-1][3]))
        if newfile == testfile:
            return {'status': 'unchanged', 'dvpid': dvpid}
        del newfile['lastModificationDate']
        del testfile['lastModificationDate']
        if newfile == testfile:
            return {'status': 'filesonly', 'dvpid': dvpid}
        return {'status': 'updated', 'dvpid': dvpid}

    def diff_metadata(self, serial):
        '''
        Analyzes differences in metadata between current serializer
        instance and last updated serializer instance.
        Returns a list of field changes consisting of

        [{key: (old_value, new_value}] or None if no changes

        For example:

        [{'title':
        ('Cascading effects of algal warming in a freshwater community',
         'Cascading effects of algal warming in a freshwater community theatre')}
        ]

        ----------------------------------------
        Parameters:

        serial : dryad2dataverse.serializer.Serializer instance
        ----------------------------------------
        '''
        if self.status(serial)['status'] == 'updated':
            self.cursor.execute('SELECT dryadjson from dryadStudy \
                                 WHERE doi = ?',
                                (serial.dryadJson['identifier'],))
            oldJson = json.loads(self.cursor.fetchall()[-1][0])
            out = []
            for k in serial.dryadJson:
                if serial.dryadJson[k] != oldJson.get(k):
                    out.append({k: (oldJson.get(k), serial.dryadJson[k])})
            return out

        return None

    def diff_files(self, serial):
        '''
        Returns a dict with additions and deletions from previous Dryad
        to dataverse upload

        Because checksums are not necessarily included in Dryad file
        metadata, this method uses dryad file IDs, size, or
        whatever is available.

        If dryad2dataverse.monitor.Monitor.status()
        indicates a change it will produce dictionary output with a list
        of additions or deletions, as below:

        {'add':[dyadfiletuples], 'delete:[dryadfiletuples]}

        ----------------------------------------
        Parameters:

        serial : dryad2dataverse.serializer.Serializer instance
        ----------------------------------------
        '''

        diffReport = {}
        if self.status(serial)['status'] == 'new':
            return {}
        self.cursor.execute('SELECT uid from dryadStudy WHERE doi = ?',
                            (serial.doi,))
        mostRecent = self.cursor.fetchall()[-1][0]
        self.cursor.execute('SELECT dryfilesjson from dryadFiles WHERE \
                             dryaduid = ?', (mostRecent,))
        oldFileList = self.cursor.fetchall()[-1][0]
        if not oldFileList:
            oldFileList = []
        else:
            out = []
            #With Dryad API change, files are paginated
            #now stored as list
            for old in json.loads(oldFileList):
            #for old in oldFileList:
                oldFiles = old['_embedded'].get('stash:files')
                # comparing file tuples from dryad2dataverse.serializer.
                # Maybe JSON is better?
                # because of code duplication below.
                for f in oldFiles:
                    downLink = f['_links']['stash:file-download']['href']
                    downLink = f'{constants.DRYURL}{downLink}'
                    name = f['path']
                    mimeType = f['mimeType']
                    size = f['size']
                    descr = f.get('description', '')
                    md5 = f.get('md5', '')
                    out.append((downLink, name, mimeType, size, descr, md5))
                oldFiles = out

        newFiles = serial.files
        # Tests go here
        # Can't use set on a list of dicts. Joder!
        must = set(oldFiles).issuperset(set(newFiles))
        if not must:
            needsadd = set(newFiles) - (set(oldFiles) & set(newFiles))
            diffReport.update({'add': list(needsadd)})

        must = set(newFiles).issuperset(oldFiles)
        if not must:
            needsdel = set(oldFiles) - (set(newFiles) & set(oldFiles))

            diffReport.update({'delete': list(needsdel)})
        return diffReport

    def get_dv_fid(self, url):
        '''
        Returns str — the Dataverse file ID from parsing a Dryad
        file download link.  Normally used for determining dataverse
        file ids for *deletion* in case of dryad file changes.

        ----------------------------------------
        Parameters:

        url : str
            *Dryad* file URL in form of
            'https://datadryad.org/api/v2/files/385819/download'
        ----------------------------------------
        '''
        fid = url[url.rfind('/', 0, -10)+1:].strip('/download')
        try:
            fid = int(fid)
        except ValueError as e:
            LOGGER.error('File ID %s is not an integer', fid)
            LOGGER.exception(e)
            raise

        self.cursor.execute('SELECT dvfid FROM dvFiles WHERE \
                             dryfid = ?', (fid,))
        dvfid = self.cursor.fetchall()
        if dvfid:
            return dvfid[-1][0]
        return None

    def get_dv_fids(self, filelist):
        '''
        Returns Dataverse file IDs from a list of Dryad file tuples.
        Generally, you would use the output from
        dryad2dataverse.monitor.Monitor.diff_files['delete']
        to discover Dataverse file ids for deletion.

        ----------------------------------------
        Parameters:

        filelist : list
            list of Dryad file tuples: eg:
            [('https://datadryad.org/api/v2/files/385819/download',
              'GCB_ACG_Mortality_2020.zip',
              'application/x-zip-compressed', 23787587),
             ('https://datadryad.org/api/v2/files/385820/download',
             'Readme_ACG_Mortality.txt',
             'text/plain', 1350)]
        ----------------------------------------
        '''
        fids = []
        for f in filelist:
            fids.append(self.get_dv_fid(f[0]))
        return fids
        # return [self.get_dv_fid(f[0]) for f in filelist]

    def get_json_dvfids(self, serial):
        '''
        Return a list of Dataverse file ids for dryad JSONs which were
        uploaded to Dataverse.
        Normally used to discover the file IDs to remove Dryad JSONs
        which have changed.

        ----------------------------------------
        Parameters:

        serial : dryad2dataverse.serializer.Serializer instance
        ----------------------------------------
        '''
        self.cursor.execute('SELECT max(uid) FROM dryadStudy WHERE doi=?',
                            (serial.doi,))
        try:
            uid = self.cursor.fetchone()[0]
            self.cursor.execute('SELECT dvfid FROM dvFiles WHERE \
                                 dryaduid = ? AND dryfid=?', (uid, 0))
            jsonfid = [f[0] for f in self.cursor.fetchall()]
            return jsonfid

        except TypeError:
            return []

    def update(self, transfer):
        '''
        Updates the Monitor database with information from a
        dryad2dataverse.transfer.Transfer instance

        If a Dryad primary metadata record has changes, it will be
        deleted from the database.

        This method should be called after all transfers are completed,
        including Dryad JSON updates, as the last action for transfer.

        ----------------------------------------
        Parameters:

        transfer : dryad2dataverse.transfer.Transfer instance
        ----------------------------------------
        '''
        # get the pre-update dryad uid in case we need it.
        self.cursor.execute('SELECT max(uid) FROM dryadStudy WHERE doi = ?',
                            (transfer.dryad.dryadJson['identifier'],))
        olduid = self.cursor.fetchone()[0]
        if olduid:
            olduid = int(olduid)
        if self.status(transfer.dryad)['status'] != 'unchanged':
            doi = transfer.doi
            lastmod = transfer.dryad.dryadJson.get('lastModificationDate')
            dryadJson = json.dumps(transfer.dryad.dryadJson)
            dvJson = json.dumps(transfer.dvStudy)

            # Update study metadata
            self.cursor.execute('INSERT INTO dryadStudy \
                                 (doi, lastmoddate, dryadjson, dvjson) \
                                 VALUES (?, ?, ?, ?)',
                                (doi, lastmod, dryadJson, dvJson))
            self.cursor.execute('SELECT max(uid) FROM dryadStudy WHERE \
                                 doi = ?', (doi,))
            dryaduid = self.cursor.fetchone()[0]
            #if type(dryaduid) != int:
            if not isinstance(dryaduid, int):
                try:
                    raise TypeError('Dryad UID is not an integer')
                except TypeError as e:
                    LOGGER.error(e)
                    raise

            # Update dryad file json
            self.cursor.execute('INSERT INTO dryadFiles VALUES (?, ?)',
                                (dryaduid,
                                 json.dumps(transfer.dryad.fileJson)))
            # Update dataverse study map
            self.cursor.execute('SELECT dvpid FROM dvStudy WHERE \
                                 dvpid = ?', (transfer.dryad.dvpid,))
            if not self.cursor.fetchone():
                self.cursor.execute('INSERT INTO dvStudy VALUES (?, ?)',
                                    (dryaduid, transfer.dvpid))
            else:
                self.cursor.execute('UPDATE dvStudy SET dryaduid=?, \
                                     dvpid=? WHERE dvpid =?',
                                    (dryaduid, transfer.dryad.dvpid,
                                     transfer.dryad.dvpid))

            # Update the files table
            # Because we want to have a *complete* file list for each
            # dryaduid, we have to copy any existing old files,
            # then add and delete.
            if olduid:
                self.cursor.execute('SELECT * FROM dvFiles WHERE \
                                     dryaduid=?', (olduid,))
                inserter = self.cursor.fetchall()
                for rec in inserter:
                    # TODONE FIX THIS #I think it's fixed 11 Feb 21
                    self.cursor.execute('INSERT INTO dvFiles VALUES \
                                         (?, ?, ?, ?, ?, ?)',
                                        (dryaduid, rec[1], rec[2],
                                         rec[3], rec[4], rec[5]))
            # insert newly uploaded files
            for rec in transfer.fileUpRecord:
                try:
                    dvfid = rec[1]['data']['files'][0]['dataFile']['id']
                    # Screw you for burying the file ID this deep
                except (KeyError, IndexError) as err:
                    dvfid = rec[1].get('status')
                    if dvfid == 'Failure: MAX_UPLOAD size exceeded':
                        LOGGER.warning('Monitor: max upload size of %s exceeded. '
                                       'Unable to get dataverse file ID',
                                       constants.MAX_UPLOAD)
                        LOGGER.warning('Error:\n$%s', err)
                        continue
                    else:
                        dvfid = 'JSON read error'
                        LOGGER.warning('JSON read error')
                recMd5 = rec[1]['data']['files'][0]['dataFile']['checksum']['value']
                # md5s verified during upload step, so they should
                # match already
                self.cursor.execute('INSERT INTO dvFiles VALUES \
                                     (?, ?, ?, ?, ?, ?)',
                                    (dryaduid, rec[0], recMd5,
                                     dvfid, recMd5, json.dumps(rec[1])))

            # Now the deleted files
            for rec in transfer.fileDelRecord:
                # fileDelRecord consists only of [fid,fid2, ...]
                # Dryad record ID is int not str
                self.cursor.execute('DELETE FROM dvFiles WHERE dvfid=? \
                                     AND dryaduid=?',
                                    (int(rec), dryaduid))
                LOGGER.debug('deleted dryfid = %s, dryaduid = %s', rec, dryaduid)

            # And lastly, any JSON metadata updates:
            # NOW WHAT?
            # JSON has dryfid==0
            self.cursor.execute('SELECT * FROM dvfiles WHERE \
                                 dryfid=? and dryaduid=?',
                                (0, dryaduid))
            try:
                exists = self.cursor.fetchone()[0]
                # Old metadata must be deleted on a change.
                if exists:
                    shouldDel = self.status(transfer.dryad)['status']
                    if shouldDel == 'updated':
                        self.cursor.execute('DELETE FROM dvfiles WHERE \
                                             dryfid=? and dryaduid=?',
                                            (0, dryaduid))
            except TypeError:
                pass

            if transfer.jsonFlag:
                # update dryad JSON
                djson5 = transfer.jsonFlag[1]['data']['files'][0]['dataFile']['checksum']['value']
                dfid = transfer.jsonFlag[1]['data']['files'][0]['dataFile']['id']
                self.cursor.execute('INSERT INTO dvfiles VALUES \
                                     (?, ?, ?, ?, ?, ?)',
                                    (dryaduid, 0, djson5, dfid,
                                     djson5, json.dumps(transfer.jsonFlag[1])))

        self.conn.commit()

    def set_timestamp(self, curdate=None):
        '''
        Adds current time to the database table. Can be queried and be used
        for subsequent checking for updates. To query last modification time,
        use the dataverse2dryad.monitor.Monitor.lastmod attribute.

        ----------------------------------------
        Parameters:

        curdate : str
            UTC datetime string in the format suitable for the Dryad API.
            eg. 2021-01-21T21:42:40Z
            or .strftime('%Y-%m-%dT%H:%M:%SZ')
        ----------------------------------------
        '''
        #Dryad API uses Zulu time
        if not curdate:
            curdate = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.cursor.execute('INSERT INTO lastcheck VALUES (?)',
                            (curdate,))
        self.conn.commit()
