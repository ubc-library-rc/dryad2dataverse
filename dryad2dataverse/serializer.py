'''Import and convert dryad metadata'''
from . import constants
import urllib.parse
import requests

#TODO Add generic contact info to required metadata

class Serializer(object):
    def __init__(self, doi):
        '''
        doi : str
            DOI of Dryad study. Required for downloading. eg: 'doi:10.5061/dryad.2rbnzs7jp'
        '''
        self.doi = doi
        self._dryadJson = None
        self._fileJson = None
        #Serializer objects will be assigned a dataverse study PID 
        #if dryad2Dataverse.transfer.Transfer() is instantiated
        self.dvpid = None

    def fetch_record(self, url=None, timeout=45):
        '''
        Fetches Dryad study record JSON from Dryad V2 API at https://datadryad.org/api/v2/datasets/
        Saves to Dryad._dryadJson
        url : str
            Dryad instance base URL (eg: 'https://datadryad.org')
        timeout : int
            timeout in seconds. Default 45
        '''
        if not url:
            url = constants.DRYURL
        headers = {'accept':'application/json', 'Content-Type':'application/json'}
        doiClean = urllib.parse.quote(self.doi, safe='')
        resp = requests.get(f'{url}/api/v2/datasets/{doiClean}',
                            headers=headers, timeout=timeout)
        resp.raise_for_status()
        self._dryadJson = resp.json() 

    @property
    def id(self):
        '''
        Returns Dryad unique ID.

        The 'id' is not dryadjson['id']
        It's actually the integer part of testCase._dryadJson['_links']['stash:version']['href']

        The documentation, naturally, is not clear that this is the case.
        '''
        href = self.dryadJson['_links']['stash:version']['href']
        index = href.rfind('/') + 1
        return int(href[index:])
    
    @property
    def dryadJson(self):
        if not self._dryadJson:
            self.fetch_record()
        return self._dryadJson

    @property
    def dvJson(self):
        self._assemble_json()
        return self._dvJson

    #taken from transfer.py
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
            fileList = requests.get(f'{constants.DRYURL}/api/v2/versions/{self.id}/files', 
                                    headers=headers,
                                    timeout=timeout)
            fileList.raise_for_status()
            self._fileJson = fileList.json()
        return self._fileJson 

    #also taken from transfer.py
    @property
    def files(self):
        '''
        Returns a list of tuples with:
        (Download_location, filename, mimetype, size, description)

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
                descr = f.get('description', '') #HOW ABOUT PUTTING THIS IN THE DRYAD API PAGE?
                out.append((downLink, name, mimeType, size, descr))

        return out

    @property
    def oversize(self, maxsize=None):
        if not maxsize:
            maxsize = constants.MAX_UPLOAD
        toobig=[]
        for f in self.files:
            if f[3] >= maxsize:
                toobig.append(f)
        return toobig



    def _typeclass(self, typeName, multiple, typeClass):
        '''
        Creates wrapper around single or multiple Dataverse JSON objects.
        Returns a dict *without* the 'value' key'
        
        typeName : str
            Dataverse typeName (eg: 'author')
        multiple : boolean
        typeClass : str
            Dataverse typeClass. Usually one of 'compound', 'primitive, 'controlledVocabulary')
        '''
        return {'typeName':typeName, 'multiple':multiple, 'typeClass':typeClass}

    def _convert_generic(self, **kwargs):
        '''
        Generic json creator of form:
            {dvField:
                {'typeName': dvField,
                  'value': dryField}
        Suitable for generalized conversions. Only provides fields with multiple: False and typeclass:Primitive
            
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
            Notes to be prepended to list type values. No trailing space required.
        '''

        dvField = kwargs.get('dvField')
        dryField = kwargs.get('dryField')
        inJson = kwargs.get('inJson')
        addJson = kwargs.get('addJson')
        pNotes = kwargs.get('pNotes', '')
        rType = kwargs.get('rType', 'dict')
        if not dvField or not dryField or not inJson:
            raise TypeError('Incorrect or insufficient fields provided')
        outfield = inJson.get(dryField)
        if outfield: outfield = outfield.strip()
        '''
        if not outfield:
            raise ValueError(f'Dryad field {dryField} not found')
        '''
        # If value missing can still concat empty dict
        if not outfield: return {}
        if rType == 'list':
            if pNotes:
                outfield = [f'{pNotes} {outfield}'] 
       
        outJson = {dvField:
                        {'typeName':dvField,
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
        Produces required author json fields. Special csase, requires concatenation of several fields
        author : dict
            dryad['author'] JSON segment
        '''
        first = author.get('firstName')
        last = author.get('lastName')
        if first + last == None:
            return None
        authname = f"{author.get('lastName','')}, {author.get('firstName', '')}"
        return {'authorName':{'typeName':'authorName', 'value': authname, 'multiple':False, 'typeClass':'primitive'}}
    
    def _convert_keywords(self, *args):
        '''
        Produces the insane keyword structure from a list of words
        args : list with str elements
            remember to expand with *
        General input is Dryad JSON 'keywords', ie *Dryad['keywords']
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
                if note =='versionNumber':
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
        Makes a dataverse bounding box from appropriate coordinates. Returns dataverse json

        north, south, east, west | float
        Coordinates in decimal degrees.
        '''
        names = ['north', 'south', 'east', 'west']
        points = [str(x) for x in [north, south, east, west]]#Because coordinates in DV are strings BFY
        coords = [(x[0]+'Longitude', {x[0]:x[1]}) for x in zip(names, points)]#Yes, everything is longitude
        out = []
        for c in coords:
            out.append(self._convert_generic(inJson=c[1],
                                             dvField=c[0],
                                             #dryField='north'))
                                             dryField=[k for k in c[1].keys()][0]))
        return out

    def _convert_geospatial(self, dryJson):
        '''
        Outputs Dataverse geospatial metadata block.
        Requires internet connection to connect to https://geonames.org
        dryJson : dict
            Dryad json as dict
        '''
        if dryJson.get('locations'):
            out ={}
            coverage = []
            box = []
            otherCov = None
            gbbox = None
            for loc in dryJson.get('locations'):
                if loc.get('place'):
                    '''These are impossible to clean. Going to "other" field"'''

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
                    west =  loc['box']['swLongitude']
                    area = self._boundingbox(north, south, east, west)
                    box.append(area)

            if coverage:
                otherCov = self._typeclass(typeName='geographicCoverage', multiple=True, typeClass='compound')
                otherCov['value'] = coverage

            if box:
                gbbox = self._typeclass(typeName='geographicCoverage', multiple=True, typeClass='compound')
                gbbox['value'] = box

            if otherCov or gbbox:
                gblock = {'geospatial': {'displayName' : 'Geospatial Metadata',
                                         'fields': []}}
                if otherCov:
                    gblock['geospatial']['fields'].append(otherCov)
                if gbbox:
                    gblock['geospatial']['fields'].append(gbbox)
            return gblock
        else:
            return{}
        
    def _assemble_json(self, dryJson=None, dvContact=None, dvEmail=None, defContact=True):
        '''
        Assembles Dataverse json from Dryad JSON components

        dryJson : dict
            Dryad json as dict
        dvContact : str 
            default Dataverse contact name
        dvEmail : str
            default Dataverse 4 contact email address
        defContact : boolean
            include default contact information with record
        '''
        if not dvContact:
            dvContact = constants.DV_CONTACT_NAME
        if not dvEmail:
            dvEmail = constants.DV_CONTACT_EMAIL
        if not dryJson:
            dryJson = self.dryadJson
        #print(dryJson)
        self._dvJson ={'datasetVersion':
                {'license':'CC0',
                 'termsOfUse': 'CC0 Waiver',
                 'metadataBlocks':{'citation':
                                    {'displayName': 'Citation Metadata',
                                      'fields': []},
                                   
                                   }
                 }
                }
        '''
        REQUIRED Dataverse fields

        Dryad is a general purpose database; it is hard/impossible to get
        Dataverse required subject tags out of their keywords, so:
        '''
        defaultSubj = {'typeName' : 'subject', 
                       'typeClass':'controlledVocabulary',
                       'multiple': True,
                       'value' : ['Other']}
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(defaultSubj) 

        reqdTitle = self._convert_generic(inJson=dryJson,
                                         dryField='title',
                                         dvField='title')['title']
        
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(reqdTitle) 
       
        ##rewrite as function: authors
        out = []
        for a in dryJson['authors']:
            reqdAuthor = self._convert_author_names(a)
            if reqdAuthor:
                affiliation = self._convert_generic(inJson=a, 
                                                dvField='authorAffiliation',
                                                dryField='affiliation')
                addOrc={'authorIdentifierScheme': 
                {'typeName':'authorIdentifierScheme', 
                    'value': 'ORCID',
                    'typeClass': 'controlledVocabulary',
                    'multiple':False}}
                #only ORCID at UBC
                orcid = self._convert_generic(inJson=a, 
                                                dvField='authorIdentifier',
                                                dryField='orcid',
                                                addJson=addOrc)
                if affiliation: reqdAuthor.update(affiliation)
                if orcid: reqdAuthor.update(orcid)
                out.append(reqdAuthor)

        authors= self._typeclass(typeName='author', multiple=True, typeClass='compound')
        authors['value'] = out

        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(authors)


        ##rewrite as function:contact
        out = []
        for e in dryJson['authors']:
            reqdContact=self._convert_generic(inJson=e, 
                                              dvField='datasetContactEmail', 
                                              dryField='email')
            if reqdContact:
                author = self._convert_author_names(e)
                author = {'author':author['authorName']['value']}#for passing to function
                author = self._convert_generic(inJson=author,
                                               dvField='datasetContactName',
                                               dryField='author')
                if author: reqdContact.update(author)
                affiliation = self._convert_generic(inJson=e, 
                                                dvField='datasetContactAffiliation',
                                                dryField='affiliation')
                if affiliation: reqdContact.update(affiliation)
                out.append(reqdContact)

        if defContact: #Adds default contact information the tail of the list
            defEmail = self._convert_generic(inJson={'em':dvEmail},
                                             dvField='datasetContactEmail',
                                             dryField='em')
            defName = self._convert_generic(inJson={'name':dvContact},
                                            dvField='datasetContactName',
                                            dryField='name')
            defEmail.update(defName)
            out.append(defEmail)

        contacts = self._typeclass(typeName='datasetContact', multiple=True, typeClass='compound')
        contacts['value'] = out
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(contacts)

        #Description
        description = self._typeclass(typeName='dsDescription', multiple=True, typeClass='compound')
        desCat =[('abstract','<b>Abstract</b><br/>'),
                  ('methods','<b>Methods</b><br />'), 
                  ('usageNotes','<b>Usage notes</b><br />')]
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
        '''
        #Add original DOI to description as well
        #Decided to move it to Agency
        formattedDoi = '<b>Dryad DOI:</b><br />' + self.dryadJson['identifier']+ '\n'
        origDoi = self._convert_generic(inJson={'doi':formattedDoi},
                                       dvField='dsDescriptionValue',
                                       dryField='doi')
        descDate = self._convert_generic(inJson=dryJson,
                                         dvField='dsDescriptionDate',
                                         dryField='lastModificationDate')
        origDoi.update(descDate)
        out.append(origDoi)
        '''
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
            grants = self._typeclass(typeName='grantNumber', multiple=True, typeClass='compound')
            grants['value'] = out 
            self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(grants)
        
        #Keywords
            keywords = self._typeclass(typeName='keyword', multiple=True, typeClass='compound')
            out = []
            for key in dryJson.get('keywords', []): #Apparently keywords are not required
                keydict = {'keyword':key}#because takes a dict
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
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(moddate['dateOfDeposit'])#This one isn't nested BFY
        
        #distribution date
        distdate = self._convert_generic(inJson=dryJson,
                                            dvField='distributionDate',
                                            dryField='publicationDate')
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(distdate['distributionDate'])#Also not nested

        #publications
        publications = self._typeclass(typeName='publication', multiple=True, typeClass='compound')
        #quick and dirty lookup tabls
        lookup = {'IsDerivedFrom':'Is derived from', 'Cites':'Cites', 'IsSupplementTo': 'Is supplement to', 'IsSupplementedBy': 'Is supplmented by'}
        out=[]
        if dryJson.get('relatedWorks'):
            for r in dryJson.get('relatedWorks'):
                id = r.get('identifier')
                relationship = r.get('relationship')
                idType = r.get('identifierType')
                citation = {'citation': f"{lookup[relationship]}: {id}"}

                pubcite = self._convert_generic(inJson=citation,
                                                dvField='publicationCitation',
                                                dryField='citation')
                pubIdType = self._convert_generic(inJson=r,
                                                  dvField='publicationIDType',
                                                  dryField='identifierType')
                #ID type must be lower case
                pubIdType['publicationIDType']['value'] =  pubIdType['publicationIDType']['value'].lower()
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
        agency = self._typeclass(typeName='otherId', multiple=True, typeClass='compound')
        agency['value'] = [doi]
        self._dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(agency)
        
