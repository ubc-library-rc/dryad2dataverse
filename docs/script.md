---
layout: default
title:  
nav_order: 4
---

# Automated migrator and tracker - dryadd

---

While it's all very nice that there's code that can migrate Dryad material to Dataverse, many users are not familiar enough with Python/programming or, just as likely, don't want to have to program things themselves. Anyone transferring from Dryad to Dataverse is likely doing a variant of the same thing, which consists of:

* Finding new Dryad material, usually from their own institution
* Moving it to Dataverse

and possibly: 

* Checking for updates and handling **those** automatically

Included with **dryad2dataverse** package is a console application called **dryadd** which does all of this. Or, if you don't even want to install dryad2dtaverse, [binary files for Windows, MacOS and Linux](https://github.com/ubc-library-rc/dryad2dataverse/releases). Depending on what computing platform and installation method you use, the application will be called `dryadd.py, dryadd`, `dryadd_linux` or `dryadd.exe`. Note that there are a wide variety of system architectures available, but not all of them.

**The most current version of _dryadd_ will always be available if you install via _pip_. The binary files may lag behind and/or not get every release** 

Note that these utilities are *console* programs. That is, they do not have a GUI and are meant to be run from the command line in a Windows DOS prompt or PowerShell session or a terminal in the case of other platforms.

### An important caveat

This product **will not** publish anything in a Dataverse installation (at this time, at least). This is intentional to allow a human-based curatorial step before releasing any data onto an unsuspecting audience. There's no error like systemic error, so not automatically releasing material should help alleviate this.

### Usage

The implementation is relatively straightforward. Simply supply the required parameters and the software should do the rest. The help menu below is available from the command line by either running the script without inputs or by using the `-h` switch.


```nohighlight
usage: dryadd [-h] [-u URL] -k KEY -t TARGET -e EMAIL -s USER -r RECIPIENTS [RECIPIENTS ...] -p PWD [--server MAILSERV] [--port PORT] -c CONTACT -n CNAME [-v] -i ROR [--tmpfile TMP]
              [--db DBASE] [--log LOG] [-l] [-x EXCLUDE [EXCLUDE ...]] [-b NUM_BACKUPS] [-w] [--warn-threshold WARN] [--version]

Dryad to Dataverse importer/monitor. All arguments NOT enclosed by square brackets are required for the script to run but some may already have defaults, specified by "Default". The
"optional arguments" below refers to the use of the option switch, (like -u), meaning "not a positional argument."

options:
  -h, --help            show this help message and exit
  -u URL, --dv-url URL  Destination Dataverse root url. Default: https://borealisdata.ca
  -k KEY, --key KEY     REQUIRED: API key for dataverse user
  -t TARGET, --target TARGET
                        REQUIRED: Target dataverse short name
  -e EMAIL, --email EMAIL
                        REQUIRED: Email address which sends update notifications. ie: "user@website.invalid".
  -s USER, --user USER  REQUIRED: User name for SMTP server. Check your server for details.
  -r RECIPIENTS [RECIPIENTS ...], --recipient RECIPIENTS [RECIPIENTS ...]
                        REQUIRED: Recipient(s) of email notification. Separate addresses with spaces
  -p PWD, --pwd PWD     REQUIRED: Password for sending email account. Enclose in single quotes to avoid OS errors with special characters.
  --server MAILSERV     Mail server for sending account. Default: smtp.mail.yahoo.com
  --port PORT           Mail server port. Default: 465. Mail is sent using SSL.
  -c CONTACT, --contact CONTACT
                        REQUIRED: Contact email address for Dataverse records. Must pass Dataverse email validation rules (so "test@test.invalid" is not acceptable).
  -n CNAME, --contact-name CNAME
                        REQUIRED: Contact name for Dataverse records
  -v, --verbosity       Verbose output
  -i ROR, --ror ROR     REQUIRED: Institutional ROR URL. Eg: "https://ror.org/03rmrcq20". This identifies the institution in Dryad repositories.
  --tmpfile TMP         Temporary file location. Default: /tmp
  --db DBASE            Tracking database location and name. Default: $HOME/dryad_dataverse_monitor.sqlite3
  --log LOG             Complete path to log. Default: /var/log/dryadd.log
  -l, --no_force_unlock
                        No forcible file unlock. Required if /lock endpint is restricted
  -x EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        Exclude these DOIs. Separate by spaces
  -b NUM_BACKUPS, --num-backups NUM_BACKUPS
                        Number of database backups to keep. Default 3
  -w, --warn-too-many   Warn and halt execution if abnormally large number of updates present.
  --warn-threshold WARN
                        Do not transfer studies if number of updates is greater than or equal to this number. Default: 15
  --version             Show version number and exit
```
### Requirements

**Software**

* If you installed using _pip_ the requirements will be filled by default (see the [installation document](installation.md) for more details).

* If using a binary file, it must be supported by your operating system and system architecture (eg. Intel Mac).

**Hardware**

* You will need sufficient storage space on your system to hold the contents of the largest Dryad record that you are transferring. This is not necessarily a small amount; Dryad studies can range into the tens or hundreds of Gb, which means that a "normal" `/tmp` directory will normally not have enough space allocated to it. The software will work on one study at a time and delete the files as it goes, but there are studies in the Dryad repository that are huge, even if most of them are quite small.

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

**A note about GMail**

Dryad2dataverse is now set up to use yahoo email by default, because it doesn't require two-factor authentication to use. If you decide to use Google mail, you will need to follow the procedure outlined here <https://support.google.com/accounts/answer/185833?hl=en>. Note that it will require enabling two-factor authentication.

**Updates to Dryad studies**

The software is designed to automatically update changed studies. Simply run the utility with the same parameters as the previous run and any studies in Dataverse will be updated


**Miscellaneous**

The **dryadd/.py/.exe** works best if run at intervals. This can easily be achieved by adding it to your system's _crontab_ or using the Windows scheduler. Currently it does not run as a system or service, although it may in the future.

Dryad itself is constantly changing, as is Dataverse. Although the software should work predictably, changes in both the Dryad API and Dataverse API can cause unforeseen consequences.

To act as a backup against catastrophic error, the monitoring database is automatically copied and renamed with a timestamp. Although the default number of backups is 3 by default, any number of backups can be kept. Obviously, if you run the software once a minute this isn't helpful, but it could be if you update once a month.

