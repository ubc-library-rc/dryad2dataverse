from nose.tools import *
import copy
import json
import os
import pickle
import sqlite3
import  dryad2dataverse.serializer
import  dryad2dataverse.transfer
import  dryad2dataverse.monitor

#Don't rely on relative path for loading files
fprefix = os.path.dirname(os.path.realpath(__file__))+os.sep

testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
#with open(f'{fprefix}dryad_dummy_metadata.json') as f:
#    testCase._dryadJson = json.load(f)
#montest = dryad2dataverse.monitor.Monitor('/Users/paul/tmp/wtf.db')
montest = dryad2dataverse.monitor.Monitor(':memory:')
#######
## Dryad JSON changes all the time. Replace this JSON with a current one if you get errors.
#######
#with open(f'{fprefix}dryad_files_orig.json') as f:
#with open(f'{fprefix}2rbnzs7jp_14Jan22.json') as f:
#    testCase._fileJson = json.load(f)

def setup():
    print( "Start test")

def teardown():
    print( "Finish ")

#@with_setup(setup, teardown)
#@params(testCase)jj
def test_file_id():
    ftest = dryad2dataverse.transfer.Transfer(testCase)
    assert_equal(testCase.files, [tuple(x) for x in ftest.files], True)
    #FILE IDS change. This is for 14 Jan 2022
    assert_equal(267417, ftest._dryad_file_id(ftest.files[0][0]), True)

def test_newmeta():
    diff = montest.status(testCase)
    assert_equal(diff['status'], 'new', True)

def test_identical_meta():
    lastmod = testCase.dryadJson['lastModificationDate']
    dvjson = {'dvdata' : 'no dv data'}
    dvjson = json.dumps(dvjson)
    montest.cursor.execute('INSERT INTO dryadStudy VALUES (?, ?, ?, ?,?)',
                        (1,testCase.dryadJson['identifier'],lastmod, json.dumps(testCase.dryadJson), dvjson))
    montest.cursor.execute('INSERT INTO dryadFiles VALUES (?,?)', (1, json.dumps(testCase.fileJson)))
    montest.cursor.execute('INSERT INTO dvStudy VALUES (?,?)', (1, "hdl:AB2/TESTHANDLE"))
    diff = montest.status(testCase)
    assert_equal(diff['status'], 'identical', True)

def test_lastmodsame():
    visi = testCase.dryadJson['visibility']
    testCase.dryadJson['visibility'] = 'VISIBILITY CHANGED'
    diff = montest.status(testCase)
    assert_equal(diff['status'], 'lastmodsame', True)
    assert_equal(diff['notes'], 'metadata_changed', True)
    testCase.dryadJson['visibility'] = visi

def test_changed_date():
    ordate = testCase.dryadJson['lastModificationDate']
    testCase.dryadJson['lastModificationDate'] = '1941-12-07'
    diff = montest.status(testCase)
    assert_equal(diff['status'], 'updated', True)
    testCase.dryadJson['lastModificationDate'] = ordate

def test_unchanged_files():
    doi = testCase.doi
    montest.cursor.execute('SELECT uid from dryadStudy WHERE doi = ?',(doi,))
    dryuid = montest.cursor.fetchone()[0]
    djson = json.dumps(testCase.fileJson)
    montest.cursor.execute('DELETE  FROM  dryadFiles WHERE dryaduid = ?', (dryuid, ))
    montest.cursor.execute('INSERT INTO dryadFiles VALUES (?, ?)', (dryuid, djson))
    diff = montest.status(testCase)
    assert_equal(diff['status'], 'identical', True)
    diff = montest.diff_files(testCase)
    assert_equal.__self__.maxDiff = None
    assert_equal({}, diff, True)

def test_added_files():
    assert_equal.__self__.maxDiff = None
    newdata=copy.copy(testCase.fileJson[0]['_embedded']['stash:files'][-1])
    newdata['path'] = 'ubc_rand1.csv'
    newdata['description'] = 'UBC random data 1'
    newdata['digestType'] = 'md5'
    newdata['digest'] = '6f953c01804e4fc8ec97f7c45d8259b8'
    testCase.fileJson[0]['_embedded']['stash:files'].append(newdata)
    #print(testCase.files)
    diff = montest.diff_files(testCase)
    assert_not_equal({}, diff)
    expect = {'add': [( 'ubc_rand1.csv',
           'text/plain',
           1350,
           'UBC random data 1', 
           'md5',
           '6f953c01804e4fc8ec97f7c45d8259b8')]}
    assert_equal(expect, diff)
    #restore state
    del testCase.fileJson[0]['_embedded']['stash:files'][-1]
     

def test_deleted_files():
    newdata=copy.copy(testCase.fileJson[0]['_embedded']['stash:files'][0])
    del testCase.fileJson[0]['_embedded']['stash:files'][0]
    diff = montest.diff_files(testCase)
    assert_not_equal({}, diff)
    expect = {'delete': [('GCB_ACG_Mortality_2020.zip',
           'application/x-zip-compressed',
           23787587,
           '',
           '', '')]}
    assert_equal.__self__.maxDiff = None 
    assert_equal(expect, diff)
    #and restore
    testCase.fileJson[0]['_embedded']['stash:files'].insert(0,newdata)

def test_added_hash():
    testCase.fileJson[-1]['_embedded']['stash:files'][-1]['digestType']='md5'
    testCase.fileJson[-1]['_embedded']['stash:files'][-1]['digest']='6c994262e3e31a972ba63b4e07f0test'
    diff = montest.diff_files(testCase)
    assert_equal.__self__.maxDiff = None 
    assert_not_equal({}, diff)
    print(diff)
    assert_equal(diff, {'hash_change' : 
        [x[1:] for x in testCase.files if x[-1].endswith('test')]})
    #restore state
    testCase._fileJson = None

def test_no_transfer():
    ftest = dryad2dataverse.transfer.Transfer(testCase)
    assert_equal(ftest.fileUpRecord,  [])
    assert_equal(ftest.fileDelRecord, [])

#def test_uploaded_transfer():
#    ftest = dryad2dataverse.transfer.Transfer(testCase)
#    ftest.fileUpRecord.append((385819, json.dumps({'dvn':'simulatedJson'})))
#
#
