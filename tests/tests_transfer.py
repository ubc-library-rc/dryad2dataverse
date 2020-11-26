from nose.tools import *
import sqlite3
import json
import pickle
import  dryad2dataverse.serializer
import  dryad2dataverse.transfer


global testCase
testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
with open('tests/dryadStudy.json') as f:
    testCase._dryadJson = json.load(f)


def setup():
    print( "Start test")

def teardown():
    print( "Finish ")

#@with_setup(setup, teardown)
#@params(testCase)
def test_file_id():
    dryad = testCase
    files = [('https://datadryad.org/api/v2/files/385819/download', 'GCB_ACG_Mortality_2020.zip', 'application/x-zip-compressed', 23787587, ''), ('https://datadryad.org/api/v2/files/385820/download', 'Readme_ACG_Mortality.txt', 'text/plain', 1350, '')]
    ftest = dryad2dataverse.transfer.Transfer(dryad)
    assert_equal(files, ftest.files, True)
    assert_equal(385819, ftest._dryad_file_id(ftest.files[0][0]), True)
    
