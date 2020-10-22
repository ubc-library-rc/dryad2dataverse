from nose.tools import *
import sqlite3
import json
import pickle
import  dryad2dataverse.dryad as dryad

testCase = dryad.Dryad('doi:10.5061/dryad.2rbnzs7jp')
'''
conn = sqlite3.Connection('/Volumes/LBRY/Research Commons/DryadToSPDataverse/analysis/dryadInfo.db')
cursor=conn.cursor()
testCase.dryJson = json.loads(cursor.execute(f'SELECT json from dryadjson WHERE json like "%{testCase.doi}%"').fetchone()[0]) '''
with open('/Users/paul/Documents/Work/Projects/dryad2dataverse/tmp/one.pickle', 'rb') as f:
    testCase.dryJson = pickle.load(f)

NULLVALUES= {x[0]: None for x in testCase.dryJson['authors'][0].items()}

NOMULT ={'multiple':False, 'typeClass':'primitive'}

def setup():
    print( "Start test")

    def teardown():
        print( "Finish ")


def test_generic():
    #Test on affiliation
    out = {'authorAffiliation':{'typeName':'authorAffiliation', 'value':'University of Minnesota', 'multiple':False, 'typeClass':'primitive'}}
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['authors'][0], 
                dvField='authorAffiliation',
                dryField='affiliation'), out)

    # Test NULLVALUES
    assert_equal(testCase._convert_generic(inJson=NULLVALUES,
                dvField='authorAffiliation',
                dryField='affiliation'), {})


@with_setup(setup)
def test_abstract():
    assert_equal.__self__.maxDiff = None
    abstract = '<p>Drought-related tree mortality is now a widespread phenomenon predicted to increase in magnitude with climate change. However, the patterns of which species and trees are most vulnerable to drought, and the underlying mechanisms have remained elusive, in part due to the lack of relevant data and difficulty of predicting the location of catastrophic drought years in advance. We used long‐term demographic records and extensive databases of functional traits and distribution patterns to understand the responses of 20 to 53 species to an extreme drought in a seasonally dry tropical forest in Costa Rica, which occurred during the 2015 El Niño Southern Oscillation event. Overall, species-specific mortality rates during the drought ranged from 0% to 34%, and varied little as a function of tree size. By contrast, hydraulic safety margins correlated well with probability of mortality among species, while morphological or leaf economics spectrum traits did not. This firmly suggests hydraulic traits as targets for future research.</p>'

    abs = {'dsDescriptionValue': 
            {'typeName':'dsDescriptionValue', 
              'value':abstract, 'multiple':False, 'typeClass':'primitive'}}
    assert_equal(isinstance(testCase.dryJson['abstract'], str), True)
    #assert_equal(testCase._convert_abstract(testCase.dryJson['abstract']), abs)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson, dvField='dsDescriptionValue', dryField='abstract'), abs)

def test_author():
    #dvAuthor = json.loads("{'authorName':{'typeName':'authorName', 'value': 'Powers, Jennifer'}}")
    dvAuthor = {'authorName':{'typeName':'authorName', 'value': 'Powers, Jennifer','multiple':False, 'typeClass':'primitive'}}
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_author_names(testCase.dryJson['authors'][0]), dvAuthor)

def test_email():
    email = {'datasetContactEmail': 
            {'typeName':'datasetContactEmail',
                'value':'powers@umn.edu','multiple':False, 'typeClass':'primitive'}}
    isinstance(testCase.dryJson['authors'][0], dict)
    #assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['authors'][0], dvField='datasetContactEmail', dryField='email'), email)

def test_orcid():
    addJson={'authorIdentifierScheme': 
                {'typeName':'authorIdentifierScheme', 
                    'value': 'ORCID',
                    'typeClass': 'controlledVocabulary',
                    'multiple':False}}


    orcid = {'authorIdentifier': {'typeName':'authorIdentifier','value':'0000-0003-3451-4803','multiple':False, 'typeClass':'primitive'}}
    orcid.update(addJson)
    isinstance(testCase.dryJson['authors'][0], dict)
    assert_equal(isinstance(addJson, dict),True)
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    #assert_equal(testCase._convert_orcid(testCase.dryJson['authors'][0]),orcid)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['authors'][0], dvField='authorIdentifier', dryField='orcid', addJson=addJson),orcid)

def test_affiliation():
    affil = {'authorAffiliation': 
               {'typeName':'authorAffiliation', 'value': 'University of Minnesota'}
            }
    affil['authorAffiliation'].update(NOMULT)
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    #assert_equal(testCase._convert_affiliation(testCase.dryJson['authors'][0]),affil)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['authors'][0], dvField='authorAffiliation', dryField='affiliation'),affil)

def test_isni():
    '''Dryad has no ISNI'''
    addJson={'authorIdentifierScheme': 
                {'typeName':'authorIdentifierScheme', 
                    'value': 'ISNI'}}
    addJson['authorIdentifierScheme'].update(NOMULT)

    ident = {'authorIdentifier': {'typeName':'authorIdentifier','value':'0000-0003-3451-4803'}
               }
    ident['authorIdentifier'].update(NOMULT)
       
    assert_equal(isinstance(addJson, dict),True)
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['authors'][0], dvField='authorIdentifier', dryField='affiliationISNI', addJson=addJson),{})

def test_funders():
    funder = {'grantNumberValue': 
               {'typeName':'grantNumberValue', 'value': 'CAREER grant DEB 1053237'}}
    funder['grantNumberValue'].update(NOMULT)
    assert_equal(isinstance(testCase.dryJson['funders'][0], dict), True)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['funders'][0], dvField='grantNumberValue', dryField='awardNumber') , funder)

def test_doi():
    doi  = {'relatedDatasets': 
            {'typeName':'relatedDatasets', 'value': ['Original dataset in Dryad repository: doi:10.5061/dryad.2rbnzs7jp']}}
    doi['relatedDatasets'].update(NOMULT)
    pnotes= 'Original dataset in Dryad repository:'

    
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson, 
        dvField='relatedDatasets', 
        dryField='identifier', 
        addJson=None,
        pNotes=pnotes,
        rType='list'
        ), doi)

def test_keyword():
    keywords=[
            {'keywordValue':{'typeName':'keywordValue','value':'drought'}},
            {'keywordValue':{'typeName':'keywordValue','value':'Tree mortality'}},
            {'keywordValue':{'typeName':'keywordValue','value':'Costa Rica'}}
            ]

    assert_equal(isinstance(testCase.dryJson['keywords'], list), True)
    assert_equal(testCase._convert_keywords(*testCase.dryJson['keywords']), keywords)

def test_lastmod():
    lastmod= {'distributionDate': 
            {'typeName':'distributionDate',
                'value':'2020-03-17'}.update(NOMULT)}

def test_notes():
    assert_equal.__self__.maxDiff = None
    notes = {'typeName': 'notesText', 
             'typeClass':'primitive',
             'multiple':False,
             'value': '<p><b>Dryad version number:</b> 4</p>\n<p><b>Version status:</b> submitted</p>\n<p><b>Dryad curation status:</b> Published</p>\n<p><b>Sharing link:</b> https://datadryad.org/stash/share/anFoRwjUzvjvpH8RA2T0mNipNsVst0s0N5mFzcTTcJE</p>\n<p><b>Storage size:</b> 23874866</p>\n<p><b>Visibility:</b> public</p>\n'}
    assert_equal(testCase._convert_notes(testCase.dryJson), notes )

def test_pub_date():
    pubdate = {'distributionDate': 
               {'typeName':'distributionDate', 'value': '2020-03-17'}}
    pubdate['distributionDate'].update(NOMULT)

    assert_equal(testCase._convert_generic(inJson=testCase.dryJson, 
            dvField='distributionDate', 
            dryField='publicationDate') , pubdate)

def test_issn():
    
    addJson = {'publicationIDType': 
               {'typeName':'publicationIDType', 'value': 'issn'}}
    addJson['publicationIDType'].update(NOMULT)
    addJson['publicationIDType']['typeClass']='controlledVocabulary' #remember to do this
    issn = {'publicationIDNumber':
            {'typeName':'publicationIDNumber', 'value':'TEST'}}
    issn['publicationIDNumber'].update(NOMULT)

    testCase.dryJson.update({'publicationISSN': 'TEST'})
    out = addJson.copy()
    out.update(issn)
    
    assert_equal(isinstance(out, dict), True)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson, 
        dvField='publicationIDNumber', 
        dryField='publicationISSN', 
        addJson=addJson,
        ), out)
    del testCase.dryJson['publicationISSN']


def test_title():
    #TITLES don't actually have the 'title' prepended BFY
    out= {'title': 
            {'typeName':'title',
                'value':'A catastrophic tropical drought kills hydraulically vulnerable tree species'}}
    out['title'].update(NOMULT)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson, 
        dvField='title', 
        dryField='title', 
        addJson=None,
        ), out)


