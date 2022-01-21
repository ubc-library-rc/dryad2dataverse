from nose.tools import *
import sqlite3
import json
import pickle
import  dryad2dataverse.serializer
import  dryad2dataverse.transfer


global testCase
testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
#Dryad file IDS are not constant. In fact, almost nothing is constant so testing
#is hard
#Dryad json for test case on 14 Jan 2022 is 2rbnzs7jp_14Jan22.json 
#with open('tests/dryadStudy.json') as f:
#    testCase._dryadJson = json.load(f)


def setup():
    print( "Start test")

def teardown():
    print( "Finish ")

#@with_setup(setup, teardown)
#@params(testCase)
def test_file_id():
    '''
    Does file_id even matter? we found out in Dec 2021  that they're changeable.
    So this test constantly needs updating. Dammit.
    '''
    assert_equal.__self__.maxDiff = None
    files = [list(x) for x in testCase.files] 
    ftest = dryad2dataverse.transfer.Transfer(testCase)
    assert_equal(files, ftest.files, True)
    assert_equal(267417, ftest._dryad_file_id(ftest.files[0][0]), True)
    
