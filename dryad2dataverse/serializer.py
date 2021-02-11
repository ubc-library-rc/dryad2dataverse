'''
Serializes Dryad study JSON to Dataverse JSON, as well as
producing associated file information.
'''

import logging
import urllib.parse

import requests

from  dryad2dataverse import constants

logger = logging.getLogger(__name__)
#Connection monitoring as per
#https://stackoverflow.com/questions/16337511/log-all-requests-from-the-python-requests-module
url_logger = logging.getLogger('urllib3')

class Serializer(object):
    '''
    Serializes Dryad JSON to Dataverse JSON
    '''
    def __init__(self, doi):
        '''
        Creates Dryad study metadata instance.

        ----------------------------------------
        Parameters:

        doi : str
            DOI of Dryad study. Required for downloading.
            eg: 'doi:10.5061/dryad.2rbnzs7jp'
        ----------------------------------------
        '''
        self.doi = doi
        self._dryadJson = None
        self._fileJson = None
        self._dvJson = None
        #Serializer objects will be assigned a Dataverse study PID
        #if dryad2Dataverse.transfer.Transfer() is instantiated
        self.dvpid = None
        logger.debug('Creating Serializer instance object')

    def fetch_record(self, url=None, timeout=45):
        '''
        Fetches Dryad study record JSON from Dryad V2 API at
        https://datadryad.org/api/v2/datasets/
        Saves to Dryad._dryadJson

        ----------------------------------------
        Parameters:

        url : str
            Dryad instance base URL (eg: 'https://datadryad.org')
        timeout : int
            timeout in seconds. Default 45
        ----------------------------------------
        '''
        if not url:
            url = constants.DRYURL
        try:
            headers = {'accept':'application/json',
                       'Content-Type':'application/json'}
            doiClean = urllib.parse.quote(self.doi, safe='')
            resp = requests.get(f'{url}/api/v2/datasets/{doiClean}',
                                headers=headers, timeout=timeout)
            resp.raise_for_status()
            self._dryadJson = resp.json()
        except Exception as e:
            logger.error('URL error for: %s', url)
            logger.exception(e)
            raise

    @property
    def id(self):
        '''
        Returns Dryad unique *database* ID, not the DOI

        Where the original Dryad JSON is dryadJson, it's the integer
        trailing portion of:

        dryadJson['_links']['stash:version']['href']
        '''
        href = self.dryadJson['_links']['stash:version']['href']
        index = href.rfind('/') + 1
        return int(href[index:])

    @property
    def dryadJson(self):
        '''
        Returns Dryad study JSON
        '''
        if not self._dryadJson:
            self.fetch_record()
        return self._dryadJson

    @property
    def dvJson(self):
        '''
        Returns Dataverse study JSON
        '''
        self._assemble_json()
        return self._dvJson

    @property
    def fileJson(self, timeout=45):
        '''
        Returns a list of file JSONs from call to Dryad API /files/{id},
        where the ID is parsed from the Dryad JSON. Dryad file listings
        are paginated

        ----------------------------------------
        Parameters:
        timeout : int
            request timeout in seconds
        ----------------------------------------
        '''
        if not self._fileJson:
            try:
                self._fileJson = []
                headers = {'accept':'application/json',
                           'Content-Type':'application/json'}
                fileList = requests.get(f'{constants.DRYURL}/api/v2/versions/{self.id}/files',
                                        headers=headers,
                                        timeout=timeout)
                fileList.raise_for_status()
                total = fileList.json()['total']
                lastPage = fileList.json()['_links']['last']['href']
                pages = int(lastPage[lastPage.rfind('=')+1:])
                self._fileJson.append(fileList.json())
                for i in range(2, pages+1):
                    fileCont = requests.get(f'{constants.DRYURL}/api/v2'
                                            f'/versions/{self.id}/files?page={i}',
                                            headers=headers,
                                            timeout=timeout)
                    fileCont.raise_for_status()
                    self._fileJson.append(fileCont.json())
            except Exception as e:
                logger.exception(e)
                raise
        return self._fileJson

    @property
    def files(self):
        '''
        Returns a list of tuples with:

        (Download_location, filename, mimetype, size, description,
        digestType, md5sum)

        At this time only md5 is supported.
        '''
        out = []
        for page in self.fileJson:
            files = page['_embedded'].get('stash:files')
            if files:
                for f in files:
                    downLink = f['_links']['stash:file-download']['href']
                    downLink = f'{constants.DRYURL}{downLink}'
                    name = f['path']
                    mimeType = f['mimeType']
                    size = f['size']
                    #HOW ABOUT PUTTING THIS IN THE DRYAD API PAGE?
                    descr = f.get('description', '')
                    digestType = f.get('digestType')
                    #not all files have a digest
                    digest = f.get('digest')
                    md5 = ''
                    if digestType == 'md5' and digest:
                        md5 = digest
                        #nothing in the docs as to algorithms so just picking md5
                        #Email from Ryan Scherle 30 Nov 20: supported digest type
                        #('adler-32','crc-32','md2','md5','sha-1','sha-256',
                        #'sha-384','sha-512')
                    out.append((downLink, name, mimeType, size, descr, md5))

        return out

    @property
    def oversize(self, maxsize=None):
        '''
        Returns a list of Dryad files whose size value
        exceeds maxsize. Maximum size defaults to
        dryad2dataverse.constants.MAX_UPLOAD

        ----------------------------------------
        Parameters:

        maxsize : int
            size in bytes in which to flag as oversize.
            Default: constants.MAX_UPLOAD
        ----------------------------------------
        '''
        if not maxsize:
            maxsize = constants.MAX_UPLOAD
        toobig = []
        for f in self.files:
            if f[3] >= maxsize:
                toobig.append(f)
        return toobig

    def _typeclass(self, typeName, multiple, typeClass):
        '''
        Creates wrapper around single or multiple Dataverse JSON objects.
        Returns a dict *without* the  Dataverse 'value' key'

        ----------------------------------------
        Parameters:

        typeName : str
            Dataverse typeName (eg: 'author')
        multiple : boolean
        typeClass : str
            Dataverse typeClass. Usually one of 'compound', 'primitive,
            'controlledVocabulary')
        ----------------------------------------
        '''
        return {'typeName':typeName, 'multiple':multiple,
                'typeClass':typeClass}

    def _convert_generic(self, **kwargs):
        '''
        Generic dataverse json segment creator of form:
            {dvField:
                {'typeName': dvField,
                  'value': dryField}
        Suitable for generalized conversions. Only provides fields with
        multiple: False and typeclass:Primitive

        ----------------------------------------
        Parameters:

        dvField : str
            Dataverse output field
        dryField : str
            Dryad JSON field to convert
        inJson : dict
            Dryad JSON **segment** to convert
        addJSON : dict (optional)
            any other JSON required to complete (cf ISNI)
        rType : str
            'dict' (default) or 'list'
            returns 'value' field as dict value or list.
        pNotes : str
            Notes to be prepended to list type values.
            No trailing space required.
        ----------------------------------------
        '''

        dvField = kwargs.get('dvField')
        dryField = kwargs.get('dryField')
        inJson = kwargs.get('inJson')
        addJson = kwargs.get('addJson')
        pNotes = kwargs.get('pNotes', '')
        rType = kwargs.get('rType', 'dict')
        if not dvField or not dryField or not inJson:
            try:
                raise ValueError('Incorrect or insufficient fields provided')
            except ValueError as e:
                logger.exception(e)
                raise
        outfield = inJson.get(dryField)
        if outfield: outfield = outfield.strip()
        #if not outfield:
        #    raise ValueError(f'Dryad field {dryField} not found')
        # If value missing can still concat empty dict
        if not outfield:
            return {}
        if rType == 'list':
            if pNotes:
                outfield = [f'{pNotes} {outfield}']

        outJson = {dvField:{'typeName':dvField,
                            'multiple': False,
                            'typeClass':'primitive',
                            'value': outfield}}
        #Simple conversion
        if not addJson:
            return outJson

        #Add JSONs together
        addJson.update(outJson)
        return addJson

    def _convert_author_names(self, author):
        '''
        Produces required author json fields.
        Special case, requires concatenation of several fields
        ----------------------------------------
        Parameters:

        author : dict
            dryad['author'] JSON segment
        ----------------------------------------
        '''
        first = author.get('firstName')
        last = author.get('lastName')
        if first + last is None:
            return None
        authname = f"{author.get('lastName','')}, {author.get('firstName', '')}"
        return {'authorName':
                {'typeName':'authorName', 'value': authname,
                 'multiple':False, 'typeClass':'primitive'}}

    def _convert_keywords(self, *args):
        '''
        Produces the insane keyword structure Dataverse JSON segment
        from a list of words

        ----------------------------------------
        Parameters:

        args : list with str elements
            remember to expand with *
        General input is Dryad JSON 'keywords', ie *Dryad['keywords']
        ----------------------------------------
        '''
        outlist = []
        for arg in args:
            outlist.append({'keywordValue': {
                'typeName':'keywordValue',
                'value': arg}})
        return outlist

    def _convert_notes(self, dryJson):
        '''
        dryJson : dict
            Dryad JSON in dict format

        returns formatted notes field with Dryad JSON values that
        don't really fit anywhere into the Dataverse JSON.
        '''
        notes = ''
        #these fields should be concatenated into notes
        notable = ['versionNumber',
                   'versionStatus',
                   'manuscriptNumber',
                   'curationStatus',
                   'preserveCurationStatus',
                   'invoiceId',
                   'sharingLink',
                   'loosenValidation',
                   'skipDataciteUpdate',
                   'storageSize',
                   'visibility',
                   'skipEmails']
        for note in notable:
            text = dryJson.get(note)
            if text:
                text = str(text).strip()
                if note == 'versionNumber':
                    text = f'<b>Dryad version number:</b> {text}'
                if note == 'versionStatus':
                    text = f'<b>Version status:</b> {text}'
                if note == 'manuscriptNumber':
                    text = f'<b>Manuscript number:</b> {text}'
                if note == 'curationStatus':
                    text = f'<b>Dryad curation status:</b> {text}'
                if note == 'preserveCurationStatus':
                    text = f'<b>Dryad preserve curation status:</b> {text}'
                if note == 'invoiceId':
                    text = f'<b>Invoice ID:</b> {text}'
                if note == 'sharingLink':
                    text = f'<b>Sharing link:</b> {text}'
                if note == 'loosenValidation':
                    text = f'<b>Loosen validation:</b> {text}'
                if note == 'skipDataciteUpdate':
                    text = f'<b>Skip Datacite update:</b> {text}'
                if note == 'storageSize':
                    text = f'<b>Storage size:</b> {text}'
                if note == 'visibility':
                    text = f'<b>Visibility:</b> {text}'
                if note == 'skipEmails':
                    text = f'<b>Skip emails:</b> {text}'

                notes += f'<p>{text}</p>\n'
        concat = {'typeName':'notesText',
                  'multiple':False,
                  'typeClass': 'primitive',
                  'value': notes}
        return concat

    def _boundingbox(self, north, south, east, west):
        '''
        Makes a Dataverse bounding box from appropriate coordinates.
        Returns Dataverse json segment

        ----------------------------------------
        Parameters:

        north, south, east, west | float
            Coordinates in decimal degrees.
        ----------------------------------------
        '''
        names = ['north', 'south', 'east', 'west']
        points = [str(x) for x in [north, south, east, west]]
        #Because coordinates in DV are strings BFY
        coords = [(x[0]+'Longitude', {x[0]:x[1]}) for x in zip(names, points)]
        #Yes, everything is longitude in Dataverse
        out = []
        for coord in coords:
            out.append(self._convert_generic(inJson=coord[1],
                                             dvField=coord[0],
                                             #dryField='north'))
                                             dryField=[k for k in coord[1].keys()][0]))
        return out

    def _convert_geospatial(self, dryJson):
        '''
        Outputs Dataverse geospatial metadata block.
        Requires internet connection to connect to https://geonames.org

        ----------------------------------------
        Parameters:

        dryJson : dict
            Dryad json as dict
        ----------------------------------------
        '''
        if dryJson.get('locations'):
            #out = {}
            coverage = []
            box = []
            otherCov = None
            gbbox = None
            for loc in dryJson.get('locations'):
                if loc.get('place'):
                    #These are impossible to clean. Going to "other" field

                    other = self._convert_generic(inJson=loc,
                                                  dvField='otherGeographicCoverage',
                                                  dryField='place')
                    coverage.append(other)


                if loc.get('point'):
                    #makes size zero bounding box
                    north = loc['point']['latitude']
                    south = north
                    east = loc['point']['longitude']
                    west = east
                    point = self._boundingbox(north, south, east, west)
                    box.append(point)

                if loc.get('box'):
                    north = loc['box']['neLatitude']
                    south = loc['box']['swLatitude']
                    east = loc['box']['neLongitude']
                    west = loc['box']['swLongitude']
                    area = self._boundingbox(north, south, east, west)
                    box.append(area)

            if coverage:
                otherCov = self._typeclass(typeName='geographicCoverage',
                                           multiple=True, typeClass='compound')
                otherCov['value'] = coverage

            if box:
                gbbox = self._typeclass(typeName='geographicCoverage',
                                        multiple=True, typeClass='compound')
                gbbox['value'] = box

            if otherCov or gbbox:
                gblock = {'geospatial': {'displayName' : 'Geospatial Metadata',
                                         'fields': []}}
                if otherCov:
                    gblock['geospatial']['fields'].append(otherCov)
                if gbbox:
                    gblock['geospatial']['fields'].append(gbbox)
            return gblock
        return {}

    def _assemble_json(self, dryJson=None, dvContact=None,
                       dvEmail=None, defContact=True):
        '''
        Assembles Dataverse json from Dryad JSON components

        Dataverse JSON is a nightmare, so this function is too.
        ----------------------------------------
        Parameters:

        dryJson : dict
            Dryad json as dict
        dvContact : str
            default Dataverse contact name
        dvEmail : str
            default Dataverse 4 contact email address
        defContact : boolean
            include default contact information with record
        ----------------------------------------
        '''
        if not dvContact:
            dvContact = constants.DV_CONTACT_NAME
        if not dvEmail:
            dvEmail = constants.DV_CONTACT_EMAIL
        if not dryJson:
            dryJson = self.dryadJson
        #print(dryJson)
        self._dvJson = {'datasetVersion':
                        {'license':'CC0',
                         'termsOfUse': 'CC0 Waiver',
                         'metadataBlocks':{'citation':
                                           {'displayName': 'Citation Metadata',
                                            'fields': []},
                                           }
                         }
                        }
        #REQUIRED Dataverse fields

        #Dryad is a general purpose database; it is hard/impossible to get
        #Dataverse required subject tags out of their keywords, so:
        defaultSubj = {'typeName' : 'subject',
                       'typeClass':'controlledVocabulary',
                       'multiple': True,
                       'value' : ['Other']}
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(defaultSubj)

        reqdTitle = self._convert_generic(inJson=dryJson,
                                          dryField='title',
                                          dvField='title')['title']

        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(reqdTitle)

        #authors
        out = []
        for a in dryJson['authors']:
            reqdAuthor = self._convert_author_names(a)
            if reqdAuthor:
                affiliation = self._convert_generic(inJson=a,
                                                    dvField='authorAffiliation',
                                                    dryField='affiliation')
                addOrc = {'authorIdentifierScheme':
                          {'typeName':'authorIdentifierScheme',
                           'value': 'ORCID',
                           'typeClass': 'controlledVocabulary',
                           'multiple':False}}
                #only ORCID at UBC
                orcid = self._convert_generic(inJson=a,
                                              dvField='authorIdentifier',
                                              dryField='orcid',
                                              addJson=addOrc)
                if affiliation:
                    reqdAuthor.update(affiliation)
                if orcid:
                    reqdAuthor.update(orcid)
                out.append(reqdAuthor)

        authors = self._typeclass(typeName='author',
                                  multiple=True, typeClass='compound')
        authors['value'] = out

        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(authors)


        ##rewrite as function:contact
        out = []
        for e in dryJson['authors']:
            reqdContact = self._convert_generic(inJson=e,
                                                dvField='datasetContactEmail',
                                                dryField='email')
            if reqdContact:
                author = self._convert_author_names(e)
                author = {'author':author['authorName']['value']}
                #for passing to function
                author = self._convert_generic(inJson=author,
                                               dvField='datasetContactName',
                                               dryField='author')
                if author:
                    reqdContact.update(author)
                affiliation = self._convert_generic(inJson=e,
                                                    dvField='datasetContactAffiliation',
                                                    dryField='affiliation')
                if affiliation:
                    reqdContact.update(affiliation)
                out.append(reqdContact)

        if defContact:
            #Adds default contact information the tail of the list
            defEmail = self._convert_generic(inJson={'em':dvEmail},
                                             dvField='datasetContactEmail',
                                             dryField='em')
            defName = self._convert_generic(inJson={'name':dvContact},
                                            dvField='datasetContactName',
                                            dryField='name')
            defEmail.update(defName)
            out.append(defEmail)

        contacts = self._typeclass(typeName='datasetContact',
                                   multiple=True, typeClass='compound')
        contacts['value'] = out
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(contacts)

        #Description
        description = self._typeclass(typeName='dsDescription',
                                      multiple=True, typeClass='compound')
        desCat = [('abstract', '<b>Abstract</b><br/>'),
                  ('methods', '<b>Methods</b><br />'),
                  ('usageNotes', '<b>Usage notes</b><br />')]
        out = []
        for desc in desCat:
            if dryJson.get(desc[0]):
                descrField = self._convert_generic(inJson=dryJson,
                                                   dvField='dsDescriptionValue',
                                                   dryField=desc[0])
                descrField['dsDescriptionValue']['value'] = desc[1] + descrField['dsDescriptionValue']['value']

                descDate = self._convert_generic(inJson=dryJson,
                                                 dvField='dsDescriptionDate',
                                                 dryField='lastModificationDate')
                descrField.update(descDate)
                out.append(descrField)

        description['value'] = out
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(description)

        #Granting agencies
        if dryJson.get('funders'):

            out = []
            for fund in dryJson['funders']:
                org = self._convert_generic(inJson=fund,
                                            dvField='grantNumberAgency',
                                            dryField='organization')
                if fund.get('awardNumber'):
                    fund = self._convert_generic(inJson=fund,
                                                 dvField='grantNumberValue',
                                                 dryField='awardNumber')
                    org.update(fund)
                out.append(org)
            grants = self._typeclass(typeName='grantNumber',
                                     multiple=True, typeClass='compound')
            grants['value'] = out
            self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(grants)

        #Keywords
            keywords = self._typeclass(typeName='keyword',
                                       multiple=True, typeClass='compound')
            out = []
            for key in dryJson.get('keywords', []):
                #Apparently keywords are not required
                keydict = {'keyword':key}
                #because takes a dict
                kv = self._convert_generic(inJson=keydict,
                                           dvField='keywordValue',
                                           dryField='keyword')
                vocab = {'dryad':'Dryad'}
                voc = self._convert_generic(inJson=vocab,
                                            dvField='keywordVocabulary',
                                            dryField='dryad')
                kv.update(voc)
                out.append(kv)
            keywords['value'] = out
            self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(keywords)

        #modification date
        moddate = self._convert_generic(inJson=dryJson,
                                        dvField='dateOfDeposit',
                                        dryField='lastModificationDate')
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(moddate['dateOfDeposit'])
        #This one isn't nested BFY

        #distribution date
        distdate = self._convert_generic(inJson=dryJson,
                                         dvField='distributionDate',
                                         dryField='publicationDate')
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(distdate['distributionDate'])
        #Also not nested

        #publications
        publications = self._typeclass(typeName='publication', multiple=True, typeClass='compound')
        #quick and dirty lookup table
        #TODO see https://github.com/CDL-Dryad/dryad-app/blob/31d17d8dab7ea3bab1256063a1e4d0cb706dd5ec/stash/stash_datacite/app/models/stash_datacite/related_identifier.rb
        #no longer required
        #lookup = {'IsDerivedFrom':'Is derived from',
        #          'Cites':'Cites',
        #          'IsSupplementTo': 'Is supplement to',
        #          'IsSupplementedBy': 'Is supplemented by'}
        out = []
        if dryJson.get('relatedWorks'):
            for r in dryJson.get('relatedWorks'):
                #id = r.get('identifier')
                #TODO Verify that changing id to _id has not broken anything: 11Feb21
                _id = r.get('identifier')
                relationship = r.get('relationship')
                idType = r.get('identifierType')
                #citation = {'citation': f"{lookup[relationship]}: {id}"}
                citation = {'citation': relationship.capitalize()}
                pubcite = self._convert_generic(inJson=citation,
                                                dvField='publicationCitation',
                                                dryField='citation')
                pubIdType = self._convert_generic(inJson=r,
                                                  dvField='publicationIDType',
                                                  dryField='identifierType')
                #ID type must be lower case
                pubIdType['publicationIDType']['value'] = pubIdType['publicationIDType']['value'].lower()
                pubIdType['publicationIDType']['typeClass'] = 'controlledVocabulary'

                pubUrl = self._convert_generic(inJson=r,
                                               dvField='publicationURL',
                                               dryField='identifier')

                #Dryad doesn't just put URLs in their URL field.
                if pubUrl['publicationURL']['value'].lower().startswith('doi:'):
                    fixurl = 'https://doi.org/' + pubUrl['publicationURL']['value'][4:]
                    pubUrl['publicationURL']['value'] = fixurl
                    print(fixurl)
                pubcite.update(pubIdType)
                pubcite.update(pubUrl)
                out.append(pubcite)
        publications['value'] = out
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(publications)
        #notes
        #go into primary notes field, not DDI
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(self._convert_notes(dryJson))

        #Geospatial metadata
        self._dvJson['datasetVersion']['metadataBlocks'].update(self._convert_geospatial(dryJson))

        #DOI --> agency/identifier
        doi = self._convert_generic(inJson=dryJson, dryField='identifier',
                                    dvField='otherIdValue')
        doi.update(self._convert_generic(inJson={'agency':'Dryad'},
                                         dryField='agency',
                                         dvField='otherIdAgency'))
        agency = self._typeclass(typeName='otherId',
                                 multiple=True, typeClass='compound')
        agency['value'] = [doi]
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(agency)

