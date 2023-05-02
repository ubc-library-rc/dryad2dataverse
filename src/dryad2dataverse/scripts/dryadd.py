#! python
'''
Dryad daemon for monitoring and automatically uploading studies associated with a particular ROR

Requires Python 3.6+ and requests library

'''

from  email.message import EmailMessage as Em
import argparse
import ast
import datetime
import glob
import logging
import logging.handlers
import os
import shutil
import smtplib
import sys
import textwrap
import time

import requests
import dryad2dataverse
import dryad2dataverse.monitor
import dryad2dataverse.serializer
import dryad2dataverse.transfer
from dryad2dataverse.handlers import SSLSMTPHandler

VERSION = (0, 5, 2)
__version__ = '.'.join([str(x) for x in VERSION])

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

def __clean_msg(msg:str, width=100) -> str:
    '''
    Cleans a string for nice, legible emailing

    Who knew there were limits to email sizes?
    https://www.rfc-editor.org/rfc/rfc2821#section-4.5.3.1
    '''
    msg = msg.split('\n')
    msg = [x.strip() for x in msg]
    for num, val in enumerate(msg):
        #list with tuples
        if val.startswith('[('):
            details = ast.literal_eval(val)
            details = [list(x) for x in details]
            for num2, val2 in enumerate(details):
                details[num2] = '\n'.join(textwrap.wrap(', '.join([str(x) for x in val2]),
                                                        width=width))
            msg[num] = '\n'.join(details)
        #single list
        elif val.startswith('['):
            msg[num] = '\n'.join(textwrap.wrap(str(val), width=width))
    msg = [x for x in msg if x]
    msg = '\n'.join(msg)
    return msg

def notify(msgtxt, width=100, **kwargs):
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
    width : int
        Maximum line length. Max 1000

    From the argument parser these keys and values are required:
    email : str
        From address for account
    user : str
        User name for email account
    pwd : str
        Password for email account
    mailserv : str
        SMTP server for sending mail
    port : int
        Mailserver port. Default 465
    recipients : list
        List of email addresses of recipients
    '''

    msg = Em()
    msg['Subject'] = msgtxt[0]
    msg['From'] = kwargs['email']
    msg['To'] = kwargs['recipients']
    content = __clean_msg(msgtxt[1], max(width, 1000))
    msg.set_content(content)

    server = smtplib.SMTP_SSL(kwargs['mailserv'], kwargs.get('port', 465))

    server.login(kwargs['user'], kwargs['pwd'])
    #To must be split. See
    #https://stackoverflow.com/questions/8856117/
    #how-to-send-email-to-multiple-recipients-using-python-smtplib
    #server.sendmail(msg['From'], msg['To'].split(','), msg.as_string())
    server.send_message(msg)
    server.close()

def __bad_dates(rectuple: tuple, mod_date: str) -> tuple:
    '''
    As of 10 December 2021 the Dryad API has a bug which doesn't filter
    anything if you ask for a date preceding 11 December 2021.

    This convenience function will filter those results until the API
    works again.


    rectuple : tuple
        output from dryadd.get_records

    mod_date : str
        Date string in '%Y-%m-%dT%H:%M:%SZ' format
        None for mod_date doesn't filter results
    '''
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    fmt2 = '%Y-%m-%d'

    #If python3.7, much easier
    #datetime.strptime(date, fmt)
    #but python3.6
    #datetime.datetime(*(time.strptime(date_string, format)[0:6]))
    #There could also be no mod_date if you are looking for
    #new files
    if mod_date:
        records = [x for x in rectuple
        if datetime.datetime(*(time.strptime(x[1]['lastModificationDate'],
                             fmt2)[0:6])) >=
                             datetime.datetime(*(time.strptime(mod_date,
                                               fmt)[0:6]))
                  ]
        return tuple(records)
    return rectuple

def get_records(ror: 'str', mod_date=None, verbosity=True, timeout=100):
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

    timeout : int
        request timeout in seconds
    '''
    headers = {'accept':'application/json',
               'Content-Type':'application/json'}
    per_page = 1
    params = {'affiliation' : ror,
              'per_page' : per_page}
    if mod_date:
        params['modifiedSince'] = mod_date
    stud = requests.get(f'{DRY}/search', headers=headers,
                        params=params, timeout=timeout)
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
                            params=params,
                            timeout=timeout)
        time.sleep(10) # don't overload their system with API calls
        stud.raise_for_status()
        records += stud.json()['_embedded']['stash:datasets']


    #return tuple([(x['identifier'], x) for x in records])
    #This can be removed when they fix the API
    return __bad_dates(tuple((x['identifier'], x)
                              for x in records),
                              mod_date)

def argp():
    '''
    Argument parser
    '''
    description = ('Dryad to Dataverse importer/monitor. '
                   'All arguments NOT enclosed by square brackets are required for '
                   'the script to run but some may already have defaults, specified '
                   'by "Default". '
                   'The "optional arguments" below refers to the use of the option switch, '
                   '(like -u), meaning "not a positional argument."'
                   )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--dv-url',
                        help='Destination Dataverse root url. '
                        'Default: https://borealisdata.ca',
                        required=False,
                        default='https://borealisdata.ca',
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
                        help='REQUIRED: Email address '
                        'which sends update notifications. ie: '
                        '"user@website.invalid".',
                        required=True,
                        dest='email')
    parser.add_argument('-s', '--user',
                        help=('REQUIRED: User name for SMTP server. Check '
                              'your server for details. '),
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
                        'Default: smtp.mail.yahoo.com',
                        required=False,
                        default='smtp.mail.yahoo.com',
                        dest='mailserv')
    parser.add_argument('--port',
                        help='Mail server port. Default: 465. '
                        'Mail is sent using SSL.',
                        required=False,
                        type=int,
                        #default=587,
                        default=465,
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
                        help='Temporary file location. Default: /tmp',
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
                        help='No forcible file unlock. Required '
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
    parser.add_argument('-b', '--num-backups',
                        help=('Number of database backups to keep. '
                              'Default 3'),
                        required=False,
                        type=int,
                        default=3)
    parser.add_argument('-w', '--warn-too-many',
                        help=('Warn and halt execution if abnormally large '
                              'number of updates present.'),
                        action='store_true',)
    parser.add_argument('--warn-threshold',
                        help=('Do not transfer studies if number of updates '
                              'is greater than or equal to this number. '
                              'Default: 15'),
                        type=int,
                        dest='warn',
                        default=15)
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__
                        +'; dryad2dataverse '+
                        dryad2dataverse.__version__,
                        help='Show version number and exit')

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

def email_log(mailhost, fromaddr, toaddrs, credentials, port=465, secure=(),
              level=logging.WARNING, timeout=100):
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
    port : Mailserver port. Default 465
    secure : tuple
        The tuple should be either an empty tuple, or a single-value tuple with
        the name of a keyfile, or a 2-value tuple with the names of the keyfile
        and certificate file.
        See https://docs.python.org/3/library/logging.handlers.html
    level : int
        logging level. Default logging.WARNING
    '''
    #pylint: disable=too-many-arguments
    #Because consistency is for suckers and yahoo requires full hostname
    subject = 'Dryad to Dataverse transfer error'
    elog = logging.getLogger('email_log')
    mailer = SSLSMTPHandler(mailhost=(mailhost, port),
                            fromaddr=fromaddr,
                            toaddrs=toaddrs, subject=subject,
                            credentials=credentials, secure=secure,
                            timeout=timeout)
    l_format = logging.Formatter('%(name)s - %(asctime)s'
                                 ' - %(levelname)s - %(funcName)s - '
                                 '%(message)s')
    mailer.setFormatter(l_format)
    mailer.setLevel(level)
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
    logger = logging.getLogger()#root logger
    #Set all the logs to the same level:
    #https://stackoverflow.com/questions/35325042/
    #python-logging-disable-logging-from-imported-modules
    for name in ['dryad2dataverse.serializer',
               'dryad2dataverse.transfer',
               'dryad2dataverse.monitor']:
        logging.getLogger(name).setLevel(level)
    rotator = logging.handlers.RotatingFileHandler(filename=path,
                                                   maxBytes=10*1024**2,
                                                   backupCount=10)
    logger.addHandler(rotator)
    l_format = logging.Formatter('%(name)s - %(asctime)s'
                                 ' - %(levelname)s - %(funcName)s - '
                                 '%(message)s')
    rotator.setFormatter(l_format)
    rotator.setLevel(level)
    logger.setLevel(level)
    return logger

def checkwarn(val:int, **kwargs) -> None:
    '''
    Halt program execution before processing if threshold value of modified
    Dryad studies exceeded. Useful for checking if the Dryad API has changed
    and caused havoc.

    val: int
        Number of modified or new studies
    kwargs: dict
        Email notification information.
        {'user': user email,
         'recipients':[list of recipients],
         'pwd' ; email server password],
         'mailserv' : smtp mail server,
         'warn': Threshold for number of warnings (int)}
        see dryadd.notify for full details of parameters.

        Include log info:
        {loggers: [logging.logger, logging.logger,...]}
        Skip check
        {'warn_too_many': bool}

    '''
    if not kwargs.get('warn_too_many'):
        return
    if val >= kwargs.get('warn',0):
        mess = ('Large number of updates detected. '
                f'{val} new studies exceeds threshold of {kwargs.get("warn", 0)}. '
                'Program execution halted.')
        subject = ('Dryad to Dataverse large update warning')
        for logme in kwargs.get('loggers'):
            logme.warning(mess)
        notify(msgtxt=(subject, mess),
               **vars(kwargs))
        sys.exit()

def verbo(verbosity:bool, **kwargs)->None:
    '''
    verbosity: bool
        if True, print dict
    kwargs : dict
        Dictionary to print out
    '''
    if verbosity:
        for key, value in kwargs.items():
            print(f'{key}: {value}')

def main(log='/var/log/dryadd.log', level=logging.warning):
    '''
    Main Dryad transfer daemon

    log : str
        path to logfile
    level : int
        log level, usually one of logging.LOGLEVEL (ie, logging.warning)
    '''
    #pylint: disable=too-many-branches
    #pylint: disable=too-many-statements
    #pylint: disable=too-many-locals
    parser = argp()
    args = parser.parse_args()
    if args.log:
        log = args.log
    logger = rotating_log(log, level)

    set_constants(args)
    elog = email_log(args.mailserv, args.email, args.recipients,
                     (args.user, args.pwd), port=args.port)


    logger.info('Beginning update process')
    monitor = dryad2dataverse.monitor.Monitor(args.dbase)
    #copy the database to make a backup, because paranoia is your friend
    if os.path.exists(dryad2dataverse.constants.DBASE):
        shutil.copyfile(dryad2dataverse.constants.DBASE,
                        dryad2dataverse.constants.DBASE+'.'+
                        datetime.datetime.now().strftime('%Y-%m-%d-%H%M'))
    #list comprehension includes untimestamped dbase name, hence 2+
    fnames = glob.glob(os.path.abspath(dryad2dataverse.constants.DBASE)
                       +'*')
    fnames.remove(os.path.abspath(dryad2dataverse.constants.DBASE))
    fnames.sort(reverse=True)
    fnames = fnames[args.num_backups:]
    for fil in fnames:
        os.remove(fil)
    logger.info('Last update time: %s', monitor.lastmod)
    #get all updates since the last update check
    updates = get_records(args.ror, monitor.lastmod,
                          verbosity=args.verbosity)
    logger.info('Total new files: %s', len(updates))
    elog.info('Total new files: %s', len(updates))

    checkwarn(val=len(updates),
              loggers=[logger],
              **vars(args))

    #update all the new files
    verbo(args.verbosity, **{'Total to process': len(updates)})
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
            #verbose output
            verbo(args.verbosity,
                  **{'Processing': count,
                     'DOI': study.doi,
                     'Title': study.dryadJson['title']})
            if study.embargo:
                logger.warning('Study %s is embargoed. Skipping', study.doi)
                elog.warning('Study %s is embargoed. Skipping', study.doi)
                verbo(args.verbosity, **{'Embargoed':study.embargo})
                continue
            #it turns out that the Dryad API sends all the metadata
            #from the study in their search, so it's not necessary
            #to download it again
            study.dryadJson = doi[1]

            #check to see what sort of update it is.
            update_type = monitor.status(study)['status']
            verbo(args.verbosity, **{'Status': update_type})
            #create a transfer object to copy the files over
            transfer = dryad2dataverse.transfer.Transfer(study)
            transfer.test_api_key()
            #Now start the action
            if update_type == 'new':
                logger.info('New study: %s, %s', doi[0], doi[1]['title'])
                logger.info('Uploading study metadata')
                transfer.upload_study(targetDv=args.target)
                #New files are in now in monitor.diff_files()['add']
                #with 2 Feb 2022 API change
                #so we can ignore them here
                logger.info('Uploading Dryad JSON metadata')
                transfer.upload_json()
                transfer.set_correct_date()
                notify(new_content(study),
                       **vars(args))

            elif update_type == 'updated':
                logger.info('Updated metadata: %s', doi[0])
                logger.info('Updating metadata')
                transfer.upload_study(dvpid=study.dvpid)
                #remove old JSON files
                rem = monitor.get_json_dvfids(study)
                transfer.delete_dv_files(rem)
                transfer.upload_json()
                transfer.set_correct_date()
                notify(changed_content(study, monitor),
                       **vars(args))

                #new, identical, updated, lastmodsame
            elif update_type in ('unchanged', 'lastmodsame'):
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
        notify(finished, **vars(args))

    except dryad2dataverse.exceptions.DataverseBadApiKeyError as api_err:
        logger.exception(api_err)
        elog.exception(api_err)
        print(f'Error: {api_err}. Exiting. For details see log at {args.log}.')
        sys.exit()#graceful exit is graceful

    except Exception as err: # pylint: disable=broad-except
        elog.exception('%s\nCritical failure with DOI: %s : %s\n%s', err,
                       doi[0], doi[1]['title'], doi[1].get('sharingLink'),
                       stack_info=True, exc_info=True)
        logger.exception('%s\nCritical failure with DOI: %s : %s\n%s', err,
                         doi[0], doi[1]['title'], doi[1].get('sharingLink'),
                         stack_info=True, exc_info=True)
        print(f'Error: {err}. Exiting. For details see log at {args.log}.')
        sys.exit()

if __name__ == '__main__':
    main()
