'''
Dryad daemon for monitoring and automatically uploading studies associated with a particular ROR

Requires Python 3.6+ and request

'''

from  email.message import EmailMessage as Em
import argparse
import logging
import shutil
import smtplib
import time
import os

import requests

import dryad2dataverse.monitor
import dryad2dataverse.serializer
import dryad2dataverse.transfer

DRY = 'https://datadryad.org/api/v2'

def notify(serial, monitor,
           user=None, pwd=None,
           mailserv='smtp.gmail.com',
           port=None, recipient=None):
    '''
    Basic email change notifier. Will sent email outlining metadata changes
    to recipient.

    Has only really been tested with Gmail (although it should work with anything,
    and Gmail requires 'Allow less secure apps' or whatever they call it.
    '''

    if not port:
        port = 587
    msg = Em()
    msg['Subject'] = f'Dryad study change notification for {serial.doi}'
    msg['From'] = user
    msg['To'] = [recipient]

    content = f'Study {serial.dryadJson["title"]} / {serial.doi} has changed content.\n\
            \nDetails:\n\
            \nMetadata changes:\
            \n{monitor.diff_metadata(serial)}\n\
            \nFile changes:\
            \n{monitor.diff_files(serial)}\n\
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

def get_records(ror: 'str', mod_date=None):
    '''
    returns a tuple of ((doi, metadata), ...). Dryad searches return complete
    study metadata from the search, surprisingly.

    ror : str
        ROR string including http

    mod_date : str
            UTC datetime string in the format suitable for the Dryad API.
            eg. 2021-01-21T21:42:40Z
            or .strftime('%Y-%m-%dT%H:%M:%SZ')
            if no mod_date is passed, all studies will be retrieved
    '''
    headers = {'accept':'application/json',
               'Content-Type':'application/json'}
    per_page = 1
    params = {'affiliation' : ror,
              'per_page' : per_page}
    if mod_date:
        params['modifiedSince'] = mod_date
    #print(params)
    stud = requests.get(f'{DRY}/search', headers=headers,
                        params=params)
    records = []
    total = stud.json()['total']
    print(f'Total Records: {total}')
    params['per_page'] = 100
    for data in range(total//100+1):
        print(f'Records page: {data+1}')
        params['page'] = data+1
        print(params)
        stud = requests.get(f'{DRY}/search',
                            headers=headers,
                            params=params)
        time.sleep(10) # don't overload their system with API calls
        stud.raise_for_status()
        records += stud.json()['_embedded']['stash:datasets']
    dois = [x['identifier'] for x in records]
    return tuple((x, y) for x, y in zip(dois, records))

def argp():
    '''
    Argument parser
    '''
    parser = argparse.ArgumentParser(description='Dryad to Dataverse import daemon')
    parser.add_argument('-u', '--dv-url',
                        help='Destination dataverse root url. '
                        'Eg: https://dataverse.scholarsportal.info',
                        required=False,
                        dest='url')
    parser.add_argument('-k', '--key',
                        help='API key for dataverse user',
                        required=True,
                        dest='key')
    parser.add_argument('-t', '--target',
                        help='Target dataverse short name',
                        required=True,
                        dest='target')
    parser.add_argument('-e', '--email',
                        help='Username for email address'
                        'which sends update notifications.',
                        required=False,
                        dest='user')
    parser.add_argument('-r', '--recipient',
                        help='Recipient of email notification',
                        required=False,
                        dest='recipients')
    parser.add_argument('-p', '--pwd',
                        help='Password for email account',
                        required=False,
                        dest='pwd')
    parser.add_argument('--server',
                        help='Mail server. Eg. smtp.gmail.com',
                        required=False,
                        dest='mailserv')
    parser.add_argument('--port',
                        help='Mail server port',
                        required=False,
                        type=int,
                        dest='port')
    parser.add_argument('-c', '--contact',
                        help='Contact email for Dataverse records',
                        required=True,
                        dest='contact')
    parser.add_argument('-n', '--contact-name',
                        help='Contact name for Dataverse records',
                        required=True,
                        dest='cname')
    parser.add_argument('-v', '--verbosity',
                        help='Verbose output',
                        required=False,
                        action='store_true')
    parser.add_argument('-i', '--ror',
                        help='Institutional ROR url. '
                        'Eg: https://ror.org/03rmrcq20',
                        required=True,
                        dest='ror')
    parser.add_argument('--tmpfile',
                        help='Temporary file location (if not /tmp)',
                        required=False,
                        dest='tmp')
    parser.add_argument('--db',
                        help='Tracking database location and name if not'
                        '$HOME/dryad_dataverse_monitor.sqlite3',
                        required=False,
                        dest='dbase')
    return parser

def set_constants(args):
    '''
    Set the appropriate dryad2dataverse constants
    '''
    dryad2dataverse.constants.DV_CONTACT_EMAIL = args.contact
    dryad2dataverse.constants.DV_CONTACT_ = args.contact
    dryad2dataverse.constants.APIKEY = args.key
    if args.url:
        dryad2dataverse.constants.DVURL = args.url
    if args.dbase:
        dryad2dataverse.constants.DBASE = args.dbase

def main(log='/var/log/dryadd.log'):
    '''
    Main Dryad transfer daemon

    log : str
        Full path to dryad log location. Default /var/log/dryadd.log
    '''
    parser = argp()
    args = parser.parse_args()
    set_constants(args)
    '''
    dryad2dataverse.constants.DV_CONTACT_EMAIL = args.contact
    dryad2dataverse.constants.DV_CONTACT_ = args.contact
    dryad2dataverse.constants.APIKEY = args.key
    if args.url:
        dryad2dataverse.constants.DVURL = args.url
    '''
    logging.basicConfig(level=logging.DEBUG,
                        filename=log,
                        filemode='w',
                        format='%(name)s - %(asctime)s'
                               ' - %(levelname)s - %(funcName)s - '
                               '%(message)s')

    #copy the database to make a backup, because paranoia is your friend
    if os.path.exists(dryad2dataverse.constants.DBASE):
        shutil.copyfile(dryad2dataverse.constants.DBASE,
                        dryad2dataverse.constants.DBASE+'.bak')

    monitor = dryad2dataverse.monitor.Monitor(args.dbase)
    #TODO remove line below on release
    monitor.set_timestamp('1999-01-14T00:00:00Z')
    logging.info('Last update time: %(monitor.lastmod)s')

    #get all updates since the last update check
    updates = get_records(args.ror, monitor.lastmod)
    import pickle
    import sys
    with open('/Users/paul/tmp/updates.pickle', 'wb') as f:
           pickle.dump(updates, f)
    print(updates)
    sys.exit()
    #update all the new files
    for doi in updates:
        if not updates:
            break #no new files in this case
        #Create study object
        study = dryad2dataverse.serializer.Serializer(doi[0])
        '''
        with open('/Users/paul/tmp/doi.pickle', 'wb') as f:
            pickle.dump(doi, f)
        sys.exit()
        '''
        #it turns out that the Dryad API sends all the metadata
        #from the study in their search, so it's not necessary
        #to download it again
        study._dryadJson = doi[1]

        #check to see what sort of update it is.
        update_type = monitor.status(study)['status']

        #create a transfer object to copy the files over
        transfer = dryad2dataverse.transfer.Transfer(study)

        #Now start the action
        if update_type == 'new':
            logging.info('New study: %(doi[0])s')
            logging.info('Uploading study metadata')
            transfer.upload_study(targetDv=args.target)
            logging.info('Uploading files to Dataverse')
            transfer.upload_files()
            logging.info('Uploading Dryad JSON metadata')
            transfer.upload_json()

        if update_type == 'updated':
            logging.info('Updated metadata: %(doi[0])s')
            logging.info('Updating metadata')
            transfer.upload_study(dvpid=study.dvpid)
            #remove old JSON files
            rem = monitor.get_json_dvfids(study)
            transfer.delete_dv_files(rem)
            transfer.upload_json()

        if update_type == 'unchanged':
            logging.info('Unchanged metadata %(doi[0])s')
            continue

        if update_type != 'unchanged':
            notify(study, monitor,
                   user=args.user, pwd=args.pwd,
                   recipient=args.recipients)

        diff = monitor.diff_files(study)
        if diff.get('delete'):
            del_these = monitor.get_dv_fids(diff['delete'])
            transfer.delete_dv_files(dvfids=del_these)
            logging.info('Deleted files %(diff["delete"])s from Dataverse')
        if diff.get('add'):
            logging.info('Adding files %(diff["add"])s to Dataverse')
            transfer.upload_files(diff['add'], pid=study.dvpid)

        #Update the tracking database for that record
        monitor.update(transfer)
    #and finally, update the time for the next run
    monitor.set_timestamp()

if __name__ == '__main__':
    #print(get_records('https://ror.org/03rmrcq20', '2021-01-01'))
    main(log='/Users/paul/tmp/dry.log')
