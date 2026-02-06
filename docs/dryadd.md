---
layout: default
title: The dryadd application 
nav_order: 4
---

# Dryadd: move your material with almost no effort.
---

The **dryadd** application is designed to operate with minimal effort after simply filling in the blanks in a configuration file, so that you're one and done.

---
### Important
This product **will not publish** anything in a Dataverse installation. This is intentional to allow a human-based curatorial step before releasing any data onto an unsuspecting audience.

**Publishing must be done manually or via automation such as found in [dataverse_utils](https://ubc-library-rc.github.io/dataverse_utils')**

---

## Usage

**Dryadd** operates based on simple [YAML](https://en.wikipedia.org/wiki/YAML) configuration file. The first run of **dryadd** will generate one if there is not one present at its stated location.

Defaults are:

|platform|default|
|--------|-------|
|ios|~/.config/dryad2dataverse/dryad2dataverse_config.yml|
|linux|~/.config/dryad2dataverse/dryad2dataverse_config.yml|
|darwin|~/Library/Application Support/dryad2dataverse/dryad2dataverse_config.yml|
|win32|~/AppData/Roaming/dryad2dataverse/dryad2dataverse_config.yml|
|cygwin|~/.config/dryad2dataverse/dryad2dataverse_config.yml|

If you do not want to use the default location for your platform, you can specify a file with the `-c` switch. For example `dryadd -c /tmp/testme.yml` will use the file '/tmp/testme.yml' or create one if it does not exist.

Once it's configured correctly, you can run the **dryadd** application simply by running `dryadd`.

If you don't wish to store your Dryad secret and Dataverse API key in the configuration file, they may be specified using the `-s` and `-k` switches respectively, ie: `dryadd -s [dryad_secret] -k [dataverse_key]`

If you forget all this, help is available via `dryadd -h`. The help is long, so run it through a pager: `dryadd -h |more`. It is also reproduced below.

### YAML configuration file

The configration file is self-documenting, and is reproduced here for your convenience.

```yaml
#Sample configuration file dryad2dataverse
#It will *not* work unless you fill it in, because both
#Dryad and Dataverse require user information.

#------
#Dryad configuration
#------
#Dryad base URL
dry_url: https://datadryad.org
#API path
api_path: /api/v2
#Application ID (contact Dryad to get an institutional account)
app_id: null
#Secret key, should have come with your application ID.
secret: null

#------
#Dataverse configuration
#------
#Base url of Dataverse instance (eg: https://borealisdata.ca)
dv_url: null 
#Dataverse API KEY
api_key: null
#Maximum upload size in bytes (contact Dataverse administrator for value if unknown)
max_upload: 3221225472
#Contact email address for Dataverse record, eg: research.data@test.invalid
dv_contact_email: null
#Contact name associated with the address (like, say, "[University] Research Data Services")
dv_contact_name: null
#Dataverse target collection shortname
target: Null
#To stop conversion to tabular data, add extensions here. Tabular processing can cause
#problems and the original files were not processed that way. It is recommended to
#keep this as is and add more if required.
notab:
- .sav
- .por
- .zip
- .csv
- .tsv
- .dta
- .rdata
- .xslx
- .xls

#------
#Monitoring configuration
#------
#Location of persistent database which tracks transfers over time.
#If you ever move the database, you must change this to the new location or everything will be transferred again
dbase: ~/dryad_dataverse_monitor.sqlite3

#------
#Transfer information
#------
#Institutional ROR. Find your ROR here: https://ror.org/search
ror: null

#Location of temporarily downloaded files. This doesn't default to the normal
#temp file location because the files can be gigantic, and so is manually specified
tempfile_location: /tmp

#Email address which sends update notifications. 
#Note, OATH2 is not supported. Yahoo is free 
#and you may as well use it
sending_email: null
#Account username. Check provider for details
sending_email_username: null
#Account password. Check provider for details; may be different than
#an ordinary account if using an application
email_send_password: null
#SMTP server configuration
smtp_server: smtp.mail.yahoo.com
#Mail is sent using SSL; check with provider for details
ssl_port: 465
#List of email addresses that will receive notifications
recipients: 
- null
#location of dryadd log
#include full file name: eg: /var/log/dryadd.log
#The default below will exist but is a terrible place
#for a log so you should change it.
log: ~/dryadd.log
#level at which to write a log message. Select from:
# debug, info, warning, error or critical
loglevel: warning
#level at which to send an email message about problems.
#Same levels as above, obviously.
email_loglevel: warning

#Forcible file unlock. Forcible file unlocking requires admin privileges in Dataverse.
#Normally you wouldn't need to change this.
force_unlock: false
#Number of database backups to keep
number_of_backups: 3

#------
#Troubleshooting options
#------
#Warn if too many new updates. Occasionally, Dryad will change their
#"persistent" IDs and then everything looks new, which causes everything
#to be loaded again. It's recommended that this be "true" to stop an accidental
#complete reingest
warn_too_many: true
#Number of new Dryad surveys which will trigger a warning and stop execution.
#This is to prevent accidentally ingesting thousands of surveys if you 
#misconfigure something
warning_threshold: 15
#Force dryadd into test mode
test_mode: false
#Test mode - only transfer first [n] of the total number of (new) records. 
#Old ones will still be updated, though
test_mode_limit: 5


#------
#Exclusion list
#------
#Dryad DOIs to exclude from transfers. This is usually because the files in the
#study are too large to be ingested into Dataverse, but may also be used for
#studies with errors or any other reason
#
#IMPORTANT!
#
#Uncomment below and add dois in place of null, one per line.
#exclude_list:
#- null
```

### Application help

```no-highlight
dryadd -h

usage: dryadd [-h] [-c CONFIG] [-s SECRET] [-k API_KEY] [-v] [--version]

Dryad to Dataverse importer/monitor. All arguments enclosed by square brackets are OPTIONAL for and are used for overriding defaults and/or providing sensitive information.

options:
  -h, --help            show this help message and exit
  -c, --config-file CONFIG
                        Dryad configuration file.
                        Default:
                        ~/Library/Application Support/dryad2dataverse/dryad2dataverse_config.yml
  -s, --secret SECRET   Secret for Dryad API.
  -k, --api-key API_KEY
                        Dataverse API key
  -v, --verbosity       Verbose output
  --version             Show version number and exit

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
```

## Requirements

**Hardware**

* You will need sufficient storage space on your system to hold the contents of the largest Dryad record that you are transferring. This is not necessarily a small amount; Dryad studies can range into the tens or hundreds of Gb, which means that a "normal" `/tmp` directory will normally not have enough space allocated to it. This is why it is user-specifiable. The software will work on one study at a time and delete the files as it goes, but there are studies in the Dryad repository that are huge, even if most of them are quite small.

**Other**

* A destination Dataverse must exist, and you should know its short name.
* The API key must have sufficient privileges to create new studies and upload data.
* You will need an email address for contact information as this is a required field in Dataverse (but not necessarily in Dryad) and a name to go with it. For example, `i_heart_data@test.invalid` and `Dataverse Support`. Note: Use a valid email address (unlike the example) because uploads will also fail if the address is invalid.
* Information for an email address which *sends* notifications
	* The sending email address  ("user@test.invalid")
	* The user name (usually, but not always, "user" from "user@test.invalid")
	* The password for this account
	* The smtp server address which sends mail. For example, if using gmail, it's `smtp.gmail.com`
	* The port required to send email via SSL.
* At least one email address to receive update and error notifications. This can be the same as the sender.
* A place to store your sqlite3 tracking database.

## Other items of note

**GMail**

Dryad2dataverse is now set up to use yahoo email by default, because it doesn't require two-factor authentication to use. If you decide to use Google mail, you will need to follow the procedure outlined here <https://support.google.com/accounts/answer/185833?hl=en>. Note that it will require enabling two-factor authentication.

**Updates to Dryad studies**

The software is designed to automatically update changed studies. Simply run the utility with the same parameters as the previous run and any studies in Dataverse will be updated

**Scheduling**

While **dryadd** can be run on an ad-hoc basis, you may wish to add it a scheduler such as a linux crontab or the Windows scheduler so that transfers can be made automatically.

**Miscellaneous**
Dryad itself is constantly changing, as is Dataverse. Although the software should work predictably, changes in both the Dryad API and Dataverse API can cause unforeseen consequences.

To act as a backup against catastrophic error, the monitoring database is automatically copied and renamed with a timestamp and retains a user-specified number of backups.

