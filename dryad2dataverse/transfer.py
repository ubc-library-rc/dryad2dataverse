import requests
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder
from . import constants
import hashlib
import copy

#TODO Set publication date 
'''
#whichever date
date=('dateOfDeposit', depDate[0].text)[0]
ie, one of distributionDate, productionDate, dateOfDeposit
params = {'persistentId' : dvn4StdyId}
            newdate = requests.put(f'{DVN4}/datasets/:persistentId/citationdate', headers=AUTHHEAD, data=date, params=params)

'''

class Transfer(object):
    def __init__(self, dryad):
        '''
        dryad : dryad.Dryad object
        '''
        self.dryad = dryad
        self._fileJson = None
        #self._files =  [list(f) for f in self.dryad.files]
        self._files = copy.deepcopy(self.dryad.files)
        self.fileUpRecord = []
        self.fileDelRecord = []
        self.dvStudy = None
        self.jsonFlag = None #Whether or not new json uploaded

    def _del(self): #Change name to __del__ to make a destructor
        '''Clears crap from constants.TMP on deletion'''
        for f in self.files:
            if os.path.exists(f'{constants.TMP}{os.sep}{f[1]}'):
                os.remove(f'{constants.TMP}{os.sep}{f[1]}')

    @property
    def dvpid(self):
        return self.dryad.dvpid

    @property
    def auth(self):
        '''Returns datavese authentication header'''
        return {'X-Dataverse-key' : constants.APIKEY}

    @property
    def fileJson(self):
        '''
        Despite what you may think, the uniquely identifying integer describing a dataset is not
        dryadJson['id']

        It's actually the integer part of testCase._dryadJson['_links']['stash:version']['href']
        '''
        return self.dryad.fileJson.copy()
   
    @property
    def files(self):
        '''
        Returns a list of lists with:
        [Download_location, filename, mimetype, size, description, md5digest]
        This is mutable; downloading a file will add md5 info if not available
        '''
        return self._files

    @property
    def oversize(self):
        return self.dryad.oversize
    
    @property
    def doi(self):
        return self.dryad.doi

    def _dryad_file_id(self, url):
        '''
        Returns Dryad fileID from dryad file download URL as integer

        url : str
            Dryad file URL in format 'https://datadryad.org/api/v2/files/385820/download'
        '''
        fid = url.strip('/download')
        fid = int(fid[fid.rfind('/')+1:])
        return fid

    def _make_dv_head(self, apikey):
        return {'X-Dataverse-key' : apikey}

    def _set_correct_date(self, url, header, data):
        #TODO write this correctly
        requests.put(f'{DVN4}/datasets/:persistentId/citationdate', headers=AUTHHEAD, data=date, params=params)

    def upload_study(self, url=None, apikey=None, timeout=45, **kwargs):
        '''
        Uploads Dryad study metadata to target dataverse or updates existing. targetDv kwarg creates new, dvpid kwarg updates

        url : str
            URL of Dataverse instance. Defaults to constants.DVURL
        apikey : str
            API key of user. Defaults to contants.APIKEY
        timeout : int
            timeout on POST request

        KEYWORD ARGUMENTS
        One of these is required. Supplying both or neither raises an value error 
        targetDv : str
            short name of target dataverse. Required if new dataset. specify as targetDV=value
        dvpid = str
            Dataverse persistent ID (for updating metadata)
            This is not required for new uploads, specify as dvpid=value
        OPTIONAL KEYWORD ARGUMENTS
        '''
        if not url: url = constants.DVURL
        if not apikey: apikey = constants.APIKEY
        headers = {'X-Dataverse-key' : apikey}

        targetDv = kwargs.get('targetDv')
        dvpid = kwargs.get('dvpid')
        dryFid = kwargs.get('dryFid')
        if not targetDv and not dvpid:
            raise ValueError('You must supply one of targetDv or dvpid')
        if targetDv and dvpid:
            raise ValueError('Supply only one of targetDv or dvpid')
        if not dvpid:
            endpoint = f'{url}/api/dataverses/{targetDv}/datasets'
            upload = requests.post(endpoint, 
                               headers=headers, json = self.dryad.dvJson)
        else:
            endpoint = f'{url}/api/datasets/:persistentId/versions/:draft'
            params={'persistentId':dvpid}
            #Yes, dataverse uses *different* json for edits
            upload = requests.put(endpoint, params=params,
                               headers=headers, json = self.dryad.dvJson['datasetVersion'])
            #self._dvrecord = upload.json()
            
        upload.raise_for_status()
        updata = upload.json()
        self.dvStudy = updata
        if updata.get('status') != 'OK' : raise #probably should raise something specific here
        if targetDv:
            self.dryad.dvpid = updata['data'].get('persistentId')
        if dvpid:
            self.dryad.dvpid = updata['data'].get('datasetPersistentId')
        return self.dvpid

    def _check_md5(self, infile):
        '''
        Returns md5 checksum of file

        infile : str
            complete path to file
        '''
        blocksize = 2**16
        with open(infile, 'rb') as m:
            fmd5 = hashlib.md5()
            fblock = m.read(blocksize)
            while len(fblock) > 0:
                fmd5.update(fblock)
                fblock = m.read(blocksize)
        return fmd5.hexdigest()

    def download_file(self, url, filename, tmp=None, maxsize=None, timeout=45):
        #TODO finish max size checking, figure out what to do with the md5
        '''
        Downloads file via requests streaming and saves to constants.TMP
        returns 1 on success and 0 
        url : str
            URL of download
        filename : str
            output file name
        timeout: int
            requests timeout
        tmp : str
            temporary directory for downloads. Defaults to dryad2dataverse.constants.TMP
        maxsize : int
            Maximum file size in bytes. Defaults to dryad2dataverse.constants.MAX_UPLOAD
        chk : str
            md5 sum of file (if available)
        '''
        if not tmp:
            tmp = constants.TMP
        if tmp.endswith(os.sep): tmp = tmp[:-1]
        if not maxsize:
            maxsize = constants.MAX_UPLOAD
        
        try:
            down = requests.get(url, timeout=timeout, stream=True)
            down.raise_for_status()
            with open(f'{tmp}{os.sep}{filename}', 'wb') as fi:
                for chunk in down.iter_content(chunk_size=8192):
                    fi.write(chunk)

            #verify size
            #https://stackoverflow.com/questions/2104080/how-can-i-check-file-size-in-python'
            if maxsize:
                checkSize = os.stat(f'{tmp}{os.sep}{filename}').st_size
                if checkSize != maxsize:
                    raise #raise what? I need some custom exceptions
            #now check the md5
            md5 = self._check_md5(f'{tmp}{os.sep}{filename}')
            if chk:
                if md5 != chk:
                    raise #is this really what I want to do on a bad checksum?
            for i in self._files:
                if url == i[0]:
                    i[-1] = md5
            return md5 
        except:
            raise
            return 0

    def download_files(self, files=None):
        if not files:
            files = self.files
        try:
            for f in files:
                self.download_file(f[0], f[1], chk=f[-1]) 
        except:
            raise

    def upload_file(self, filename, mimetype, size, descr, md5, studyId=None, dest=None, fprefix=None, timeout=300, dryadUrl=None):
        '''
        Uploads file to Dataverse study. Returns a tuple of the dryadFid (or None) and Dataverse JSON from the POST request.
        Failures produce JSON with different status messages rather than raising an exception.

        filename : str
            Filename (not including path)
        mimetype : str
            Mimetype of file
        size : int
            Size in bytes
        studyId : str
            Persistent study identifier for dataverse. Defaults to Transfer.dvpid
        dest : str
            Destination dataverse installation url. Defaults to constants.DVURL
        md5 : str
            md5 checksum for file
        fprefix : str
            Path to file, not including a trailing slash
        timeout : int
            Timeout in seconds for POST request
        dryadUrl : str
            Dryad download URL if you want to include a dryad file id
        '''
        if not studyId : studyId = self.dvpid
        if not dest:
            dest = constants.DVURL
        if not fprefix:
            fprefix = constants.TMP
        if dryadUrl:
            fid = dryadUrl.strip('/download')
            fid = int(fid[fid.rfind('/')+1:])
        params = {'persistentId' : studyId}
        upfile = fprefix + os.sep + filename[:]
        badExt = filename[filename.rfind('.'):].lower()
        
        dv4meta = {'label' : filename[:], 'description' : descr} #Descriptions are technically possible, although how to add them is buried in Dryad's API documentation
        #if mimetype == 'application/zip' or filename.lower().endswith('.zip'):
        if mimetype == 'application/zip' or badExt in constants.NOTAB:
            mimetype = 'application/octet-stream' # stop unzipping automatically
            filename += 'NOPROCESS' #Also screw with their naming convention

        if size >= constants.MAX_UPLOAD:
            fail = (fid, {'status' : 'Failure: MAX_UPLOAD size exceeded'} )
            self.fileUpRecord.append(fail)
            return fail 

        fields = {'file': (filename, open(upfile, 'rb'), mimetype)}
        fields.update({'jsonData': f'{dv4meta}'})
        multi = MultipartEncoder(fields=fields)
        ctype = {'Content-type' : multi.content_type}
        tmphead = self.auth.copy()
        tmphead.update(ctype)
        url = dest + '/api/datasets/:persistentId/add'
        try:
            upload = requests.post(url, params=params, headers=tmphead, data=multi, timeout=timeout)
            upload.raise_for_status()
            self.fileUpRecord.append((fid, upload.json()))
            upmd5 = upload.json()['data']['files'][0]['dataFile']['checksum']['value']
            if upmd5 != md5:
                raise
            return (fid, upload.json())
        except:
            print( upload.text)
            raise
            return (fid, {'status' : f'Failure: Reason {upload.reason}'})

    def upload_files(self, files=None, pid=None, fprefix=None):
        '''
        Uploads multiple files to study with persistentId pid. Returns a list of the original tuples plus JSON responses.
        
        files: list
            list contains a tuple with (dryadDownloadURL, filename, mimetype, size)
        pid : str
            defaults to self.dvpid, which is generated by calling Transfer.upload_study()
        '''
        if not files:
            files = self.files
        if not fprefix:
            fprefix = constants.TMP
        out = []
        for f in files:
            out.append(self.upload_file(f[1], f[2], f[3], f[4], f[5], pid, dryadUrl=f[0], fprefix=fprefix))
        return out

    def upload_json(self, studyId=None, dest=None):
        '''
        Uploads Dryad json as a separate file for archival purposes
        pid : str
            Dataverse pid
        '''
        if not studyId:
            studyId = self.dvpid
        if not dest:
            dest = constants.DVURL
        if not self.jsonflag:
            url = dest + '/api/datasets/:persistentId/add'
            pack = io.StringIO(json.dumps(self.dryad.dryadJson))
            desc = {'description':f'{self.dryad.doi}.json', 'categories':['Documentation', 'Code']} 
            try:
                meta = requests.post(f'{url}', 
                                     params={'persistentId':studyId}, 
                                     headers=self.auth, 
                                     files={'file':(f'Dryad_{self.doi}.json', pack, 'text/plain;charset=UTF-8'), 
                                            'jsonData':f'{desc}'})
                self.fileUpRecord.append(0, meta.json())#0 because no dryad fid will be zero
                meta.raise_for_status()
                self.jsonflag = (0, meta.json())

            except:
                raise

    def delete_dv_file(self, dvfid, dvurl=None, key=None):
        #WTAF curl -u $API_TOKEN: -X DELETE https://$HOSTNAME/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/123

        '''
        Deletes files from Dataverse target given a dataverse file ID.
        This information is unknowable unless discovered by
        dryad2dataverse.monitor.Monitor or by other methods.

        Returns 1 on success (204 response), or 0 on other response.

        dvurl : str
            Base URL of dataverse instance. Defaults to dryad2dataverse.constants.DVURL

        dvfid : 
            Dataverse file ID number
        
        '''
        if not dvurl:
            dvurl = constants.DVURL
        if not key:
            key = constants.APIKEY

        delme = requests.delete(f'{dvurl}/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/{dvfid}', auth=(key,''))
        if delme.status_code == 204:
            self.fileDelRecord.append(dvfid)
            return 1
        return 0

    def delete_dv_files(self, dvfids=None, dvurl=None, key=None):
        '''
        Deletes all files in list of dataverese file file ids from dataverse. 
        dvfids : list
            List of dataverse fids. Defaults to dryad2dataverse.transfer.Transfer.fileDelRecord
        dvurl : str
            Base URL of Dataverse. Defaults to dryad2dataverse.constants.DVURL
        key : str
            API key for Dataverse. Detfaults to dryad2dataverse.constants.APIKEY
        '''
        #if not dvfids:
        #   dvfids = self.fileDelRecord
        if not dvurl:
            dvurl = constants.DVURL
        if not key:
            key = constants.APIKEY
        for fid in dvfids:
            self.delete_dv_file(fid, dvurl, key)
            
            


