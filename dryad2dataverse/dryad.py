'''Import and convert dryad metadata'''
import urllib.parse
import requests

#TODO rename class to Serializer
class Dryad(object):
    def __init__(self, doi):
        '''
        doi : str
            DOI of Dryad study. Required for downloading
        '''
        self.doi = doi
        self._dryadJson = None

    def fetch_record(self, timeout=45):
        '''
        Fetches Dryad study record JSON from Dryad V2 API at https://datadryad.org/api/v2/datasets/
        Saves to Dryad._dryadJson

        timeout : int
            timeout in seconds. Default 45
        '''

        headers = {'accept':'application/json', 'Content-Type':'application/json'}
        doiClean = urllib.parse.quote(self.doi, safe='')
        resp = requests.get(f'https://datadryad.org/api/v2/datasets/{doiClean}',
                            headers=headers, timeout=timeout)
        resp.raise_for_status()
        self._dryadJson = resp.json() 

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
        
    def assemble_json(self, dryJson=None):
        '''
        Assembles Dataverse json from Dryad JSON components

        dryJson : dict
            Dryad json as dict
        '''
        if not dryJson:
            dryJson = self._dryadJson
        #print(dryJson)
        self.dvJson ={'datasetVersion':
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
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(defaultSubj) 

        reqdTitle = self._convert_generic(inJson=dryJson,
                                         dryField='title',
                                         dvField='title')['title']
        
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(reqdTitle) 
       
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

        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(authors)


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
        contacts = self._typeclass(typeName='datasetContact', multiple=True, typeClass='compound')
        contacts['value'] = out
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(contacts)

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
        description['value'] = out
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(description)

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
            self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(grants)
        
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
            self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(keywords)
        #modification date
        moddate = self._convert_generic(inJson=dryJson,
                                            dvField='dateOfDeposit',
                                            dryField='lastModificationDate')
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(moddate['dateOfDeposit'])#This one isn't nested BFY
        
        #distribution date
        distdate = self._convert_generic(inJson=dryJson,
                                            dvField='distributionDate',
                                            dryField='publicationDate')
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(distdate['distributionDate'])#Also not nested

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
                pubcite.update(pubIdType)
                pubcite.update(pubUrl)
                out.append(pubcite)
        publications['value'] = out
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(publications)
        #notes
        #go into primary notes field, not DDI
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(self._convert_notes(dryJson))

        #Geospatial metadata
        self.dvJson['datasetVersion']['metadataBlocks'].update(self._convert_geospatial(dryJson))

