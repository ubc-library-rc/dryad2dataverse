'''
This module handles data downloads and uploads from a Dryad instance to a Dataverse instance
'''

import hashlib
import io
import json
import logging
import os
import time
import traceback

import requests
from requests.adapters import HTTPAdapter
from requests_toolbelt.multipart.encoder import MultipartEncoder

from dryad2dataverse import constants
from dryad2dataverse import exceptions

LOGGER = logging.getLogger(__name__)
URL_LOGGER = logging.getLogger('urllib3')

class Transfer():
    '''
    Transfers metadata and data files from a
    Dryad installation to Dataverse installation.
    '''
    def __init__(self, dryad):
        '''
        Creates a dryad2dataverse.transfer.Transfer instance.

        ----------------------------------------
        Parameters:
            dryad : dryad2dataverse.serializer.Serializer instance
        ----------------------------------------
        '''
        self.dryad = dryad
        self._fileJson = None
        self._files = [list(f) for f in self.dryad.files]
        #self._files = copy.deepcopy(self.dryad.files)
        self.fileUpRecord = []
        self.fileDelRecord = []
        self.dvStudy = None
        self.jsonFlag = None #Whether or not new json uploaded
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=constants.RETRY_STRATEGY))

    def _del__(self): #TODONE: Change name to __del__ to make a destructor
        '''Expunges files from constants.TMP on deletion'''
        for f in self.files:
            if os.path.exists(f'{constants.TMP}{os.sep}{f[1]}'):
                os.remove(f'{constants.TMP}{os.sep}{f[1]}')

    def test_api_key(self, url=None, apikey=None):
        '''
        Tests for an expired API key and raises
        dryad2dataverse.exceptions.Dryad2dataverseBadApiKeyError
        the API key is bad. Ignores other HTTP errors.

        ----------------------------------------
        Parameters:

        url : str
            — Base URL to Dataverse installation.
              Defaults to dryad2dataverse.constants.DVURL

        apikey : str
            — Default dryad2dataverse.constants.APIKEY.

        ----------------------------------------
        '''
        #API validity check appears to come before a PID validity check
        params = {'persistentId': 'doi:000/000/000'} # PID is irrelevant
        if not url:
            url = constants.DVURL
        headers = {'X-Dataverse-key': apikey if apikey else constants.APIKEY}
        bad_test = self.session.get(f'{url}/api/datasets/:persistentId',
                                headers=headers,
                                params=params)
        #There's an extra space in the message which Harvard
        #will probably find out about, so . . .
        if bad_test.json().get('message').startswith('Bad api key'):
            try:
                raise exceptions.DataverseBadApiKeyError('Bad API key')
            except exceptions.DataverseBadApiKeyError as e:
                LOGGER.critical('API key has expired or is otherwise invalid')
                LOGGER.exception(e)
                #LOGGER.exception(traceback.format_exc()) #not really necessary
                raise
        try: #other errors
            bad_test.raise_for_status()
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            LOGGER.exception(e)
            LOGGER.exception(traceback.format_exc())
            raise

    @property
    def dvpid(self):
        '''
        Returns Dataverse study persistent ID as str.
        '''
        return self.dryad.dvpid

    @property
    def auth(self):
        '''
        Returns datavese authentication header dict.
        ie: `{X-Dataverse-key' : 'APIKEYSTRING'}`
        '''
        return {'X-Dataverse-key' : constants.APIKEY}

    @property
    def fileJson(self):
        '''
        Returns a list of file JSONs from call to Dryad API /files/{id},
        where the ID is parsed from the Dryad JSON. Dryad file listings
        are paginated.
        '''
        return self.dryad.fileJson.copy()

    @property
    def files(self):
        '''
        Returns a list of lists with:

        [Download_location, filename, mimetype, size, description, md5digest]

        This is mutable; downloading a file will add md5 info if not available.
        '''
        return self._files

    @property
    def oversize(self):
        '''
        Returns list of files exceeding Dataverse ingest limit
        dryad2dataverse.constants.MAX_UPLOAD.
        '''
        return self.dryad.oversize

    @property
    def doi(self):
        '''
        Returns Dryad DOI.
        '''
        return self.dryad.doi

    @staticmethod
    def _dryad_file_id(url):
        '''
        Returns Dryad fileID from dryad file download URL as integer.
        ----------------------------------------
        Parameters:

        url : str
            — Dryad file URL in format
            'https://datadryad.org/api/v2/files/385820/download'.
        ----------------------------------------
        '''
        fid = url.strip('/download')
        fid = int(fid[fid.rfind('/')+1:])
        return fid

    @staticmethod
    def _make_dv_head(apikey):
        '''
        Returns Dataverse authentication header as dict.

        ----------------------------------------
        Parameters:

        apikey : str
            — Dataverse API key.
        ----------------------------------------
        '''
        return {'X-Dataverse-key' : apikey}

    #@staticmethod
    def set_correct_date(self, url=None, hdl=None,
                         d_type='distributionDate',
                         apikey=None):
        '''
        Sets "correct" publication date for Dataverse.

        Note: dryad2dataverse.serializer maps Dryad 'publicationDate'
        to Dataverse 'distributionDate' (see serializer.py ~line 675).

        Dataverse citation date default is ":publicationDate". See
        Dataverse API reference:
        https://guides.dataverse.org/en/4.20/api/native-api.html#id54.

        ----------------------------------------
        Parameters:

        url : str
            — Base URL to Dataverse installation.
              Defaults to dryad2dataverse.constants.DVURL

        hdl : str
            — Persistent indentifier for Dataverse study.
              Defaults to Transfer.dvpid (which can be None if the
              study has not yet been uploaded).

        d_type : str
            — Date type. One of  'distributionDate', 'productionDate',
            'dateOfDeposit'. Default 'distributionDate'.

        apikey : str
            — Default dryad2dataverse.constants.APIKEY.
        ----------------------------------------
        '''
        try:
            if not url:
                url = constants.DVURL
            if not hdl:
                hdl = self.dvpid
            headers = {'X-Dataverse-key' : apikey}
            if apikey:
                headers = {'X-Dataverse-key' : apikey}
            else:
                headers = {'X-Dataverse-key' : constants.APIKEY}

            params = {'persistentId': hdl}
            set_date = self.session.put(f'{url}/api/datasets/:persistentId/citationdate',
                                        headers=headers,
                                        data=d_type,
                                        params=params,
                                        timeout=45)
            set_date.raise_for_status()

        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError) as err:
            LOGGER.warning('Unable to set citation date for %s',
                           hdl)
            LOGGER.warning(err)
            LOGGER.warning(set_date.text)

    def upload_study(self, url=None, apikey=None, timeout=45, **kwargs):
        '''
        Uploads Dryad study metadata to target Dataverse or updates existing.
        Supplying a `targetDv` kwarg creates a new study and supplying a
        `dvpid` kwarg updates a currently existing Dataverse study.

        ----------------------------------------
        Parameters:

        url : str
            — URL of Dataverse instance. Defaults to constants.DVURL.

        apikey : str
            — API key of user. Defaults to contants.APIKEY.

        timeout : int
            — timeout on POST request.

        **KEYWORD ARGUMENTS**

        One of these is required. Supplying both or neither raises a NoTargetError

        targetDv : str
            — Short name of target dataverse. Required if new dataset.
            Specify as targetDV=value.

        dvpid = str
            — Dataverse persistent ID (for updating metadata).
            This is not required for new uploads, specify as dvpid=value

        ----------------------------------------
        '''
        if not url:
            url = constants.DVURL
        if not apikey:
            apikey = constants.APIKEY
        headers = {'X-Dataverse-key' : apikey}

        targetDv = kwargs.get('targetDv')
        dvpid = kwargs.get('dvpid')
        #dryFid = kwargs.get('dryFid') #Why did I put this here?
        if not targetDv and not dvpid:
            try:
                raise exceptions.NoTargetError('You must supply one of targetDv \
                                    (target dataverse) \
                                     or dvpid (Dataverse persistent ID)')
            except exceptions.NoTargetError as e:
                LOGGER.error('No target dataverse or dvpid supplied')
                LOGGER.exception(e)
                raise

        if targetDv and dvpid:
            try:
                raise ValueError('Supply only one of targetDv or dvpid')
            except ValueError as e:
                LOGGER.exception(e)
                raise
        if not dvpid:
            endpoint = f'{url}/api/dataverses/{targetDv}/datasets'
            upload = self.session.post(endpoint,
                                       headers=headers,
                                       json=self.dryad.dvJson,
                                       timeout=timeout)
            LOGGER.debug(upload.text)
        else:
            endpoint = f'{url}/api/datasets/:persistentId/versions/:draft'
            params = {'persistentId':dvpid}
            #Yes, dataverse uses *different* json for edits
            upload = self.session.put(endpoint, params=params,
                                      headers=headers,
                                      json=self.dryad.dvJson['datasetVersion'],
                                      timeout=timeout)
            #self._dvrecord = upload.json()
            LOGGER.debug(upload.text)

        try:
            updata = upload.json()
            self.dvStudy = updata
            if updata.get('status') != 'OK':
                try:
                    raise exceptions.DataverseUploadError(('Status return is not OK.'
                                                           f'{upload.status_code}: '
                                                           f'{upload.reason}. '
                                                           f'{upload.request.url} '
                                                           f'{upload.text}'))
                except exceptions.DataverseUploadError as e:
                    LOGGER.exception(e)
                    LOGGER.exception(traceback.format_exc())
                    raise exceptions.DataverseUploadError(('Status return is not OK.'
                                                           f'{upload.status_code}: '
                                                           f'{upload.reason}. '
                                                           f'{upload.request.url} '
                                                           f'{upload.text}'))
            upload.raise_for_status()
        except Exception as e: # Only accessible via non-requests exception
            LOGGER.exception(e)
            LOGGER.exception(traceback.format_exc())
            raise

        if targetDv:
            self.dryad.dvpid = updata['data'].get('persistentId')
        if dvpid:
            self.dryad.dvpid = updata['data'].get('datasetPersistentId')
        return self.dvpid

    @staticmethod
    def _check_md5(infile):
        '''
        Returns the md5 checksum of a file.

        ----------------------------------------
        Parameters:

        infile : str
            — Complete path to target file.
        ----------------------------------------
        '''
        blocksize = 2**16
        with open(infile, 'rb') as m:
            fmd5 = hashlib.md5()
            fblock = m.read(blocksize)
            while fblock:
                fmd5.update(fblock)
                fblock = m.read(blocksize)
        return fmd5.hexdigest()

    def download_file(self, url, filename, tmp=None,
                      size=None, chk=None, timeout=45):
        '''
        Downloads a file via requests streaming and saves to constants.TMP.
        returns md5sum on success and an exception on failure.

        ----------------------------------------
        Parameters:

        url : str
            — URL of download.

        filename : str
            — Output file name.

        timeout : int
            — Requests timeout.

        tmp : str
            — Temporary directory for downloads.
              Defaults to dryad2dataverse.constants.TMP.

        size : int
            — Reported file size in bytes.
              Defaults to dryad2dataverse.constants.MAX_UPLOAD.

        chk : str
            - md5 sum of file (if available and known).
        ----------------------------------------
        '''
        LOGGER.debug('Start download sequence')
        LOGGER.debug('MAX SIZE = %s', constants.MAX_UPLOAD)
        LOGGER.debug('Filename: %s, size=%s', filename, size)
        if not tmp:
            tmp = constants.TMP
        if tmp.endswith(os.sep):
            tmp = tmp[:-1]

        if size:
            if size > constants.MAX_UPLOAD:
                LOGGER.warning('%s: File %s exceeds '
                               'Dataverse MAX_UPLOAD size. Skipping download.',
                               self.doi, filename)
                md5 = 'this_file_is_too_big_to_upload__' #HA HA
                for i in self._files:
                    if url == i[0]:
                        i[-1] = md5
                LOGGER.debug('Stop download sequence with large file skip')
                return md5
        try:
            down = self.session.get(url, timeout=timeout, stream=True)
            down.raise_for_status()
            with open(f'{tmp}{os.sep}{filename}', 'wb') as fi:
                for chunk in down.iter_content(chunk_size=8192):
                    fi.write(chunk)

            #verify size
            #https://stackoverflow.com/questions/2104080/how-can-i-check-file-size-in-python'
            if size:
                checkSize = os.stat(f'{tmp}{os.sep}{filename}').st_size
                if checkSize != size:
                    try:
                        raise exceptions.DownloadSizeError('Download size does not match '
                                                           'reported size')
                    except exceptions.DownloadSizeError as e:
                        LOGGER.exception(e)
                        raise
            #now check the md5
            md5 = Transfer._check_md5(f'{tmp}{os.sep}{filename}')
            if chk:
                if md5 != chk:
                    try:
                        raise exceptions.HashError('Hex digest mismatch: {md5} : {chk}')
                        #is this really what I want to do on a bad checksum?
                    except exceptions.HashError as e:
                        LOGGER.exception(e)
                        raise
            for i in self._files:
                if url == i[0]:
                    i[-1] = md5
            LOGGER.debug('Complete download sequence')
            return md5
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError) as err:
            LOGGER.critical('Unable to download %s', url)
            LOGGER.exception(err)
            raise exceptions.DataverseDownloadError

    def download_files(self, files=None):
        '''
        Bulk downloader for files.

        ----------------------------------------
        Parameters:

        files : list
            — Items in list can be tuples or list with a minimum of:

              (dryaddownloadurl, filenamewithoutpath, [md5sum])

              The md5 sum should be the last member of the tuple.

              Defaults to self.files.

              Normally used without arguments to download all the associated
              files with a Dryad study.
        ----------------------------------------
        '''
        if not files:
            files = self.files
        try:
            for f in files:
                self.download_file(f[0], f[1], size=f[3], chk=f[-1])
        except exceptions.DataverseDownloadError as e:
            LOGGER.exception('Unable to download file with info %s\n%s', f, e)
            raise

    def file_lock_check(self, study, dv_url, apikey=None, count=0):
        '''
        Checks for a study lock

        Returns True if locked. Normally used to check
        if processing is completed. As tabular processing
        halts file ingest, there should be no locks on a
        Dataverse study before performing a data file upload.

        ----------------------------------------
        Parameters:

        study : str
            — Persistent indentifer of study.

        dv_url : str
            — URL to base Dataverse installation.

        apikey : str
            — API key for user.
              If not present authorization defaults to self.auth.

        count : int
            — Number of times the function has been called. Logs
              lock messages only on 0.
        ----------------------------------------
        '''
        if dv_url.endswith('/'):
            dv_url = dv_url[:-1]
        if apikey:
            headers = {'X-Dataverse-key': apikey}
        else:
            headers = self.auth
        params = {'persistentId': study}
        try:
            lock_status = self.session.get(f'{dv_url}/api/datasets/:persistentId/locks',
                                           headers=headers,
                                           params=params, timeout=300)
            lock_status.raise_for_status()
            if lock_status.json().get('data'):
                if count == 0:
                    LOGGER.warning('Study %s has been locked', study)
                    LOGGER.warning('Lock info:\n%s', lock_status.json())
                return True
            return False
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError) as err:
            LOGGER.error('Unable to detect lock status for %s', study)
            LOGGER.error('ERROR message: %s', lock_status.text)
            LOGGER.exception(err)
            #return True #Should I raise here?
            raise

    def force_notab_unlock(self, study, dv_url, apikey=None):
        '''
        Checks for a study lock and forcibly unlocks and uningests
        to prevent tabular file processing. Required if mime and filename
        spoofing is not sufficient.

        **Forcible unlocks require a superuser API key.**

        ----------------------------------------
        Parameters:

        study : str
            — Persistent indentifer of study.

        dv_url : str
            — URL to base Dataverse installation.

        apikey : str
            — API key for user.
              If not present authorization defaults to self.auth.
        ----------------------------------------
        '''
        if dv_url.endswith('/'):
            dv_url = dv_url[:-1]
        if apikey:
            headers = {'X-Dataverse-key': apikey}
        else:
            headers = self.auth
        params = {'persistentId': study}
        lock_status = self.session.get(f'{dv_url}/api/datasets/:persistentId/locks',
                                       headers=headers,
                                       params=params, timeout=300)
        lock_status.raise_for_status()
        if lock_status.json()['data']:
            LOGGER.warning('Study %s has been locked', study)
            LOGGER.warning('Lock info:\n%s', lock_status.json())
            force_unlock = self.session.delete(f'{dv_url}/api/datasets/:persistentId/locks',
                                               params=params, headers=headers,
                                               timeout=300)
            force_unlock.raise_for_status()
            LOGGER.warning('Lock removed for %s', study)
            LOGGER.warning('Lock status:\n %s', force_unlock.json())
            #This is what the file ID was for, in case it can
            #be implemented again.
            #According to Harvard, you can't remove the progress bar
            #for uploaded tab files that squeak through unless you
            #let them ingest first then reingest them. Oh well.
            #See:
            #https://groups.google.com/d/msgid/dataverse-community/
            #74caa708-e39b-4259-874d-5b6b74ef9723n%40googlegroups.com
            #Also, you can't uningest it because it hasn't been
            #ingested once it's been unlocked. So the commented
            #code below is useless (for now)
            #uningest = requests.post(f'{dv_url}/api/files/{fid}/uningest',
            #                         headers=headers,
            #                         timeout=300)
            #LOGGER.warning('Ingest halted for file %s for study %s', fid, study)
            #uningest.raise_for_status()

    def upload_file(self, dryadUrl=None, filename=None,
                    mimetype=None, size=None, descr=None,
                    md5=None, studyId=None, dest=None,
                    fprefix=None, force_unlock=False, timeout=300):
        '''
        Uploads file to Dataverse study. Returns a tuple of the
        dryadFid (or None) and Dataverse JSON from the POST request.
        Failures produce JSON with different status messages
        rather than raising an exception.

        ----------------------------------------
        Parameters:

        filename : str
            — Filename (not including path).

        mimetype : str
            — Mimetype of file.

        size : int
            — Size in bytes.

        studyId : str
            — Persistent Dataverse study identifier.
              Defaults to Transfer.dvpid.

        dest : str
            — Destination dataverse installation url.
              Defaults to constants.DVURL.

        md5 : str
            — md5 checksum for file.

        fprefix : str
            — Path to file, not including a trailing slash.

        timeout : int
            - Timeout in seconds for POST request. Default 300.

        dryadUrl : str
            - Dryad download URL if you want to include a Dryad file id.


        force_unlock : bool
            — Attempt forcible unlock instead of waiting for tabular
              file processing.
              Defaults to False.
              The Dataverse `/locks` endpoint blocks POST and DELETE requests
              from non-superusers (undocumented as of 31 March 2021).
              **Forcible unlock requires a superuser API key.**

        ----------------------------------------
        '''
        if not studyId:
            studyId = self.dvpid
        if not dest:
            dest = constants.DVURL
        if not fprefix:
            fprefix = constants.TMP
        if dryadUrl:
            fid = dryadUrl.strip('/download')
            fid = int(fid[fid.rfind('/')+1:])
        else:
            fid = 0 #dummy fid for non-Dryad use
        params = {'persistentId' : studyId}
        upfile = fprefix + os.sep + filename[:]
        badExt = filename[filename.rfind('.'):].lower()
        #Descriptions are technically possible, although how to add
        #them is buried in Dryad's API documentation
        dv4meta = {'label' : filename[:], 'description' : descr}
        #if mimetype == 'application/zip' or filename.lower().endswith('.zip'):
        if mimetype == 'application/zip' or badExt in constants.NOTAB:
            mimetype = 'application/octet-stream' # stop unzipping automatically
            filename += '.NOPROCESS' # Also screw with their naming convention
            #debug log about file names to see what is up with XSLX
            #see doi:10.5061/dryad.z8w9ghxb6
            LOGGER.debug('File renamed to %s for upload', filename)
        if size >= constants.MAX_UPLOAD:
            fail = (fid, {'status' : 'Failure: MAX_UPLOAD size exceeded'})
            self.fileUpRecord.append(fail)
            LOGGER.warning('%s: File %s of '
                           'size %s exceeds '
                           'Dataverse MAX_UPLOAD size. Skipping.', self.doi, filename, size)
            return fail

        fields = {'file': (filename, open(upfile, 'rb'), mimetype)}
        fields.update({'jsonData': f'{dv4meta}'})
        multi = MultipartEncoder(fields=fields)
        ctype = {'Content-type' : multi.content_type}
        tmphead = self.auth.copy()
        tmphead.update(ctype)
        url = dest + '/api/datasets/:persistentId/add'
        try:
            upload = self.session.post(url, params=params,
                                       headers=tmphead,
                                       data=multi, timeout=timeout)
            #print(upload.text)
            upload.raise_for_status()
            self.fileUpRecord.append((fid, upload.json()))
            upmd5 = upload.json()['data']['files'][0]['dataFile']['checksum']['value']
            if md5 and upmd5 != md5:
                try:
                    raise exceptions.HashError(f'md5sum mismatch:\nlocal: {md5}\nuploaded: {upmd5}')
                except exceptions.HashError as e:
                    LOGGER.exception(e)
                    raise

            #Make damn sure that the study isn't locked because of
            #tab file processing
            ##SPSS files still process despite spoofing MIME and extension
            ##so there's also a forcible unlock check

            #fid = upload.json()['data']['files'][0]['dataFile']['id']
            #fid not required for unlock
            #self.force_notab_unlock(studyId, dest, fid)
            if force_unlock:
                self.force_notab_unlock(studyId, dest)
            else:
                count = 0
                wait = True
                while wait:
                    wait = self.file_lock_check(studyId, dest, count=count)
                    if wait:
                        time.sleep(15) # Don't hit it too often
                    count += 1


            return (fid, upload.json())

        except Exception as e:
            LOGGER.exception(e)
            try:
                reason = upload.json()['message']
                LOGGER.warning(upload.json())
                return (fid, {'status' : f'Failure: {reason}'})
            except Exception as e:
                LOGGER.warning('Further exceptions!')
                LOGGER.exception(e)
                LOGGER.warning(upload.text)
                return (fid, {'status' : f'Failure: Reason {upload.reason}'})

    def upload_files(self, files=None, pid=None, fprefix=None, force_unlock=False):
        '''
        Uploads multiple files to study with persistentId pid.
        Returns a list of the original tuples plus JSON responses.

        ----------------------------------------
        Parameters:

        files : list
            — List contains tuples with
            (dryadDownloadURL, filename, mimetype, size).

        pid : str
            — Defaults to self.dvpid, which is generated by calling
              dryad2dataverse.transfer.Transfer.upload_study().

        fprefix : str
            — File location prefix.
              Defaults to dryad2dataverse.constants.TMP

        force_unlock : bool
            — Attempt forcible unlock instead of waiting for tabular
              file processing.
              Defaults to False.
              The Dataverse `/locks` endpoint blocks POST and DELETE requests
              from non-superusers (undocumented as of 31 March 2021).
              **Forcible unlock requires a superuser API key.**
        ----------------------------------------
        '''
        if not files:
            files = self.files
        if not fprefix:
            fprefix = constants.TMP
        out = []
        for f in files:
            #out.append(self.upload_file(f[0], f[1], f[2], f[3],
            #                             f[4], f[5], pid, fprefix=fprefix))
            #out.append(self.upload_file(*[x for x in f],
            #last item in files is not necessary
            out.append(self.upload_file(*list(f)[:-1],
                                        studyId=pid, fprefix=fprefix,
                                        force_unlock=force_unlock))
        return out

    def upload_json(self, studyId=None, dest=None):
        '''
        Uploads Dryad json as a separate file for archival purposes.

        ----------------------------------------
        Parameters:

        studyId : str
            — Dataverse persistent identifier.
              Default dryad2dataverse.transfer.Transfer.dvpid,
              which is only generated on
              dryad2dataverse.transfer.Transfer.upload_study()

        dest : str
            — Base URL for transfer.
              Default dryad2datavese.constants.DVURL
        ----------------------------------------
        '''
        if not studyId:
            studyId = self.dvpid
        if not dest:
            dest = constants.DVURL
        if not self.jsonFlag:
            url = dest + '/api/datasets/:persistentId/add'
            pack = io.StringIO(json.dumps(self.dryad.dryadJson))
            desc = {'description':'Original JSON from Dryad',
                    'categories':['Documentation', 'Code']}
            fname = self.doi[self.doi.rfind('/')+1:].replace('.', '_')
            payload = {'file': (f'{fname}.json', pack, 'text/plain;charset=UTF-8'),
                       'jsonData':f'{desc}'}
            params = {'persistentId':studyId}
            try:
                meta = self.session.post(f'{url}',
                                         params=params,
                                         headers=self.auth,
                                         files=payload)
                #0 because no dryad fid will be zero
                meta.raise_for_status()
                self.fileUpRecord.append((0, meta.json()))
                self.jsonFlag = (0, meta.json())
                LOGGER.debug('Successfully uploaded Dryad JSON to %s', studyId)

            #JSON uploads randomly fail with a Dataverse server.log error of
            #"A system exception occurred during an invocation on EJB . . ."
            #Not reproducible, so errors will only be written to the log.
            #Jesus.
            except (requests.exceptions.HTTPError,
                    requests.exceptions.ConnectionError) as err:
                LOGGER.error('Unable to upload Dryad JSON to %s', studyId)
                LOGGER.error('ERROR message: %s', meta.text)
                LOGGER.exception(err)
                #And further checking as to what is happening
                self.fileUpRecord.append((0, {'status':'Failure: Unable to upload Dryad JSON'}))
                if not isinstance(self.dryad.dryadJson, dict):
                    LOGGER.error('Dryad JSON is not a dictionary')
            except Exception as err:
                LOGGER.error('Unable to upload Dryad JSON')
                LOGGER.exception(err)

    def delete_dv_file(self, dvfid, dvurl=None, key=None):
        #WTAF curl -u $API_TOKEN: -X DELETE
        #https://$HOSTNAME/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/123

        '''
        Deletes files from Dataverse target given a dataverse file ID.
        This information is unknowable unless discovered by
        dryad2dataverse.monitor.Monitor or by other methods.

        Returns 1 on success (204 response), or 0 on other response.

        ----------------------------------------
        Parameters:

        dvurl : str
            — Base URL of dataverse instance.
              Defaults to dryad2dataverse.constants.DVURL.

        dvfid : str
            — Dataverse file ID number.
        ----------------------------------------
        '''
        if not dvurl:
            dvurl = constants.DVURL
        if not key:
            key = constants.APIKEY

        delme = self.session.delete(f'{dvurl}/dvn/api/data-deposit/v1.1/swordv2/edit-media'
                                    f'/file/{dvfid}',
                                    auth=(key, ''))
        if delme.status_code == 204:
            self.fileDelRecord.append(dvfid)
            return 1
        return 0

    def delete_dv_files(self, dvfids=None, dvurl=None, key=None):
        '''
        Deletes all files in list of Dataverse file ids from
        a Dataverse installation.

        ----------------------------------------
        Parameters:

        dvfids : list
            — List of Dataverse file ids.
              Defaults to dryad2dataverse.transfer.Transfer.fileDelRecord.

        dvurl : str
            — Base URL of Dataverse. Defaults to dryad2dataverse.constants.DVURL.

        key : str
            — API key for Dataverse. Defaults to dryad2dataverse.constants.APIKEY.
        ----------------------------------------
        '''
        #if not dvfids:
        #   dvfids = self.fileDelRecord
        if not dvurl:
            dvurl = constants.DVURL
        if not key:
            key = constants.APIKEY
        for fid in dvfids:
            self.delete_dv_file(fid, dvurl, key)
