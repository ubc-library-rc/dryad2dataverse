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

def setup():
    print( "Start test")

    def teardown():
        print( "Finish ")


@with_setup(setup)
def test_abstract():
    abstract = '<p>Drought-related tree mortality is now a widespread phenomenon predicted to increase in magnitude with climate change. However, the patterns of which species and trees are most vulnerable to drought, and the underlying mechanisms have remained elusive, in part due to the lack of relevant data and difficulty of predicting the location of catastrophic drought years in advance. We used long‐term demographic records and extensive databases of functional traits and distribution patterns to understand the responses of 20 to 53 species to an extreme drought in a seasonally dry tropical forest in Costa Rica, which occurred during the 2015 El Niño Southern Oscillation event. Overall, species-specific mortality rates during the drought ranged from 0% to 34%, and varied little as a function of tree size. By contrast, hydraulic safety margins correlated well with probability of mortality among species, while morphological or leaf economics spectrum traits did not. This firmly suggests hydraulic traits as targets for future research.</p>\r\n'

    abs = {'dsDescriptionValue': 
            {'typeName':'dsDescriptionValue', 
              'value':abstract}}
    assert_equal(isinstance(testCase.dryJson['abstract'], str), True)
    assert_equal(testCase._convert_abstract(testCase.dryJson['abstract']), abs)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson, dvField='dsDescriptionValue', dryField='abstract'), abs)

def test_author():
    #dvAuthor = json.loads("{'authorName':{'typeName':'authorName', 'value': 'Powers, Jennifer'}}")
    dvAuthor = {'authorName':{'typeName':'authorName', 'value': 'Powers, Jennifer'}}
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_author_names(testCase.dryJson['authors'][0]), dvAuthor)

def test_email():
    email = {'datasetContactEmail': 
            {'typeName':'datasetContactEmail',
                'value':'powers@umn.edu'}}
    isinstance(testCase.dryJson['authors'][0], dict)
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_email(testCase.dryJson['authors'][0]), email)


def test_orcid():
    orcid = {'authorIdentifierScheme': 
               {'typeName':'authorIdentifierScheme', 'value': 'ORCID'},
               'authorIdentifier': {'typeName':'authorIdentifier','value':'0000-0003-3451-4803'}
               }
    isinstance(testCase.dryJson['authors'][0], dict)
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_orcid(testCase.dryJson['authors'][0]),orcid)

def test_affiliation():
    affil = {'authorAffiliation': 
               {'typeName':'authorAffiliation', 'value': 'University of Minnesota'}
            }
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_affiliation(testCase.dryJson['authors'][0]),affil)

def test_generic():
    #Test on affiliation
    out = {'authorAffiliation':{'typeName':'authorAffiliation', 'value':'University of Minnesota'}}
    assert_equal(isinstance(testCase.dryJson['authors'][0], dict), True)
    assert_equal(testCase._convert_generic(inJson=testCase.dryJson['authors'][0], 
                dvField='authorAffiliation',
                dryField='affiliation'), out)
