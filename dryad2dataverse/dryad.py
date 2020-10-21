'''Import and convert dryad metadata'''

class Dryad(object):
    def __init__(self, doi):
        '''
        doi : str
            DOI of Dryad study. Required for downloading
        '''
        self.doi = doi
        self._dryadJson = None
    
    def fetch_record(self):
        '''
        Download Dryad JSON and save to Dryad.dryadJson
        '''
        pass

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
            JSON segment to convert
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
            dryad['author']
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

        '''
        outlist = []
        for arg in args:
            outlist.append({'keywordValue': {
                'typeName':'keywordValue',
                'value': arg}})
        return outlist

    def _convert_notes(self, dryJson):
        #multiple fields must be concatenated into one.
        notes = ''
        #these fields should be concatenated into notes
        notable = ['versionNumber', 'manuscriptNumber',
                   'usageNotes', 'methods','preserveCurationStatus',
                   'invoiceId']
        for note in notable:
            text = dryJson.get(note)
            if text:
                if note =='versionNumber':
                    text = f'Dryad version number: {text}'
                if note == 'manuscriptNumber':
                    text == f'Manuscript number: {text}'
                if note == 'preserveCurationStatus':
                    text = f'Preserve curation status: {text}'
                if note == 'invoiceId':
                    text == f'Invoice ID: {text}'
                text = text.strip()
                notes += f'<p>{text}</p>\n'
        concat = {'typeName':'notesText',
                  'value': notes}
        return concat

    def _assemble_json(self, dryJson=None):
        '''
        Assembles Dataverse json from Dryad components

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
        descrField = self._convert_generic(inJson=dryJson, dvField='dsDescriptionValue', dryField='abstract')
        description['value'] = [descrField] ##FFFFUUUU
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
            for key in dryJson['keywords']:
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

        #distribution date
        moddate = self._convert_generic(inJson=dryJson,
                                            dvField='dateOfDeposit',
                                            dryField='lastModificationDate')
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(moddate)

        #distribution date
        distdate = self._convert_generic(inJson=dryJson,
                                            dvField='distributionDate',
                                            dryField='publicationDate')
        self.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'].append(distdate)

        ##TODO create minimal JSON as test for upload
        
