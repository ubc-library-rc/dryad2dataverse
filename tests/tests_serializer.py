import unittest
import os
import sqlite3
import json
import pickle
import pathlib

import  dryad2dataverse.serializer as dryad

BADURL = pathlib.Path(pathlib.Path(__file__).parent, 'badURL.json')

class TestSerialize(unittest.TestCase): 
    #@classmethod
    #def setUp(cls):
    #    #testing Dryad json 14 January 2022
    #    #This JSON is found at ./2rbnzs7jp_14Jan22.json
    #    cls.testCase = dryad.Serializer('doi:10.5061/dryad.2rbnzs7jp')
    #    #with open('tests/dryadStudy.json') as f:
    #    #    testCase._dryadJson = json.load(f)

    def setUp(self):
        self.testCase = dryad.Serializer('doi:10.5061/dryad.2rbnzs7jp')
        self.NULLVALUES= {x[0]: None for x in self.testCase.dryadJson['authors'][0].items()}
        self.NOMULT ={'multiple':False, 'typeClass':'primitive'}

    def tearDown(self):
        self.testCase.session.close()


    def test_generic(self):
        #Test on affiliation
        out = {'authorAffiliation':{'typeName':'authorAffiliation', 'value':'University of Minnesota', 'multiple':False, 'typeClass':'primitive'}}
        self.assertEqual(isinstance(self.testCase.dryadJson['authors'][0], dict), True)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson['authors'][0], 
                    dvField='authorAffiliation',
                    dryField='affiliation'), out)

        # Test self.NULLVALUES
        self.assertEqual(self.testCase._convert_generic(inJson=self.NULLVALUES,
                    dvField='authorAffiliation',
                    dryField='affiliation'), {})
        self.testCase.session.close()

    def test_abstract(self):
        self.assertEqual.__self__.maxDiff = None
        abstract = '<p>Drought-related tree mortality is now a widespread phenomenon predicted to increase in magnitude with climate change. However, the patterns of which species and trees are most vulnerable to drought, and the underlying mechanisms have remained elusive, in part due to the lack of relevant data and difficulty of predicting the location of catastrophic drought years in advance. We used long‐term demographic records and extensive databases of functional traits and distribution patterns to understand the responses of 20 to 53 species to an extreme drought in a seasonally dry tropical forest in Costa Rica, which occurred during the 2015 El Niño Southern Oscillation event. Overall, species-specific mortality rates during the drought ranged from 0% to 34%, and varied little as a function of tree size. By contrast, hydraulic safety margins correlated well with probability of mortality among species, while morphological or leaf economics spectrum traits did not. This firmly suggests hydraulic traits as targets for future research.</p>'

        abs = {'dsDescriptionValue': 
                {'typeName':'dsDescriptionValue', 
                  'value':abstract, 'multiple':False, 'typeClass':'primitive'}}
        self.assertEqual(isinstance(self.testCase.dryadJson['abstract'], str), True)
        #self.assertEqual(self.testCase._convert_abstract(self.testCase.dryadJson['abstract']), abs)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson, dvField='dsDescriptionValue', dryField='abstract'), abs)

    def test_version(self):
        self.assertEqual(True, isinstance(self.testCase.dryadJson['versionNumber'], int))
        #removed 
        #self.assertEqual(True, isinstance(self.testCase.version, int))
        self.testCase.session.close()


    def test_author(self):
        #dvAuthor = json.loads("{'authorName':{'typeName':'authorName', 'value': 'Powers, Jennifer'}}")
        dvAuthor = {'authorName':{'typeName':'authorName', 'value': 'Powers, Jennifer','multiple':False, 'typeClass':'primitive'}}
        self.assertEqual(isinstance(self.testCase.dryadJson['authors'][0], dict), True)
        self.assertEqual(self.testCase._convert_author_names(self.testCase.dryadJson['authors'][0]), dvAuthor)

    def test_email(self):
        email = {'datasetContactEmail': 
                {'typeName':'datasetContactEmail',
                    'value':'powers@umn.edu','multiple':False, 'typeClass':'primitive'}}
        isinstance(self.testCase.dryadJson['authors'][0], dict)
        #self.assertEqual(isinstance(self.testCase.dryadJson['authors'][0], dict), True)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson['authors'][0], dvField='datasetContactEmail', dryField='email'), email)

    def test_orcid(self):
        addJson={'authorIdentifierScheme': 
                    {'typeName':'authorIdentifierScheme', 
                        'value': 'ORCID',
                        'typeClass': 'controlledVocabulary',
                        'multiple':False}}


        orcid = {'authorIdentifier': {'typeName':'authorIdentifier','value':'0000-0003-3451-4803','multiple':False, 'typeClass':'primitive'}}
        orcid.update(addJson)
        isinstance(self.testCase.dryadJson['authors'][0], dict)
        self.assertEqual(isinstance(addJson, dict),True)
        self.assertEqual(isinstance(self.testCase.dryadJson['authors'][0], dict), True)
        #self.assertEqual(self.testCase._convert_orcid(self.testCase.dryadJson['authors'][0]),orcid)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson['authors'][0], dvField='authorIdentifier', dryField='orcid', addJson=addJson),orcid)

    def test_affiliation(self):
        affil = {'authorAffiliation': 
                   {'typeName':'authorAffiliation', 'value': 'University of Minnesota'}
                }
        affil['authorAffiliation'].update(self.NOMULT)
        self.assertEqual(isinstance(self.testCase.dryadJson['authors'][0], dict), True)
        #self.assertEqual(self.testCase._convert_affiliation(self.testCase.dryadJson['authors'][0]),affil)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson['authors'][0], dvField='authorAffiliation', dryField='affiliation'),affil)

    def test_isni(self):
        '''Dryad has no ISNI'''
        addJson={'authorIdentifierScheme': 
                    {'typeName':'authorIdentifierScheme', 
                        'value': 'ISNI'}}
        addJson['authorIdentifierScheme'].update(self.NOMULT)

        ident = {'authorIdentifier': {'typeName':'authorIdentifier','value':'0000-0003-3451-4803'}
                   }
        ident['authorIdentifier'].update(self.NOMULT)
           
        self.assertEqual(isinstance(addJson, dict),True)
        self.assertEqual(isinstance(self.testCase.dryadJson['authors'][0], dict), True)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson['authors'][0], dvField='authorIdentifier', dryField='affiliationISNI', addJson=addJson),{})

    def test_funders(self):
        funder = {'grantNumberValue': 
                   {'typeName':'grantNumberValue', 'value': 'CAREER grant DEB 1053237'}}
        funder['grantNumberValue'].update(self.NOMULT)
        self.assertEqual(isinstance(self.testCase.dryadJson['funders'][0], dict), True)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson['funders'][0], dvField='grantNumberValue', dryField='awardNumber') , funder)

    def test_doi(self):
        doi  = {'relatedDatasets': 
                {'typeName':'relatedDatasets', 'value': ['Original dataset in Dryad repository: doi:10.5061/dryad.2rbnzs7jp']}}
        doi['relatedDatasets'].update(self.NOMULT)
        pnotes= 'Original dataset in Dryad repository:'

        
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson, 
            dvField='relatedDatasets', 
            dryField='identifier', 
            addJson=None,
            pNotes=pnotes,
            rType='list'
            ), doi)

    def test_keyword(self):
        keywords=[
                #{'keywordValue':{'typeName':'keywordValue','value':'drought'}},
                #{'keywordValue':{'typeName':'keywordValue','value':'Tree mortality'}},
                {'keywordValue':{'typeName':'keywordValue','value':'Costa Rica'}}
                ]

        self.assertEqual(isinstance(self.testCase.dryadJson['keywords'], list), True)
        self.assertEqual(self.testCase._convert_keywords(*self.testCase.dryadJson['keywords']), keywords)

    def test_lastmod(self):
        lastmod= {'distributionDate': 
                {'typeName':'distributionDate',
                    'value':'2020-03-17'}.update(self.NOMULT)}

    def test_notes(self):
        self.assertEqual.__self__.maxDiff = None
        notes = {'typeName': 'notesText', 
                 'typeClass':'primitive',
                 'multiple':False,
                 'value': '<p><b>Dryad version number:</b> 4</p>\n<p><b>Version status:</b> submitted</p>\n<p><b>Dryad curation status:</b> Published</p>\n<p><b>Sharing link:</b> https://datadryad.org/stash/share/anFoRwjUzvjvpH8RA2T0mNipNsVst0s0N5mFzcTTcJE</p>\n<p><b>Storage size:</b> 23874866</p>\n<p><b>Visibility:</b> public</p>\n'}
        self.assertEqual(self.testCase._convert_notes(self.testCase.dryadJson), notes )

    def test_pub_date(self):
        pubdate = {'distributionDate': 
                   {'typeName':'distributionDate', 'value': '2020-03-17'}}
        pubdate['distributionDate'].update(self.NOMULT)

        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson, 
                dvField='distributionDate', 
                dryField='publicationDate') , pubdate)

    def test_issn(self):
        
        addJson = {'publicationIDType': 
                   {'typeName':'publicationIDType', 'value': 'issn'}}
        addJson['publicationIDType'].update(self.NOMULT)
        addJson['publicationIDType']['typeClass']='controlledVocabulary' #remember to do this
        issn = {'publicationIDNumber':
                {'typeName':'publicationIDNumber', 'value':'TEST'}}
        issn['publicationIDNumber'].update(self.NOMULT)

        self.testCase.dryadJson.update({'publicationISSN': 'TEST'})
        out = addJson.copy()
        out.update(issn)
        
        self.assertEqual(isinstance(out, dict), True)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson, 
            dvField='publicationIDNumber', 
            dryField='publicationISSN', 
            addJson=addJson,
            ), out)
        del self.testCase.dryadJson['publicationISSN']

    def test_title(self):
        #TITLES don't actually have the 'title' prepended BFY
        out= {'title': 
                {'typeName':'title',
                    'value':'A catastrophic tropical drought kills hydraulically vulnerable tree species'}}
        out['title'].update(self.NOMULT)
        self.assertEqual(self.testCase._convert_generic(inJson=self.testCase.dryadJson, 
            dvField='title', 
            dryField='title', 
            addJson=None,
            ), out)

    def test_bad_url(self):
        '''
        Dryad doesn't do validation checking on URLs, but may later
        So this reads a [currently] badly formatted URL and checks it.

        BADURL orginally came out of Dryad.
        '''
        fprefix = os.path.dirname(os.path.realpath(__file__))
        with open(BADURL) as f:
            dry = json.load(f)
        badJson = dryad.Serializer('irrelevant')
        badJson._dryadJson = dry
        dvurl = badJson.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'][9]['value'][0]['publicationURL']['value']
        #URL with https:// prepended
        url = 'https://www.github.com/wood-lab/Quinn_et_al_2021_Proc_B'
        self.assertEqual(dvurl, url)

    #def test_worse_url(self):
    #    '''
    #    Dryad doesn't do validation checking on URLs, but may later.
    #    This record has a URL with no data. 
    #    '''
    #    fprefix = os.path.dirname(os.path.realpath(__file__))
    #    with open(f'{fprefix}{os.sep}nullField.json') as f:
    #        dry = json.load(f)
    #    badJson = dryad.Serializer('irrelevant')
    #    badJson._dryadJson = dry
    #    dvurl = badJson.dvJson['datasetVersion']['metadataBlocks']['citation']['fields'][9]['value'][0]['publicationURL']['value']
    #    #URL with https:// prepended
    #    url = 'https://www.github.com/wood-lab/Quinn_et_al_2021_Proc_B'
    #    self.assertEqual(dvurl, url)
if __name__ == '__main__':
    unittest.main()
