from nose.tools import *
import sqlite3
import json
import pickle
import  dryad2dataverse.serializer
import  dryad2dataverse.transfer
import  dryad2dataverse.monitor

testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
with open('./tests/dryad_dummy_metadata.json') as f:
    testCase._dryadJson = json.load(f)
montest = dryad2dataverse.monitor.Monitor(':memory:')
with open('tests/dryad_files_orig.json') as f:
    testCase._fileJson=json.load(f)
def setup():
    print( "Start test")

def teardown():
    print( "Finish ")

#@with_setup(setup, teardown)
#@params(testCase)
def test_file_id():
    dryad = testCase

    files=[('https://datadryad.org/api/v2/files/385819/download', 'ubc_rand1.zip', 'application/x-zip-compressed', 23787587, ''), ('https://datadryad.org/api/v2/files/385820/download', 'ubc_rand2.csv', 'text/plain', 1350, '')]

    ftest = dryad2dataverse.transfer.Transfer(dryad)
    assert_equal(files, ftest.files, True)
    assert_equal(385819, ftest._dryad_file_id(ftest.files[0][0]), True)

def test_newmeta():
    diff =montest.status(testCase)
    assert_equal(diff['status'], 'new', True)

def test_same_meta():
    lastmod = testCase.dryadJson['lastModificationDate']
    dvjson = {'dvdata' : 'no dv data'}
    dvjson = json.dumps(dvjson)
    montest.cursor.execute('INSERT INTO dryadStudy VALUES (?, ?, ?, ?,?)',
                        (1,testCase.dryadJson['identifier'],lastmod, json.dumps(testCase.dryadJson), dvjson))
    montest.cursor.execute('INSERT INTO dryadFiles VALUES (?,?)', (1, json.dumps(testCase.fileJson)))
    montest.cursor.execute('INSERT INTO dvStudy VALUES (?,?)', (1, "hdl:AB2/TESTHANDLE"))
    diff =montest.status(testCase)
    assert_equal(diff['status'], 'unchanged', True)

def test_changed_date():
    testCase.dryadJson['lastModificationDate']='1941-12-07'
    diff =montest.status(testCase)
    assert_equal(diff['status'], 'filesonly', True)


def test_changed_meta():
    testCase.dryadJson['lastModificationDate']='1941-12-07'
    testCase.dryadJson['title'] += ' :Updated for testing'
    diff =montest.status(testCase)
    assert_equal(diff['status'], 'updated', True)

def test_unchanged_files():
    '''
    doi = testCase.dryadJson['identifier']
    montest.cursor.execute('SELECT uid from dryadStudy WHERE doi = ?',(doi))
    dryuid = montest.cursor.fetchone()[0]
    djson = json.dumps(testCase.dryadJson)
    #montest.cursor.execute('INSERT INTO dryadFiles VALUES (?, ?)', (,))
    '''
    diff = montest.diff_files(testCase)
    assert_equal({}, diff, True)

def test_added_files():
    with open('tests/dryad_files_added.json') as f:
        new = json.load(f)
    testCase._fileJson = new
    diff = montest.diff_files(testCase)
    assert_not_equal({}, diff)
    expect = {'add': [('https://datadryad.org/api/v2/files/385820/download',
           'ubc_rand3.csv',
           'application/octet-stream',
           1350,
           'A third csv with a description')]}
    assert_equal.__self__.maxDiff = None
    assert_equal(expect, diff)
    
def test_deleted_files():
    with open('tests/dryad_files_deleted.json') as f:
        new = json.load(f)
        testCase._fileJson = new
    diff = montest.diff_files(testCase)
    assert_not_equal({}, diff)
    expect = {'delete': [('https://datadryad.org/api/v2/files/385819/download',
           'ubc_rand1.zip',
           'application/x-zip-compressed',
           23787587,
           '')]}
    assert_equal.__self__.maxDiff = None
    assert_equal(expect, diff)

def test_no_transfer():
    ftest = dryad2dataverse.transfer.Transfer(testCase)
    assert_equal(ftest.fileUpRecord,  [])
    assert_equal(ftest.fileDelRecord, [])

def test_uploaded_transfer():
    ftest = dryad2dataverse.transfer.Transfer(testCase)
    ftest.fileUpRecord.append((385819, json.dumps({'dvn':'simulatedJson'})))
    

