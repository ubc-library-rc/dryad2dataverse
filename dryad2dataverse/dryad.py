'''Import and convert dryad metadata'''

TEST=2

class Dryad(object):
    def __init__(self, doi):
        '''
        doi : str
            DOI of Dryad study. Required for downloading
        '''
        self.doi = doi
        self.dryJson = None
    
    def _convert_abstract(self, abstract):
        '''
        abstract : str
            dryad['abstract']

        From examination of UBCs dois, abstract does not repeat.
        All data sets have one, so presumably it's mandatory
        '''
        return {'dsDescriptionValue':{'typeName':'dsDescriptionValue', 'value': abstract}}

    def _convert_author_names(self, author):
        '''
        Produces required author json fields
        author : dict
            dryad['author']
        '''
        first = author.get('firstName')
        last = author.get('lastName')
        if first + last == None:
            return None
        authname = f"{author.get('lastName','')}, {author.get('firstName', '')}"
        return {'authorName':{'typeName':'authorName', 'value': f'{authname}'}}
    
    def _convert_email(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''
        email = author.get('email')
        if not email: return None
        return  {'datasetContactEmail': 
            {'typeName':'datasetContactEmail',
                'value':email}}        

    def _convert_orcid(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''
        orcid = author.get('orcid')
        if not orcid: return None
        return {'authorIdentifierScheme': 
                {'typeName':'authorIdentifierScheme', 
                    'value': 'ORCID'},
               'authorIdentifier': 
               {'typeName':'authorIdentifier',
                   'value':'0000-0003-3451-4803'}
               }

    def _convert_affiliation(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''
        affiliation = author.get('affiliation')
        if not affiliation: return None
        return {'authorAffiliation': 
               {'typeName':'authorAffiliation', 'value': affiliation}
            }

    def _convert_isni(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_org(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_award(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_ident(self, author):
        '''
        Return DOI here
        author : dict
            dryad['author']
        '''

    def _convert_invoice_id(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_keywords(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_last_mod(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_license(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_locations(self, author):
        '''
        Geospatial data here. A nightmare
        author : dict
            dryad['author']
        '''

    def _convert_methods(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_pubdate(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_issn(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_pubname(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_relatedworks(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_links(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_title(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_usage_notes(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''

    def _convert_userid(self, author):
        '''
        This one may be useless
        author : dict
            dryad['author']
        '''

    def _convert_version_no(self, author):
        '''
        Produces email dataverse email json
        author : dict
            dryad['author']
        '''
