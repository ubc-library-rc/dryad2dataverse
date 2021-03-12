'''
NOT FOR PRODUCTION USE.

argv[1] DVURL - base Dataverse url with no trailing slash. ie: https://test.invalid
argv[2] APIKEY - API key for dataverse instance
argv[3] DVTARGET - target dataverse
sys.argv[4] = from email
sys.argv[5] = password
sys.argv[6] = destination


Tests all common functions of this library to see if they work. The script will randomly change metadata and files and upload them to a dataverse instance repeatedly. It doesn't actually download data from Dryad; all interactions are simulated. Edit this script toyour liking.

Run it from the ./dryad2dataverse, unless you want to edit it to point to the correct file locations.

A tracking database will be created in tests/junk.db

The interactive portion of the script will ask for deletion if desired.

'''

from  email.message import EmailMessage as Em
import json
import logging
import os
import pickle
import random
import smtplib
import sqlite3
import sys


import requests

import dryad2dataverse.monitor
import dryad2dataverse.serializer
import dryad2dataverse.transfer

dryad2dataverse.constants.DVURL =  sys.argv[1]
dryad2dataverse.constants.APIKEY = sys.argv[2]
DVTARGET = sys.argv[3]
USER = sys.argv[4]
PASS = sys.argv[5]
DEST = sys.argv[6]
dryad2dataverse.constants.DV_CONTACT_EMAIL = 'research.data@library.ubc.ca'
dryad2dataverse.constants.DV_CONTACT_NAME = 'UBC Library Research Data Support'
dryad2dataverse.constants.TMP = os.getcwd() + os.sep + 'tests'
TMP = dryad2dataverse.constants.TMP

logfile = os.getcwd() + os.sep + 'sample_loop_test.log'
logging.basicConfig(level=logging.DEBUG, filename=logfile,
        filemode='w', format='%(name)s - %(asctime)s'
                             ' - %(levelname)s - %(funcName)s - ' 
                             '%(message)s') 



title =['1. This is title one', '2. Secondary title', '3. Tertius Titlus']
files=[f'{TMP}/dryad_files_added.json', f'{TMP}/dryad_files_deleted.json', f'{TMP}/dryad_files_orig.json', f'{TMP}/dryad_files_added_toolarge.json']

def date():
    '''
    Outputs random dataverse compatible date string.
    '''
    yr = random.randint(0,20)
    month = random.randint(1,12)
    day=random.randint(1,28)
    return f'20{yr:02}-{yr:02}-{day:02}'


dates = ['2020-12-21', '2019-02-03', '2010-07-18']

def notify(serial, user=None, pwd=None,  mailserv='smtp.gmail.com', port=None, recipients=None):
    if not port:
        port = 587
    if not user:
        user = USER
    if not pwd:
        pwd = PASS
    if not recipients:
        recipients = [DEST]
    msg = Em()
    msg['Subject'] = f'Dryad study change notification for {serial.doi}'
    msg['From'] = user 
    msg['To'] = recipients

    content = f'Study {serial.dryadJson["title"]} / {serial.doi} has changed content.\n\
            \nDetails:\n\
            \nMetadata changes:\
            \n{montest.diff_metadata(serial)}\n\
            \nFile changes:\
            \n{montest.diff_files(serial)}\n\
            \nOversize files:\
            \n{serial.oversize}'
    msg.set_content(content)
    server = smtplib.SMTP(mailserv, port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(user, pwd)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.close()


for i in range(3):
    testCase = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
    with open(f'{TMP}/dryad_dummy_metadata.json') as f:
        testCase._dryadJson = json.load(f)

    testCase._dryadJson['lastModificationDate'] = random.choice(dates)
    testCase._dryadJson['title'] = random.choice(title)

    with open(random.choice(files)) as f:
        testCase._fileJson = json.load(f)
    montest = dryad2dataverse.monitor.Monitor(f'{TMP}/junk.db')
    ftest = dryad2dataverse.transfer.Transfer(testCase)
    isnew = montest.status(testCase)['status']
    diffmeta = montest.diff_metadata(testCase)
    #Studies
    print(f'DOI: {testCase.doi}')
    print(f'Handle: {testCase.dvpid}')
    if isnew == 'new':
        ftest.upload_study(targetDv=DVTARGET)
        print('New File')
        print('Uploading all files')
        ftest.upload_files()
        print('And now JSON')
        ftest.upload_json()

    if isnew == 'updated':
        print('Updated metadata')
        print('Uploading metadata')
        ftest.upload_study(dvpid=testCase.dvpid)
        print('And now JSON')
        #find old jsons and delete them
        rem = montest.get_json_dvfids(testCase)
        ftest.delete_dv_files(rem)
        ftest.upload_json()

    if isnew =='unchanged':
        print('Unchanged metadata')
        continue
    if isnew == 'filesonly':
        print('Files only')

    #Change notifications if desired
    if isnew != 'unchanged':
        notify(testCase)

       
        
    #Files
    diff = montest.diff_files(testCase)
    if diff.get('delete'):
        delthese = montest.get_dv_fids(diff['delete'])
        print(f'Delete these: {diff.get("delete")}')
        print(f'FID list: {delthese}')
        print(type(delthese))
        ftest.delete_dv_files(dvfids=delthese)
    if diff.get('add'):
        print(f'Add files: {diff.get("add")}')
        ftest.upload_files(diff['add'], pid=testCase.dvpid)

    #and now, the JSONs
    
    print(ftest.fileUpRecord)
    print(ftest.fileDelRecord)
    montest.update(ftest)
    print(diff)
    print(diffmeta)

resp = input('Delete database?')
if resp.lower() in ['yes', 'y']:
    os.remove(f'{TMP}/junk.db')


