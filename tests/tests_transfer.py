import unittest
import sqlite3
import json
import pickle
import  dryad2dataverse.serializer
import  dryad2dataverse.transfer
import logging

LOGGER = logging.getLogger('dryad2dataverse.transfer')


#global testCase
#testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
##Dryad file IDS are not constant. In fact, almost nothing is constant so testing
#is hard
#Dryad json for test case on 14 Jan 2022 is 2rbnzs7jp_14Jan22.json 
#with open('tests/dryadStudy.json') as f:
#    testCase._dryadJson = json.load(f)

class TestTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        #print( "Start test")
        cls.testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
        cls.testTrans = dryad2dataverse.transfer.Transfer(cls.testCase)

    def test_file_id(self):
        '''
        Does file_id even matter? we found out in Dec 2021  that they're changeable.
        So this test constantly needs updating. Dammit.
        '''
        self.assertEqual.__self__.maxDiff = None
        files = [list(x) for x in self.testCase.files] 
        ftest = dryad2dataverse.transfer.Transfer(self.testCase)
        self.assertEqual(files, ftest.files, True)
        self.assertEqual(267417, ftest._dryad_file_id(ftest.files[0][0]), True)

    def test_raise(self):
        with self.assertRaises(dryad2dataverse.exceptions.DataverseBadApiKeyError) as err:
            self.testTrans.test_api_key(apikey='BADBADKEY')
        
    def tearDown(self):
        print( "Finish ")

