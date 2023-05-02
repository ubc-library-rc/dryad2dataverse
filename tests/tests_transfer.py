import unittest
import sqlite3
import json
import pickle
import sys
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
        cls.testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
        cls.testTrans = dryad2dataverse.transfer.Transfer(cls.testCase)

    @classmethod
    def tearDownClass(cls):
        cls.testCase.session.close()

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

#    def test_raise(self):
#        #https://stackoverflow.com/questions/17784849/print-an-error-message-without-printing-a-traceback-and-close-the-program-when-a
#        sys.tracebacklimit = -1
#        with self.assertRaises(dryad2dataverse.exceptions.DataverseBadApiKeyError) as err:
#            self.testTrans.test_api_key(apikey='BADBADKEY')
#            self.assertTrue('BAD API key', str(err.exception))
#        sys.tracebacklimit = None


    def test_raise2(self):
        #https://stackoverflow.com/questions/17784849/print-an-error-message-without-printing-a-traceback-and-close-the-program-when-a
        try:
            #https://stackoverflow.com/questions/5255657/how-can-i-disable-logging-while-running-unit-tests-in-python-django
            logging.disable(logging.CRITICAL)
            sys.tracebacklimit = -1
            self.testTrans.test_api_key(apikey='BADBADKEY')
            sys.tracebacklimit = None
        except Exception as err:
            logging.disable(logging.NOTSET)
            sys.tracebacklimit = None
            self.assertTrue('BAD API key', err)
