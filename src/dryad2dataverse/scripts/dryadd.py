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
import pathlib
import pprint
import shutil
import smtplib
import sys
import textwrap
import time

import requests
import yaml
from requests.adapters import HTTPAdapter

import dryad2dataverse
import dryad2dataverse.auth
import dryad2dataverse.config
import dryad2dataverse.monitor
import dryad2dataverse.serializer
import dryad2dataverse.transfer
from dryad2dataverse.handlers import SSLSMTPHandler

DEFAULT_LOCATIONS = {'ios': '~/.config/dryad2dataverse',
             'linux' : '~/.config/dryad2dataverse',
             'darwin': '~/Library/Application Support/dryad2dataverse',
             'win32' : 'AppData/Roaming/dryad2dataverse',
             'cygwin' : '~/.config/dryad2dataverse'}

def argp():
    '''
    Argument parser
    '''
    description = ('Dryad to Dataverse importer/monitor. '
                   'All arguments enclosed by square brackets are OPTIONAL for '
                   'and are used for overriding defaults and/or providing sensitive'
                   'information.'
                   )

    epilog = textwrap.dedent(
             '''
                **Dryad configuration file**

                All dryadd options can be included in the file, but you can
                also specify the Dryad secret and Dataverse API key with other
                options.

                If this file is not specified,
                then the configuration file at the default location will
                be used.

                **Dryad secret**

                The dryadd program requires both an application and a secret to use.
                App IDs and secrets are provided by Dryad and can only
                be obtained directly from them at http://datadryad.org.
                The app id and secret are used to create a bearer token
                for API authentication.

                Use this option if you have not stored the secret
                in the configuration file or wish to override it.

                **Dataverse API key**

                The Dataverse API is required in order to upload both
                metadata and data. While administrator-level keys
                are recommended, any key which grants upload privileges
                should be sufficient (note: not covered by warranty).

                Use this option if you have not stored the key in the
                configuration file or wish to override it.
             ''').strip()
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=epilog)
    parser.add_argument('-c', '--config-file',
                        help=textwrap.dedent(
                            f'''
                                Dryad configuration file.
                                Default:
                                {DEFAULT_LOCATIONS[sys.platform]}/dryad2dataverse_config.yml
                                ''').strip(),
                        required=False,
                        default=f'{DEFAULT_LOCATIONS[sys.platform]}/dryad2dataverse_config.yml',
                        dest='config')
    parser.add_argument('-s', '--secret',
                        help='Secret for Dryad API.',
                        required=False,
                        dest='secret')
    parser.add_argument('-k', '--api-key',
                        help='Dataverse API key',
                        required=False,
                        dest='api_key')
    parser.add_argument('-v', '--verbosity',
                        help='Verbose output',
                        required=False,
                        action='store_true')
    parser.add_argument('--version', action='version',
                        version='dryad2dataverse ' + dryad2dataverse.__version__,
                        help='Show version number and exit')

    return parser

def new_content(serial, **kwargs):
    '''
    Creates content for new study upload message (potentially redundant
    with Dataverse emailer).

    Parameters
    ----------
    serial : dryad2dataverse.serializer.Serializer
    **kwargs
        Keyword arguments. Just pass dryad2dataverse.config.Config
    '''
    dv_link = (kwargs['dv_url'] +
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

def changed_content(serial, monitor, **kwargs):
    '''
    Creates content for file update message.

    Parameters
    ----------
    serial : dryad2dataverse.serializer.Serializer 
    monitor : dryad2dataverse.monitor.Monitor
    **kwargs
        Keyword arguments. Just pass dryad2dataverse.config.Config
    '''
    dv_link = (kwargs['dv_url'] +
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
    msg['From'] = kwargs['sending_email']
    msg['To'] = kwargs['recipients']
    content = __clean_msg(msgtxt[1], max(width, 1000))
    msg.set_content(content)

    server = smtplib.SMTP_SSL(kwargs['smtp_server'], kwargs.get('ssl_port', 465))

    server.login(kwargs['sending_email_username'], kwargs['email_send_password'])
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

def get_records(mod_date=None, verbosity=True, **kwargs):
    '''
    returns a tuple of ((doi, metadata), ...). Dryad searches return complete
    study metadata from the search, surprisingly.

    mod_date : str
        UTC datetime string in the format suitable for the Dryad API.
        eg. 2021-01-21T21:42:40Z
        or .strftime('%Y-%m-%dT%H:%M:%SZ')
        if no mod_date is passed, all studies will be retrieved

    verbosity : bool
       Output some data to stdout

    **kwargs
        Keyword arguments. Just unpack dryad2dataverse.config.Config
    '''

    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=dryad2dataverse.config.RETRY_STRATEGY))
    headers = dryad2dataverse.config.Config.update_headers(**kwargs)
    per_page = 1
    params = {'affiliation' : kwargs['ror'],
              'per_page' : per_page}
    if mod_date:
        params['modifiedSince'] = mod_date
    stud = session.get(f'{kwargs["dry_url"]}{kwargs["api_path"]}/search', headers=headers,
                        params=params)
    records = []
    total = stud.json()['total']
    if verbosity:
        print(f'Total Records: {total}', file=sys.stdout)
    params['per_page'] = 100
    for data in range(total//100+1):
        if verbosity:
            print(f'Records page: {data+1}', file=sys.stdout)
        params['page'] = data+1
        stud = session.get(f'{kwargs["dry_url"]}{kwargs["api_path"]}/search',
                            headers=headers,
                            params=params)
        time.sleep(10) # don't overload their system with API calls
        stud.raise_for_status()
        records += stud.json()['_embedded']['stash:datasets']


    #return tuple([(x['identifier'], x) for x in records])
    #This can be removed when they fix the API
    return __bad_dates(tuple((x['identifier'], x)
                              for x in records),
                              mod_date)

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
    #pylint: disable=too-many-arguments, too-many-positional-arguments
    #Because consistency is for suckers and yahoo requires full hostname
    #subject = 'Dryad to Dataverse transfer error'
    subject = 'Dryad to Dataverse logger message'
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
               'dryad2dataverse.monitor',
               'dryad2dataverse.auth',
                'dryad2dataverse.config']:
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
    if val >= kwargs.get('warning_threshold',0):
        mess = ('Large number of updates detected. '
                f'{val} new studies exceeds threshold of {kwargs.get("warning_threshold", 0)}. '
                'Program execution halted.')
        print(mess, file=sys.stderr)
        subject = 'Dryad2Dataverse large update warning'
        for logme in kwargs.get('loggers'):
            logme.warning(mess)
        notify(msgtxt=(subject, mess),
               **kwargs)
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
            print(f'{key}: {value}', file=sys.stdout)

def anonymizer(args: argparse.Namespace) -> dict:
    '''
    Redacts sensitive info for the log when parsing arguments and returns a dictionary
    with cleaner values.
    '''
    clean_me = args.__dict__.copy()#Don't work on the real thing!
    cleanser = {x : 'REDACTED' for x in ['secret', 'api_key']}
    clean_me.update(cleanser)
    return clean_me

def bulklog(message, *logfuncs):
    '''
    Convenience logging function

    message : str
        log message
    logfuncs: logging.Logger[.debug, .info, etc. method]
    '''
    for log in logfuncs:
        log('%s', message)

def test_config(cfile:pathlib.Path):
    '''
    Ensure that the config file can be loaded, and if not
    raise a helpful error because it can't be logged yet

    Parameters
    ----------
    cfile : pathlib.Path
        Config yaml file
    '''
    try:
        with open(cfile.expanduser().absolute(), encoding='utf-8') as y:
            yaml.safe_load(y)
    except yaml.YAMLError as e:
        print('Configuration file error', file=sys.stdout)
        print(e, file=sys.stderr)
        sys.exit()

def main():
    '''
    Primary function
    '''
    #pylint: disable=too-many-branches, too-many-locals, too-many-statements
    args = argp().parse_args()
    configfile = pathlib.Path(args.config)
    test_config(configfile)
    config = dryad2dataverse.config.Config(configfile.parent, configfile.name)
    for val in ['api_key', 'secret']:
        if getattr(args,val):
            config[val] = getattr(args,val)
    #TODONE remove this for prod
    config['token'] = dryad2dataverse.auth.Token(**config)

    logpath = pathlib.Path(config['log']).expanduser().absolute()
    logpath.parent.mkdir(parents=True, exist_ok=True)

    logger = rotating_log(logpath,
                          level=logging.getLevelName(config['loglevel'].upper()))
    elog = email_log(config['smtp_server'],
                     config['sending_email'],
                     config['recipients'],
                     (config['sending_email_username'], config['email_send_password']),
                     port=config['ssl_port'],
                     level = logging.getLevelName(config['email_loglevel'].upper()))
    logger.info('Beginning update process')
    for logme in [elog, logger]:
        logme.debug('Command line arguments: %s' , pprint.pformat(anonymizer(args)))

    monitor = dryad2dataverse.monitor.Monitor(**config)
    #copy the database to make a backup, because paranoia is your friend
    db_full = pathlib.Path(config['dbase']).expanduser().absolute()
    if db_full.exists():
        try:
            shutil.copyfile(db_full,
                            pathlib.Path(db_full.parent,
                                         db_full.stem + '_' +
                                         datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') +
                                         db_full.suffix)
                            )
        except FileNotFoundError:
            for _ in [logger, elog]:
                _.exception('Database not found: %s', config['dbase'])
            print(f'Database not found: {config["dbase"]}', file=sys.stderr)
            sys.exit()
    #list comprehension includes untimestamped dbase name, hence 2+
    fnames = glob.glob((str(pathlib.Path(db_full.parent,
                           db_full.stem + '*' + db_full.suffix))))
    fnames.remove(str(db_full))
    fnames.sort(reverse=True)
    fnames = fnames[config['number_of_backups']:]
    for fil in fnames:
        os.remove(fil)
        logger.info('Deleted database backup: %s', fil)
    logger.info('Last update time: %s', monitor.lastmod)
    #get all updates since the last update check
    updates = get_records(monitor.lastmod,
                          verbosity=args.verbosity,
                          **config)
    logger.info('Total new files: %s', len(updates))
    elog.info('Total new files: %s', len(updates))
    checkwarn(val=len(updates) if not config['test_mode'] else
              min(config['test_mode_limit'], len(updates)),
              loggers=[logger],
              **config)

    if config['test_mode']:
        for _ in [logger, elog]:
            _.warning('Test mode is ON - number of updates limited to %s',
                       config['test_mode_limit'])
    #update all the new files
    verbo(args.verbosity, **{'Total to process': len(updates)})

    try:
        count = 0
        testcount = 0
        for doi in updates:
            if config['test_mode'] and (testcount >= config['test_mode_limit']):
                logger.info('Test limit of %s reached', config['test_mode_limit'])
                break
            count += 1
            logger.info('Start processing %s of %s', count, len(updates))
            logger.info('DOI: %s, Dryad URL: https://datadryad.org/stash/dataset/%s',
                        doi[0], doi[0])
            if not updates:
                break #no new files in this case
            #use get in this case because people *will* have nothing to exclude
            if doi[0] in config.get('exclude_list',[]):
                logger.warning('Skipping excluded doi: %s', doi[0])
                continue
            #Create study object
            study = dryad2dataverse.serializer.Serializer(doi[0], **config)
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
            transfer = dryad2dataverse.transfer.Transfer(study, **config)
            transfer.test_api_key()
            #Now start the action
            if update_type == 'new':
                logger.info('New study: %s, %s', doi[0], doi[1]['title'])
                logger.info('Uploading study metadata')
                transfer.upload_study(targetDv=config['target'])
                #New files are in now in monitor.diff_files()['add']
                #with 2 Feb 2022 API change
                #so we can ignore them here
                logger.info('Uploading Dryad JSON metadata')
                transfer.upload_json()
                transfer.set_correct_date()
                notify(new_content(study, **config),
                       **config)
                testcount+=1

            elif update_type == 'updated':
                logger.info('Updated metadata: %s', doi[0])
                logger.info('Updating metadata')
                transfer.upload_study(dvpid=study.dvpid)
                #remove old JSON files
                transfer.delete_dv_files(monitor.get_json_dvfids(study))
                transfer.upload_json()
                transfer.set_correct_date()
                notify(changed_content(study, monitor, **config),
                       **config)

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
                                      force_unlock=config['force_unlock'])
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
                     f'Log available at: {config["log"]}'))
        notify(finished, **config)

    except dryad2dataverse.exceptions.DataverseBadApiKeyError as api_err:
        logger.exception(api_err)
        elog.exception(api_err)
        print(f'Error: {api_err}. Exiting. For details see log at {args.log}.',
              file=sys.stderr)
        sys.exit()#graceful exit is graceful

    except Exception as err: # pylint: disable=broad-except
        elog.exception('%s\nCritical failure with DOI: %s : %s\n%s', err,
                       doi[0], doi[1]['title'], doi[1].get('sharingLink'),
                       stack_info=True, exc_info=True)
        logger.exception('%s\nCritical failure with DOI: %s : %s\n%s', err,
                         doi[0], doi[1]['title'], doi[1].get('sharingLink'),
                         stack_info=True, exc_info=True)
        print(f'Error: {err}. Exiting. For details see log at {config["log"]}.',
              file=sys.stderr)
        sys.exit()

if __name__ == '__main__':
    main()
