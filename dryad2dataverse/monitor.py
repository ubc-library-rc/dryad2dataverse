import sqlite3
import json
import os
from . import constants
import copy
import smtplib
from email.message import EmailMessage as Em


class Monitor(object):
    '''Singleton'''
    '''Database object and tracker'''
    ''''https://stackoverflow.com/questions/12305142/issue-with-singleton-python-call-two-times-init'''
    __instance = None
    def __new__(cls, dbase=None, *args, **kwargs):
        if cls.__instance == None:
            cls.__instance = super(Monitor, cls).__new__(cls)
            cls.__instance.__initialized = False
            #cls.dbase = kwargs.get('dbase')
            #print(f'THIS IS DBASE {cls.dbase}')
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
                      (dryaduid INTEGER references dryadStudy (uid), dvpid TEXT);',
                      'CREATE TABLE IF NOT EXISTS dvFiles \
                      (dryaduid INTEGER references dryadStudy (uid), dryfid INT, dvfid TEXT, \
                      dvfilejson TEXT);']
            for c in create:
                cls.cursor.execute(c)
            cls.conn.commit()

        return cls.__instance

    def __init__(self, dbase=None, *args, **kwargs): #remove args and kwargs when you find out how init interacts with new.
            if self.__initialized: return
            self.__initialized = True
            if not dbase:
                self.dbase = constants.DBASE
            else:
                self.dbase = dbase

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def status(self, serial):
        '''
        serial : dryad2dataverse.serializer instance
        Returns text output of 'new', 'unchanged', 'updated' or 'filesonly'
        'new' is a completely new file
        'unchanged' is no changes at all
        'updated' is changes to lastModificationDate AND metadata changes
        'filesonly' is changes to lastModificationDate only (which presumably indicates a file change.

        '''
        #Last mod date is indicator of change. From email w/Ryan Scherle 10 Nov 2020
        doi = serial.dryadJson['identifier']
        lastMod = serial.dryadJson['lastModificationDate']
        self.cursor.execute('SELECT * FROM dryadStudy WHERE doi = ?',
                            (doi,))
        result = self.cursor.fetchall()
        
        if not result:
            return {'status': 'new', 'dvpid': None}
        dvjson = json.loads(result[-1][4])
        #Check the fresh vs. updated jsons for the keys
        try:
            dryaduid = result[-1][0]
            self.cursor.execute('SELECT dvpid from dvStudy WHERE dryaduid = ?', (dryaduid,))
            dvpid = self.cursor.fetchall()[-1][0]
            serial.dvpid = dvpid
        except:
            raise 
        newfile = copy.deepcopy(serial.dryadJson)
        testfile = copy.deepcopy(json.loads(result[-1][3]))
        if newfile == testfile:
                return {'status': 'unchanged', 'dvpid': dvpid}
        del newfile['lastModificationDate']
        del testfile['lastModificationDate']
        if newfile == testfile:
            return {'status': 'filesonly', 'dvpid': dvpid}
        else:
            return {'status':'updated', 'dvpid': dvpid}

    def diff_metadata(self, serial):
        '''
        serial : dryad2dataverse.serializer.Serializer instance
        '''
        if self.status(serial)['status'] == 'updated':
            self.cursor.execute('SELECT dryadjson from dryadStudy WHERE doi = ?',
                                (serial.dryadJson['identifier'],))
            oldJson = json.loads(self.cursor.fetchall()[-1][0])
            out = []
            for k in serial.dryadJson:
                if serial.dryadJson[k] != oldJson.get(k):
                    out.append({k: (oldJson.get(k), serial.dryadJson[k])})
            return out
        else: return None 

    def diff_files(self, serial):
        '''https://docs.python.org/3/library/stdtypes.html#frozenset.symmetric_difference

        Also:
        tuple from string:
        https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string
        
        needsdel = set(a).superset(set(b))
        #returns False if all of a not in e
        if False: 
            if not set(a) - (set(a) & set(b)):
                return set(a) - (set(a) & set(b))

        needsadd = set(f).issuperset(set(a))
        if True: return set(f) - (set(f) & set(a))

        '''
        '''
        Returns a dict with additions and deletions from previous Dryad to dataverse upload
        {'add':[dyadfiletuples], 'delete:[dryadfiletuples]}
        
        serial : dryad2dataverse.serializer.Serial instance
        '''
        if self.status(serial)['status'] == 'new':
            return {}
        diffReport = {}
        self.cursor.execute('SELECT uid from dryadStudy WHERE doi = ?',
                                (serial.dryadJson['identifier'],))
        mostRecent = self.cursor.fetchall()[-1][0]
        self.cursor.execute('SELECT dryfilesjson from dryadFiles WHERE dryaduid = ?',
                                (mostRecent,))
        oldFiles = self.cursor.fetchall()[-1][0]
        if not oldFiles:
            oldFiles = [] 
        else:
            oldFiles = json.loads(oldFiles)['_embedded'].get('stash:files')
            out = []
            #comparing file tuples from dryad2dataverse.serializer. Maybe JSON is better?
            #because of code duplication below.
            for f in oldFiles:
                downLink = f['_links']['stash:file-download']['href']
                downLink = f'{constants.DRYURL}{downLink}'
                name = f['path']
                mimeType = f['mimeType']
                size = f['size']
                descr = f.get('description', '')
                out.append((downLink, name, mimeType, size, descr))
            oldFiles = out

                
        newFiles = serial.files
        ###Tests go here
        ## Can't use set on a list of dicts. Joder!
        must = set(oldFiles).issuperset(set(newFiles))
        if not must:
            needsadd= set(newFiles) - (set(oldFiles) & set(newFiles))
            diffReport.update({'add': list(needsadd)})

        must = set(newFiles).issuperset(oldFiles)
        if not must:
            needsdel = set(oldFiles) - (set(newFiles) & set(oldFiles))

            diffReport.update({'delete': list(needsdel)})
        #now how do I get the file ids of files that need to be deleted?
        return diffReport

    def get_dv_fid(self, url):
        '''
        Returns str — the Dataverse file ID. Normally used for *deletion* of dataverse files.
        url : str
            Dryad file URL in form of 'https://datadryad.org/api/v2/files/385819/download'
        '''
        fid = url[url.rfind('/',0,-10)+1:].strip('/download') 
        try:
            fid = int(fid)
        except:
            raise ValueError('File ID is not an integer')
        self.cursor.execute('SELECT dvfid FROM dvFiles WHERE dryfid = ?', (fid,))
        dvfid = self.cursor.fetchall()
        if dvfid:
            return dvfid[-1][0]
        else: return None

    def get_dv_fids(self, filelist):
        '''Returns Dataverse file IDs from a list of Dryad file tuples.
        filelist : list
            list of Dryad file tuples: eg:
            [('https://datadryad.org/api/v2/files/385819/download', 
              'GCB_ACG_Mortality_2020.zip', 
              'application/x-zip-compressed', 23787587), 
             ('https://datadryad.org/api/v2/files/385820/download', 
             'Readme_ACG_Mortality.txt', 
             'text/plain', 1350)]
            Generally, you would use the output from
            dryad2dataverse.monitor.Monitor.diff_files['delete']
        '''
        fids=[]
        for f in filelist:
            fids.append(self.get_dv_fid(f[0]))
        return fids
        #return [self.get_dv_fid(f[0]) for f in filelist]

    def update(self, transfer):
        '''
        You should call update after transfers have completed something, or you will not be adding much useful information.
        '''
        #get the pre-update dryad uid in case we need it.
        self.cursor.execute('SELECT max(uid) FROM dryadStudy WHERE doi = ?',
                            (transfer.dryad.dryadJson['identifier'],))
        olduid = self.cursor.fetchone()[0]
        if olduid:
            olduid = int(olduid)
        if self.status(transfer.dryad)['status'] != 'unchanged':
            doi = transfer.dryad.dryadJson.get('identifier')
            lastmod = transfer.dryad.dryadJson.get('lastModificationDate')
            dryadJson = json.dumps(transfer.dryad.dryadJson)
            dvJson = json.dumps(transfer.dvStudy)

            #Update study metadata
            self.cursor.execute('INSERT INTO dryadStudy (doi, lastmoddate, dryadjson, dvjson) \
                                VALUES (?, ?, ?, ?)', (doi, lastmod, dryadJson, dvJson))
            self.cursor.execute('SELECT max(uid) FROM dryadStudy WHERE doi = ?', 
                                (doi,))
            dryaduid = self.cursor.fetchone()[0]
            if type(dryaduid) != int:
                    raise

            #Update dryad file json
            self.cursor.execute('INSERT INTO dryadFiles VALUES (?, ?)',
                                (dryaduid, json.dumps(transfer.dryad.fileJson)))
            #Update dataverse study map
            self.cursor.execute('SELECT dvpid FROM dvStudy WHERE dvpid = ?', (transfer.dryad.dvpid,))
            if not self.cursor.fetchone():
                self.cursor.execute('INSERT INTO dvStudy VALUES (?, ?)', (dryaduid, transfer.dvpid))
            else:
                self.cursor.execute('UPDATE dvStudy SET dryaduid=?, dvpid=? WHERE dvpid =?', (dryaduid, transfer.dryad.dvpid, transfer.dryad.dvpid))

            #Update the files table
            #Because we want to have a *complete* file list for each dryaduid, we have to copy any existing old files, then add and delete.
            if olduid:
                self.cursor.execute('SELECT * FROM dvFiles WHERE dryaduid=?', (olduid,))
                inserter = self.cursor.fetchall()
                for rec in inserter:
                    self.cursor.execute('INSERT INTO dvFiles VALUES (?, ?, ?, ?)',
                                        (dryaduid, rec[1], rec[2], rec[3]))
            #insert newly uploaded files
            for rec in transfer.fileUpRecord:
                try:
                    dvfid = rec[1]['data']['files'][0]['dataFile']['id']#Screw you for burying the file ID this deep
                except:
                    dvfid = rec[1].get('status')
                    if dvfid == 'Failure: MAX_UPLOAD size exceeded':
                        continue
                    else:
                        dvfid='JSON read error'
                self.cursor.execute('INSERT INTO dvFiles VALUES (?, ?, ?, ?)',
                                    (dryaduid, json.dumps(rec[0]), dvfid, json.dumps(rec[1])))

            #Now the deleted files
            for rec in transfer.fileDelRecord: #fileDelRecord consists only of [fid,fid2, ...]
                self.cursor.execute('DELETE FROM dvFiles WHERE dvfid=? AND dryaduid=?',
                                    (int(rec),dryaduid))#Dryad record ID is int not str
                print(f'deleted dryfid ={rec}, dryaduid = {dryaduid}')
        self.conn.commit()

    def notify(self, user, pwd,  mailserve, port, recipients, serial):

        try:
            msg = Em()
            msg['Subject'] = f'Dryad study change notification for {serial.doi}'
            msg['From'] = user 
            msg['To'] = recipients

            content = f'Study {serial.dryadJson["title"]}/{serial.doi} \
                    has changed content. Details:\n\n\
                    Metadata changes:\n\
                    {self.diff_metadata(serial)}\n\n\
                    File changes:\n\
                    {self.diff_files(serial)}\n\n\
                    Oversize files:\n\n\
                    {serial.oversize}'
            msg.set_content(content)
            server = smtplib.SMTP(mailserv, port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pwd)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.close()
            #logging.info(f'Sent email from {USER} to {RECIPIENTS}.')
        except Exception as err:
            #logging.critical('Unable to send email message')
            #logging.exception(err)
            raise
