'''
Dryad daemon for monitoring and automatically uploading studies associated with a particular ROR

Requires Python 3.6+ and requests library

'''

from  email.message import EmailMessage as Em
import argparse
#import datetime
import logging
import logging.handlers
import os
import shutil
import smtplib
import time

import requests
import dryad2dataverse.monitor
import dryad2dataverse.serializer
import dryad2dataverse.transfer

DRY = 'https://datadryad.org/api/v2'

def new_content(serial):
    '''
    Creates content for new study upload message (potentially redundant
    with Dataverse emailer).
    serial : dryad2dataverse.serializer.Serializer instance
    '''
    dv_link = (dryad2dataverse.serializer.constants.DVURL +
               '/dataset.xhtml?persistentId=' +
               serial.dvpid +
               '&version=DRAFT')
    subject = f'Dryad new study notification for {serial.doi}'
    content = f'Study {serial.dryadJson["title"]} / {serial.doi} is a new Dryad study.\n\
            \nDataverse URL: {dv_link}\n\
            \nDetails:\n\
            \nFiles in study:\n\
            \n{serial.files}\n\
            \nOversize files which must be moved manually:\n\
            \n{serial.oversize}'
    return (subject, content)

def changed_content(serial, monitor):
    '''
    Creates content for file update message.
    serial : dryad2dataverse.serializer.Serializer instance
    monitor : dryad2dataverse.monitor.Monitor instance
    '''
    dv_link = (dryad2dataverse.serializer.constants.DVURL +
               '/dataset.xhtml?persistentId=' +
               serial.dvpid +
               '&version=DRAFT')
    subject = f'Dryad study change notification for {serial.doi}'
    content = f'Study {serial.dryadJson["title"]} / {serial.doi} has changed content.\n\
            \nDataverse URL: {dv_link}\n\
            \nDetails:\n\
            \nMetadata changes:\
            \n{monitor.diff_metadata(serial)}\n\
            \nFile changes:\
            \n{monitor.diff_files(serial)}\n\
            \nOversize files:\
            \n{serial.oversize}'
    return (subject, content)

def notify(msgtxt,
           user=None, pwd=None,
           mailserv='smtp.gmail.com',
           port=None, recipient=None):
    '''
    Basic email change notifier. Will sent email outlining metadata changes
    to recipient. Uses SSL.

    Has only really been tested with Gmail (although it should work with anything,
    and Gmail requires 'Allow less secure apps' or whatever they call it.
    If you are having troubles with GMail:

    1. Enable less secure access

    2. Disable the CAPTCHA:
       https://accounts.google.com/DisplayUnlockCaptcha

    Note: Google will automatically revert settings after some arbitrary period
    of time. You have been warned.

    If your application worked before but suddenly it crashes with authenication
    errors, this is why.

    msgtext : tuple
        Tuple containing strings of ('subject', 'message content')
    user : str
        User name for email account (NOT full email address)
    pwd : str
        Password for email account
    mailserv : str
        SMTP server for sending mail
    port : int
        Mailserver port. Default 465
    recipient : list
        List of email addresses of recipients
    '''

    if not port:
        #port = 587
        port = 465
    msg = Em()
    msg['Subject'] = msgtxt[0]
    msg['From'] = user
    #msg['To'] = [recipient]
    msg['To'] = recipient

    content = msgtxt[1]
    msg.set_content(content)
    #server = smtplib.SMTP(mailserv, port)
    #server.ehlo()
    #server.starttls()
    #server.ehlo()
    server = smtplib.SMTP_SSL(mailserv, port)
    server.login(user, pwd)
    #To must be split. See
    #https://stackoverflow.com/questions/8856117/
    #how-to-send-email-to-multiple-recipients-using-python-smtplib
    server.sendmail(msg['From'], msg['To'].split(','), msg.as_string())
    server.close()

def get_records(ror: 'str', mod_date=None, verbosity=True):
    '''
    returns a tuple of ((doi, metadata), ...). Dryad searches return complete
    study metadata from the search, surprisingly.

    ror : str
        ROR string including http. To find your ROR, see
        https://ror.org/

    mod_date : str
        UTC datetime string in the format suitable for the Dryad API.
        eg. 2021-01-21T21:42:40Z
        or .strftime('%Y-%m-%dT%H:%M:%SZ')
        if no mod_date is passed, all studies will be retrieved

    verbosity : bool
       Output some data to stdout
    '''
    headers = {'accept':'application/json',
               'Content-Type':'application/json'}
    per_page = 1
    params = {'affiliation' : ror,
              'per_page' : per_page}
    if mod_date:
        params['modifiedSince'] = mod_date
    stud = requests.get(f'{DRY}/search', headers=headers,
                        params=params)
    records = []
    total = stud.json()['total']
    if verbosity:
        print(f'Total Records: {total}')
    params['per_page'] = 100
    for data in range(total//100+1):
        if verbosity:
            print(f'Records page: {data+1}')
        params['page'] = data+1
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
    description = ('Dryad to Dataverse import daemon. '
                   'All arguments NOT enclosed by square brackets are REQUIRED. '
                   'Arguments in [square brackets] are not required. '
                   'The "optional arguments" below refers to the use of the option switch, '
                   '(like -u), meaning "not a positional argument."'
                   )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--dv-url',
                        help='REQUIRED: Destination dataverse root url. '
                        'Default: https://dataverse.scholarsportal.info',
                        required=True,
                        dest='url')
    parser.add_argument('-k', '--key',
                        help='REQUIRED: API key for dataverse user',
                        required=True,
                        dest='key')
    parser.add_argument('-t', '--target',
                        help='REQUIRED: Target dataverse short name',
                        required=True,
                        dest='target')
    parser.add_argument('-e', '--email',
                        help='REQUIRED: Username for email address '
                        'which sends update notifications. ie, the "user" portion '
                        'of "user@website.invalid".',
                        required=True,
                        dest='user')
    parser.add_argument('-r', '--recipient',
                        help='REQUIRED: Recipient(s) of email notification. '
                        'Separate addresses with spaces',
                        required=True,
                        nargs='+',
                        dest='recipients')
    parser.add_argument('-p', '--pwd',
                        help='REQUIRED: Password for sending email account. '
                        'Enclose in single quotes to avoid OS errors with special '
                        'characters.',
                        required=True,
                        dest='pwd')
    parser.add_argument('--server',
                        help='Mail server for sending account. '
                        'Default: smtp.gmail.com',
                        required=False,
                        default='smtp.gmail.com',
                        dest='mailserv')
    parser.add_argument('--port',
                        help='Mail server port. Default: 465. '
                        'Mail is sent using SSL.',
                        required=False,
                        type=int,
                        default=587,
                        dest='port')
    parser.add_argument('-c', '--contact',
                        help='REQUIRED: Contact email address for Dataverse records. '
                        'Must pass Dataverse email validation rules (so "test@test.invalid" '
                        'is not acceptable).',
                        required=True,
                        dest='contact')
    parser.add_argument('-n', '--contact-name',
                        help='REQUIRED: Contact name for Dataverse records',
                        required=True,
                        dest='cname')
    parser.add_argument('-v', '--verbosity',
                        help='Verbose output',
                        required=False,
                        action='store_true')
    parser.add_argument('-i', '--ror',
                        help='REQUIRED: Institutional ROR URL. '
                        'Eg: "https://ror.org/03rmrcq20". This identifies the '
                        'institution in Dryad repositories.',
                        required=True,
                        dest='ror')
    parser.add_argument('--tmpfile',
                        help='Temporary file location. Default: /tmp)',
                        required=False,
                        dest='tmp')
    parser.add_argument('--db',
                        help='Tracking database location and name. '
                        'Default: $HOME/dryad_dataverse_monitor.sqlite3',
                        required=False,
                        dest='dbase')
    parser.add_argument('--log',
                        help='Complete path to log. '
                        'Default: /var/log/dryadd.log',
                        required=False,
                        dest='log',
                        default='/var/log/dryadd.log')
    parser.add_argument('-l', '--no_force_unlock',
                        help='No forcible file unlock. Required'
                        'if /lock endpint is restricted',
                        required=False,
                        action='store_false',
                        dest='force_unlock')

    parser.add_argument('-x', '--exclude',
                        help='Exclude these DOIs. Separate by spaces',
                        required=False,
                        default=[],
                        nargs='+',
                        dest='exclude')

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

def email_log(mailhost, fromaddr, toaddrs, credentials, secure=(),
              level=logging.WARNING):
    '''
    Emails log error messages to recipient

    mailhost : str
        Address of mail server. Eg. smtp.gmail.com
    fromaddr : str
        "From" address for email
    toaddrs :
        Recipient of email
    credentials : tuple
        (Username, password) tuple
    secure : tuple
        The tuple should be either an empty tuple, or a single-value tuple with
        the name of a keyfile, or a 2-value tuple with the names of the keyfile
        and certificate file.
        See https://docs.python.org/3/library/logging.handlers.html
    level : int
        logging level. Default logging.WARNING
    '''
    subject = 'Dryad to Dataverse transfer error'
    elog = logging.getLogger('email_log')
    mailer = logging.handlers.SMTPHandler(mailhost=mailhost, fromaddr=fromaddr,
                                          toaddrs=toaddrs, subject=subject,
                                          credentials=credentials, secure=secure)
    l_format = logging.Formatter('%(name)s - %(asctime)s'
                                 ' - %(levelname)s - %(funcName)s - '
                                 '%(message)s')
    mailer.setFormatter(l_format)
    elog.addHandler(mailer)
    elog.setLevel(level)
    return elog

def rotating_log(path, level):
    '''
    Create log of transactions

    path : str
        Complete path to log
    level : logging.LOGLEVEL
        logging level (eg, logging.DEBUG)

    '''
    #global logger
    #logger = logging.getLogger(__name__)
    logger = logging.getLogger()#root logger
    #Set all the logs to the same level:
    #https://stackoverflow.com/questions/35325042/
    #python-logging-disable-logging-from-imported-modules
    for na in ['dryad2dataverse.serializer',
               'dryad2dataverse.transfer',
               'dryad2dataverse.monitor']:
        logging.getLogger(na).setLevel(level)
    rotator = logging.handlers.RotatingFileHandler(filename=path,
                                                   maxBytes=10*1024**2,
                                                   backupCount=10)
    logger.addHandler(rotator)
    l_format = logging.Formatter('%(name)s - %(asctime)s'
                                 ' - %(levelname)s - %(funcName)s - '
                                 '%(message)s')
    rotator.setFormatter(l_format)
    #This is required to see the error messages from the other modules. WTF.
    #root_logger = logging.getLogger('')
    #root_logger.setLevel(level)
    #root_logger.addHandler(rotator)
    logger.setLevel(level)
    return logger

def main(log='/var/log/dryadd.log', level=logging.DEBUG):
    '''
    Main Dryad transfer daemon

    log : str
        path to logfile
    level : int
        log level, usually one of logging.LOGLEVEL (ie, logging.warning)
    '''
    parser = argp()
    args = parser.parse_args()
    if args.log:
        log = args.log
    logger = rotating_log(log, level)

    set_constants(args)

    elog = email_log((args.mailserv, args.port), args.contact, args.recipients,
                     (args.user, args.pwd))


    logger.info('Beginning update process')
    #copy the database to make a backup, because paranoia is your friend
    if os.path.exists(dryad2dataverse.constants.DBASE):
        shutil.copyfile(dryad2dataverse.constants.DBASE,
                        dryad2dataverse.constants.DBASE+'.bak')

    monitor = dryad2dataverse.monitor.Monitor(args.dbase)
    logger.info('Last update time: %s', monitor.lastmod)

    #get all updates since the last update check
    updates = get_records(args.ror, monitor.lastmod,
                          verbosity=args.verbosity)

    #update all the new files
    try:
        count = 0
        for doi in updates:
            count += 1
            logger.info('Start processing %s of %s', count, len(updates))
            logger.info('DOI: %s, Dryad URL: https://datadryad.org/stash/dataset/%s',
                        doi[0], doi[0])
            if not updates:
                break #no new files in this case
            if doi[0] in args.exclude:
                logger.warning('Skipping excluded doi: %s', doi[0])
                continue
            #Create study object
            study = dryad2dataverse.serializer.Serializer(doi[0])
            if study.embargo:
                logger.warning('Study %s is embargoed. Skipping', study.doi)
                elog.warning('Study %s is embargoed. Skipping', study.doi)
                continue

            #it turns out that the Dryad API sends all the metadata
            #from the study in their search, so it's not necessary
            #to download it again
            study.dryadJson = doi[1]

            #check to see what sort of update it is.
            update_type = monitor.status(study)['status']

            #create a transfer object to copy the files over
            transfer = dryad2dataverse.transfer.Transfer(study)

            #Now start the action
            if update_type == 'new':
                logger.info('New study: %s, %s', doi[0], doi[1]['title'])
                logger.info('Uploading study metadata')
                transfer.upload_study(targetDv=args.target)
                logger.info('Downloading study files')
                transfer.download_files()
                logger.info('Uploading files to Dataverse')
                transfer.upload_files(force_unlock=args.force_unlock)
                logger.info('Uploading Dryad JSON metadata')
                transfer.upload_json()
                notify(new_content(study),
                       user=args.user, pwd=args.pwd,
                       recipient=args.recipients)

            if update_type == 'updated':
                logger.info('Updated metadata: %s', doi[0])
                logger.info('Updating metadata')
                transfer.upload_study(dvpid=study.dvpid)
                #remove old JSON files
                rem = monitor.get_json_dvfids(study)
                transfer.delete_dv_files(rem)
                transfer.upload_json()
                notify(changed_content(study, monitor),
                       user=args.user, pwd=args.pwd,
                       recipient=args.recipients)

            if update_type == 'unchanged':
                logger.info('Unchanged metadata %s', doi[0])
                continue

            diff = monitor.diff_files(study)
            if diff.get('delete'):
                del_these = monitor.get_dv_fids(diff['delete'])
                transfer.delete_dv_files(dvfids=del_these)
                logger.info('Deleted files %s from '
                            'Dataverse', diff['delete'])
            if diff.get('add'):
                logger.info('Adding files %s '
                            'to Dataverse', diff['add'])
                #you need to download them first if they're new
                transfer.download_files(diff['add'])
                #now send them to Dataverse
                transfer.upload_files(diff['add'], pid=study.dvpid,
                                      force_unlock=args.force_unlock)

            #Update the tracking database for that record
            monitor.update(transfer)

            #Delete the transfer object to ensure that
            #the temporary directory doesn't get filled
            del transfer
        #and finally, update the time for the next run
        monitor.set_timestamp()
        logger.info('Completed update process')
        elog.info('Completed update process')
        finished = ('Dryad to Dataverse transfers completed',
                    ('Dryad to Dataverse transfer daemon has completed.\n'
                     f'Log available at: {log}'))
        notify(finished, user=args.user, pwd=args.pwd,
               recipient=args.recipients)
    except Exception as err:
        logger.critical('Critical failure with DOI: %s, '
                        'Dryad URL: https://datadryad.org/stash/dataset/%s, '
                        'Dataverse URL: %s', transfer.doi, transfer.doi,
                        dryad2dataverse.constants.DVURL+
                        '/dataset.xhtml?persistentId='+transfer.dvpid)
        logger.exception(err)
        logger.critical(err)
        elog.critical('Critical failure with DOI: %s, '
                      'Dryad URL: https://datadryad.org/stash/dataset/%s, '
                      'Dataverse URL: %s', transfer.doi, transfer.doi,
                      dryad2dataverse.constants.DVURL+
                      '/dataset.xhtml?persistentId='+transfer.dvpid)
        elog.exception(err)
        #elog.critical(err)
        raise

if __name__ == '__main__':
    main()
