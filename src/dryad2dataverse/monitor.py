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
        Creates a new singleton instance of Monitor.

        Also creates a database if existing database is not present.

        ----------------------------------------
        Parameters:

        dbase : str
            — Path to sqlite3 database. That is:
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
                      (checkdate TEXT);',
                      'CREATE TABLE IF NOT EXISTS failed_uploads \
                      (dryaduid INTEGER references dryadstudy (uid), \
                      dryfid INT, status TEXT);'
                      ]

            for line in create:
                cls.cursor.execute(line)
            cls.conn.commit()
            LOGGER.info('Using database %s', cls.dbase)

        return cls.__instance

    def __init__(self, dbase=None, *args, **kwargs):
        # remove args and kwargs when you find out how init interacts with new.
        '''
        Initialize the Monitor instance if not instantiated already (ie, Monitor
        is a singleton).

        ----------------------------------------
        Parameters:

        dbase : str
            — Complete path to desired location of tracking database
              (eg: /tmp/test.db).

            Defaults to dryad2dataverse.constants.DBASE.
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
        Returns last modification date from monitor.dbase.
        '''
        self.cursor.execute('SELECT checkdate FROM lastcheck ORDER BY rowid DESC;')
        last_mod = self.cursor.fetchall()
        if last_mod:
            return last_mod[0][0]
        return None

    def status(self, serial):
        '''
        Returns a dictionary with keys 'status' and 'dvpid' and 'notes'.
        `{status :'updated', 'dvpid':'doi://some/ident'}`.

        `status` is one of 'new', 'identical',  'lastmodsame',
        'updated'

                'new' is a completely new file.

                'identical' The metadata from Dryad is *identical* to the last time
                the check was run.

                'lastmodsame' Dryad lastModificationDate ==  last modification date
                in database AND output JSON is different.
                This can indicate a Dryad
                API output change, reindexing or something else.
                But the lastModificationDate
                is supposed to be an indicator of meaningful change, so this option
                exists so you can decide what to do given this option

                'updated' Indicates changes to lastModificationDate

                Note that Dryad constantly changes their API output, so the changes
                may not actually be meaningful.

        `dvpid` is a Dataverse persistent identifier.
        `None` in the case of status='new'

        `notes`: value of Dryad versionChanges field. One of `files_changed` or
        `metatdata_changed`. Non-null value present only when status is
        not `new` or `identical`. Note that Dryad has no way to indicate *both*
        a file and metadata change, so this value reflects only the *last* change
        in the Dryad state.

        ----------------------------------------
        Parameters:

        serial : dryad2dataverse.serializer instance
        ----------------------------------------
        '''
        # Last mod date is indicator of change.
        # From email w/Ryan Scherle 10 Nov 2020
        #The versionNumber updates for either a metadata change or a
        #file change. Although we save all of these changes internally, our web
        #interface only displays the versions that have file changes, along
        #with the most recent metadata. So a dataset that has only two versions
        #of files listed on the web may actually have several more versions in
        #the API.
        #
        #If your only need is to track when there are changes to a
        #dataset, you may want to use the `lastModificationDate`, which we have
        #recently added to our metadata.
        #
        #Note that the Dryad API output ISN'T STABLE; they add fields etc.
        #This means that a comparison of JSON may yield differences even though
        #metadata is technically "the same". Just comparing two dicts doesn't cut
        #it.
        #############################
        ## Note: by inspection, Dryad outputs JSON that is different
        ## EVEN IF lastModificationDate is unchanged. (14 January 2022)
        ## So now what?
        #############################
        doi = serial.dryadJson['identifier']
        self.cursor.execute('SELECT * FROM dryadStudy WHERE doi = ?',
                            (doi,))
        result = self.cursor.fetchall()

        if not result:
            return {'status': 'new', 'dvpid': None, 'notes': ''}
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
            return {'status': 'identical', 'dvpid': dvpid, 'notes': ''}
        if newfile['lastModificationDate'] != testfile['lastModificationDate']:
            return {'status': 'updated', 'dvpid': dvpid,
                    'notes': newfile['versionChanges']}
        return {'status': 'lastmodsame', 'dvpid': dvpid,
                     'notes': newfile.get('versionChanges')}

    def diff_metadata(self, serial):
        '''
        Analyzes differences in metadata between current serializer
        instance and last updated serializer instance.
        Returns a list of field changes consisting of:

        [{key: (old_value, new_value}] or None if no changes.

        For example:

        ```
        [{'title':
        ('Cascading effects of algal warming in a freshwater community',
         'Cascading effects of algal warming in a freshwater community theatre')}
        ]
        ```
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

    @staticmethod
    def __added_hashes(oldFiles, newFiles):
        '''
        Checks that two objects in dryad2dataverse.serializer.files format
        stripped of digestType and digest values are identical. Returns array
        of files with changed hash.

        Assumes name, mimeType, size, descr all unchanged, which is not
        necessarily a valid assumption

        oldFiles: list or tuple:
            (name, mimeType, size, descr, digestType, digest)

        newFiles: list or tuple:
            (name, mimeType, size, descr, digestType, digest)
        '''
        hash_change = []
        old = [x[1:-2] for x in oldFiles]
        #URLs are not permanent
        old_no_url = [x[1:] for x in oldFiles]
        for fi in newFiles:
            if fi[1:-2] in old and fi[1:] not in old_no_url:
                hash_change.append(fi)
        return hash_change


    def diff_files(self, serial):
        '''
        Returns a dict with additions and deletions from previous Dryad
        to dataverse upload.

        Because checksums are not necessarily included in Dryad file
        metadata, this method uses dryad file IDs, size, or
        whatever is available.

        If dryad2dataverse.monitor.Monitor.status()
        indicates a change it will produce dictionary output with a list
        of additions, deletions or hash changes (ie, identical
        except for hash changes), as below:

        `{'add':[dyadfiletuples], 'delete:[dryadfiletuples],
          'hash_change': [dryadfiletuples]}`

        ----------------------------------------
        Parameters:

        serial : dryad2dataverse.serializer.Serializer instance
        ----------------------------------------
        '''
        diffReport = {}
        if self.status(serial)['status'] == 'new':
            #do we want to show what needs to be added?
            return {'add': serial.files}
            #return {}
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
                    #Download links are not persistent. Be warned
                    downLink = f['_links']['stash:file-download']['href']
                    downLink = f'{constants.DRYURL}{downLink}'
                    name = f['path']
                    mimeType = f['mimeType']
                    size = f['size']
                    descr = f.get('description', '')
                    digestType = f.get('digestType', '')
                    digest = f.get('digest', '')
                    out.append((downLink, name, mimeType, size, descr, digestType, digest))
                oldFiles = out
        newFiles = serial.files[:]
        # Tests go here
        #Check for identity first
        #if returned here there are definitely no changes
        if (set(oldFiles).issuperset(set(newFiles)) and
                set(newFiles).issuperset(oldFiles)):
            return diffReport
        #filenames for checking hash changes.
        #Can't use URL or hashes for comparisons because they can change
        #without warning, despite the fact that the API says that
        #file IDs are unique. They aren't. Verified by Ryan Scherle at
        #Dryad December 2021
        old_map = {x:{'orig':y, 'no_hash':y[1:4]} for x,y in enumerate(oldFiles)}
        new_map = {x:{'orig':y, 'no_hash':y[1:4]} for x,y in enumerate(newFiles)}
        old_no_hash = [old_map[x]['no_hash'] for x in old_map]
        new_no_hash = [new_map[x]['no_hash'] for x in new_map]

        #check for added hash only
        hash_change = Monitor.__added_hashes(oldFiles, newFiles)

        must = set(old_no_hash).issuperset(set(new_no_hash))
        if not must:
            needsadd = set(new_no_hash) - (set(old_no_hash) & set(new_no_hash))
            #Use the map created above to return the full file info
            diffReport.update({'add': [new_map[new_no_hash.index(x)]['orig']
                                       for x in needsadd]})
        must = set(new_no_hash).issuperset(old_no_hash)
        if not must:
            needsdel = set(old_no_hash) - (set(new_no_hash) & set(old_no_hash))
            diffReport.update({'delete' : [old_map[old_no_hash.index(x)]['orig']
                                           for x in needsdel]})
        if hash_change:
            diffReport.update({'hash_change': hash_change})
        return diffReport

    def get_dv_fid(self, url):
        '''
        Returns str — the Dataverse file ID from parsing a Dryad
        file download link.  Normally used for determining dataverse
        file ids for *deletion* in case of dryad file changes.

        ----------------------------------------
        Parameters:

        url : str
            — *Dryad* file URL in form of
              'https://datadryad.org/api/v2/files/385819/download'.
        ----------------------------------------
        '''
        fid = url[url.rfind('/', 0, -10)+1:].strip('/download')
        try:
            fid = int(fid)
        except ValueError as e:
            LOGGER.error('File ID %s is not an integer', fid)
            LOGGER.exception(e)
            raise

        #File IDs are *CHANGEABLE* according to Dryad, Dec 2021
        #SQLite default returns are by ROWID ASC, so the last record
        #returned should still be the correct, ie. most recent, one.
        #However, just in case, this is now done explicitly.
        self.cursor.execute('SELECT dvfid, ROWID FROM dvFiles WHERE \
                             dryfid = ? ORDER BY ROWID ASC;', (fid,))
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
            — List of Dryad file tuples: eg:

            ```
            [('https://datadryad.org/api/v2/files/385819/download',
              'GCB_ACG_Mortality_2020.zip',
              'application/x-zip-compressed', 23787587),
             ('https://datadryad.org/api/v2/files/385820/download',
             'Readme_ACG_Mortality.txt',
             'text/plain', 1350)]
             ```
        ----------------------------------------
        '''
        fids = []
        for f in filelist:
            fids.append(self.get_dv_fid(f[0]))
        return fids
        # return [self.get_dv_fid(f[0]) for f in filelist]

    def get_json_dvfids(self, serial):
        '''
        Return a list of Dataverse file ids for Dryad JSONs which were
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
        dryad2dataverse.transfer.Transfer instance.

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
                                    (dryaduid, transfer.dryad.dvpid))
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
                    recMd5 = rec[1]['data']['files'][0]['dataFile']['checksum']['value']
                except (KeyError, IndexError) as err:
                    #write to failed uploads table instead
                    status = rec[1].get('status')
                    if not status:
                        LOGGER.error('JSON read error for Dryad file ID %s', rec[0])
                        LOGGER.error('File %s for DOI %s may not be uploaded', rec[0], transfer.doi)
                        LOGGER.exception(err)
                        msg = {'status': 'Failure: Other non-specific '
                                         'failure. Check logs'}

                        self.cursor.execute('INSERT INTO failed_uploads VALUES \
                                        (?, ?, ?);', (dryaduid, rec[0], json.dumps(msg)))
                        continue
                    self.cursor.execute('INSERT INTO failed_uploads VALUES \
                                        (?, ?, ?);', (dryaduid, rec[0], json.dumps(rec[1])))
                    LOGGER.warning(type(err))
                    LOGGER.warning('%s. DOI %s, File ID %s',
                                   rec[1].get('status'),
                                   transfer.doi, rec[0])
                    continue
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
            — UTC datetime string in the format suitable for the Dryad API.
              eg. 2021-01-21T21:42:40Z
              or .strftime('%Y-%m-%dT%H:%M:%SZ').
        ----------------------------------------
        '''
        #Dryad API uses Zulu time
        if not curdate:
            curdate = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.cursor.execute('INSERT INTO lastcheck VALUES (?)',
                            (curdate,))
        self.conn.commit()
