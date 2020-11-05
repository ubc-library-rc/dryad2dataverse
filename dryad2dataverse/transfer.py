import requests
import os
from . import constants
from requests_toolbelt.multipart.encoder import MultipartEncoder

#TODO Add uploading of dvJson, get handle
'''
AUTH = {'X-Dataverse-key':'adacb5ee-54ae-4a8f-8668-78e116229c43'}
DV = 'https://abacus-staging.library.ubc.ca/api'
upload = requests.post(f'{DV}/dataverses/six/datasets', headers=AUTH, json=testCase.dvJson)
'''

#TODO Figure out what do do with subsettable files. 
# maybe migrator.constants.NOTAB?


class Transfer(object):
    def __init__(self, dryad):
        '''
        dryad : dryad.Dryad object
        '''
        self.dryad = dryad
        self._fileJson = None

    def __del__(self):
        '''Clears crap from constants.TMP on deletion'''
        for f in self.files:
            if os.path.exists(f'{constants.TMP}{os.sep}{f[1]}'):
                os.remove(f'{constants.TMP}{os.sep}{f[1]}')

    @property
    def auth(self):
        '''Returns datavese authentication header'''
        return {'X-Dataverse-key' : constants.APIKEY}

    @property
    def fileJson(self, timeout=45):
        '''
        Despite what you may think, the uniquely identifying integer describing a dataset is not
        dryadJson['id']

        It's actually the integer part of testCase._dryadJson['_links']['stash:version']['href']

        '''
        if not self._fileJson:
            headers = {'accept':'application/json', 'Content-Type':'application/json'}
            #print(f'{constants.DRYURL}/api/v2/versions/{self.dryad.id}/files') 
            fileList = requests.get(f'{constants.DRYURL}/api/v2/versions/{self.dryad.id}/files', 
                                    headers=headers,
                                    timeout=timeout)
            fileList.raise_for_status()
            self._fileJson = fileList.json()
        return self._fileJson 

    @property
    def files(self):
        '''
        Returns a list of tuples with:
        (Download_location, filename, mimetype, size)

        '''
        out = []
        files = self.fileJson['_embedded'].get('stash:files')
        if files:
            for f in files:
                downLink = f['_links']['stash:file-download']['href']
                downLink = f'{constants.DRYURL}{downLink}'
                name = f['path']
                mimeType = f['mimeType']
                size = f['size']
                out.append((downLink, name, mimeType, size))

        return out

    def _download_file(self, url, filename, timeout=45):
        '''
        Downloads file via requests streaming and saves t  constants.TMP
        returns 1 on success and 0 
        url : str
            URL of download
        filename : str
            output file name
        timeout: int
            requests timeout
        '''
        try:
            down = requests.get(url, timeout=timeout, stream=True)
            down.raise_for_status()
            with open(f'{constants.TMP}/{filename}', 'wb') as fi:
                for chunk in down.iter_content(chunk_size=8192):
                    fi.write(chunk)
            return 1
        except:
            raise
            return 0

    def download_files(self):
        try:
            for f in self.files:
                self._download_file(f[0], f[1]) 
        except:
            raise

    def _upload_file(self, filename, mimetype, size, studyId, dest=None, fprefix=constants.TMP, timeout=300):
        if not dest:
            dest = constants.DVURL
        params = {'persistentId' : studyId}
        upfile = fprefix + os.sep + filename[:]
        dv4meta = {'label' : filename[:]} #No descriptions found in dryad metadata.
        if mimetype == 'application/zip' or filename.lower().endswith('.zip'):
            mimetype = 'application/octet-stream' # stop unzipping automatically
            filename += 'NOPROCESS'

        if size >= constants.MAX_UPLOAD:
            return {'status' : 'Failure: MAX_UPLOAD size exceeded'} 

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
            return upload.json()
        except:
            raise
            return {'status' : f'Failure: Reason {upload.reason}'}

    def upload_files(self, pid): #Get handle from somewhere
        out = []
        for f in self.files:
            out.append(self._upload_file(f[1], f[2], f[3], pid))
        return out


