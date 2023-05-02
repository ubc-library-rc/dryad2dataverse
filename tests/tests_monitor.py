import unittest
import copy
import json
import os
import pickle
import sqlite3
import  dryad2dataverse.serializer
import  dryad2dataverse.transfer
import  dryad2dataverse.monitor

class TestMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
        cls.montest = dryad2dataverse.monitor.Monitor(':memory:')

    @classmethod
    def tearDownClass(cls):
        cls.testCase.session.close()

    def test_00_file_id(self):
        ftest = dryad2dataverse.transfer.Transfer(self.testCase)
        self.assertEqual(self.testCase.files, [tuple(x) for x in ftest.files], True)
        #FILE IDS change. This is for 14 Jan 2022
        self.assertEqual(267417, ftest._dryad_file_id(ftest.files[0][0]), True)

    def test_01_newmeta(self):
        diff = self.montest.status(self.testCase)
        self.assertEqual(diff['status'], 'new', True)

    def test_02_identical_meta(self):
        lastmod = self.testCase.dryadJson['lastModificationDate']
        dvjson = {'dvdata' : 'no dv data'}
        dvjson = json.dumps(dvjson)
        self.montest.cursor.execute('INSERT INTO dryadStudy VALUES (?, ?, ?, ?,?)',
                            (1,self.testCase.dryadJson['identifier'],lastmod, json.dumps(self.testCase.dryadJson), dvjson))
        self.montest.cursor.execute('INSERT INTO dryadFiles VALUES (?,?)', (1, json.dumps(self.testCase.fileJson)))
        self.montest.cursor.execute('INSERT INTO dvStudy VALUES (?,?)', (1, "hdl:AB2/TESTHANDLE"))
        diff = self.montest.status(self.testCase)
        self.assertEqual(diff['status'], 'identical', True)

    def test_03_lastmodsame(self):
        visi = self.testCase.dryadJson['visibility']
        self.testCase.dryadJson['visibility'] = 'VISIBILITY CHANGED'
        diff = self.montest.status(self.testCase)
        self.assertEqual(diff['status'], 'lastmodsame', True)
        self.assertEqual(diff['notes'], 'metadata_changed', True)
        self.testCase.dryadJson['visibility'] = visi
    
    def test_04_changed_date(self):
        ordate = self.testCase.dryadJson['lastModificationDate']
        self.testCase.dryadJson['lastModificationDate'] = '1941-12-07'
        diff = self.montest.status(self.testCase)
        self.assertEqual(diff['status'], 'updated', True)
        self.testCase.dryadJson['lastModificationDate'] = ordate
    
    def test_06_unchanged_files(self):
        doi = self.testCase.doi
        self.montest.cursor.execute('SELECT uid from dryadStudy WHERE doi = ?',(doi,))
        dryuid = self.montest.cursor.fetchone()[0]
        djson = json.dumps(self.testCase.fileJson)
        self.montest.cursor.execute('DELETE  FROM  dryadFiles WHERE dryaduid = ?', (dryuid, ))
        self.montest.cursor.execute('INSERT INTO dryadFiles VALUES (?, ?)', (dryuid, djson))
        diff = self.montest.status(self.testCase)
        self.assertEqual(diff['status'], 'identical', True)
        diff = self.montest.diff_files(self.testCase)
        self.assertEqual.__self__.maxDiff = None
        self.assertEqual({}, diff, True)

    def test_07_added_files(self):
        self.assertEqual.__self__.maxDiff = None
        newdata=copy.copy(self.testCase.fileJson[0]['_embedded']['stash:files'][-1])
        newdata['_links']['stash:file-download']['href'] = '/api/v2/files/999999/download' 
        newdata['path'] = 'ubc_rand1.csv'
        newdata['description'] = 'UBC random data 1'
        newdata['digestType'] = 'md5'
        newdata['digest'] = '6f953c01804e4fc8ec97f7c45d8259b8'
        self.testCase.fileJson[0]['_embedded']['stash:files'].append(newdata)
        diff = self.montest.diff_files(self.testCase)
        self.assertNotEqual({}, diff)
        expect = {'add': [( 
           'https://datadryad.org/api/v2/files/999999/download', 
            'ubc_rand1.csv',
               'text/plain',
               1350,
               'UBC random data 1', 
               'md5',
               '6f953c01804e4fc8ec97f7c45d8259b8')]}
        self.assertEqual(expect, diff)
        #restore state
        del self.testCase.fileJson[0]['_embedded']['stash:files'][-1]

    def test_08_deleted_files(self):
        newdata=copy.copy(self.testCase.fileJson[0]['_embedded']['stash:files'][0])
        del self.testCase.fileJson[0]['_embedded']['stash:files'][0]
        diff = self.montest.diff_files(self.testCase)
        self.assertNotEqual({}, diff)
        expect = {'delete': [('https://datadryad.org/api/v2/files/267417/download',
                              'GCB_ACG_Mortality_2020.zip',
               'application/x-zip-compressed',
               23787587,
               '',
               '', '')]}
        self.assertEqual.__self__.maxDiff = None 
        self.assertEqual(expect, diff)
        #and restore
        self.testCase.fileJson[0]['_embedded']['stash:files'].insert(0,newdata)


    def test_09_added_hash(self):
        self.testCase.fileJson[-1]['_embedded']['stash:files'][-1]['digestType']='md5'
        self.testCase.fileJson[-1]['_embedded']['stash:files'][-1]['digest']='6c994262e3e31a972ba63b4e07f0test'
        diff = self.montest.diff_files(self.testCase)
        self.assertEqual.__self__.maxDiff = None 
        self.assertNotEqual({}, diff)
        self.assertEqual(diff, {'hash_change' : 
            [x for x in self.testCase.files if x[-1].endswith('test')]})
        #restore state
        self.testCase._fileJson = None
    
    def test_10_no_transfer(self):
        ftest = dryad2dataverse.transfer.Transfer(self.testCase)
        self.assertEqual(ftest.fileUpRecord,  [])
        self.assertEqual(ftest.fileDelRecord, [])

    def test_11_find_dvfid(self):
        #admittedly, this is kind of a garbage test
        ins = 'INSERT INTO dvfiles VALUES (?, ?, ?, ?, ?, ?);'
        data_a = (203, 16247, "02d78d74c2b7307c5821cf5e92a3478c",152242,"02d78d74c2b7307c5821cf5e92a3478c", '{}')
        data_b = (947,16247,'9f498c8e9f0875f7b132b9aadae8f8bb',258214,'9f498c8e9f0875f7b132b9aadae8f8bb', '{}') 
        self.montest.cursor.execute(ins, data_a)
        self.montest.cursor.execute(ins, data_b)
        self.montest.conn.commit()
        self.assertEqual(self.montest.get_dv_fid('https://datadryad.org/api/v2/files/16247/download'), '258214')

