---
layout: default
title:  
nav_order: 4
---

# Automated migrator and tracker - **dryadd.py**

---

While it's all very nice that there's code that can migrate Dryad material to Dataverse, many users are not familiar enough with Python/programming or, just as likely, don't want to have to program things themselves. Anyone transferring from Dryad to Dataverse is likely doing a variant of the same thing, which consists of:

* Finding new Dryad material, usually from their own institution
* Moving it to Dataverse

and possibly: 

* Checking for updates and handling **those** automatically

Included with **dryad2dataverse** is a script and possibly binary files which do exactly this. The binary files, if available for your operating system, should not even require a Python installation; they are self-contained programs which will run and monitor the copying process.

### An important caveat

This product **will not** publish anything in a Dataverse installation (at this time, at least). This is intentional to allow a human-based curatorial step before releasing any data onto an unsuspecting audience. There's no error like systematic error, so not automatically releasing material should help alleviate this.

### Requirements

**Software**

* If you are using the pure Python version of the migrator (ie, **dryadd.py**) and you have successfully installed the **dryad2dataverse** library, the requirements will be filled by default (see the [installation document](installation.md) for more details)

* If using a binary file, it must be supported by your operating system and system architecture (eg. Intel Mac)

**Hardware**

* You will need sufficient storage space on your system to hold the contents of the largest Dryad record that you are transferring. This is not necessarily a small amount; Dryad studies can range into the tens or hundreds of Gb, which means that a "normal" `/tmp` directory will normally not have enough space allocated to it.

**Other**

* A destination Dataverse must exist, and you should know its short name
* The API key must have sufficient privileges to create new studies and upload data
* You will need an email address for contact information as this is a required field in Dataverse (but not necessarily in Dryad) and a name to go with it. For example, `i_heart_data@test.invalid` and `Dataverse Support`. Note: Use a valid email address (unlike the example) because uploads will also fail if the address is invalid.
* An additional email to receive update and error notifications.
* A place to store your sqlite3 tracking database

**Miscellaneous**

This software is still new; it doesn't actually run as a daemon [yet]. To update, just run the script again at whatever interval you desire, and it will find Dryad material that has been updated since the last run.

At this time, the best solution would be to run **dryadd.py** at predifined intervals using `cron`.

To act as a backup against catastrophic error, the database is automatically copied to $DBASE.bak. Obviously, if you check once a minute this isn't helpful, but it could be if you update once a month.


### Usage

The implementation is relatively straightforward. Simply supply the required parameters and the software should do the rest.

```
usage: dryadd.py [-h] [-u URL] -k KEY -t TARGET [-e USER] [-r RECIPIENTS] [-p PWD] [--server MAILSERV] [--port PORT] -c CONTACT -n CNAME [-v] -i ROR [--tmpfile TMP] [--db DBASE]

Dryad to Dataverse import daemon. Arguments shown in square brackets (ie []) are REQUIRED, despite being shown as optional.

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --dv-url URL  Destination dataverse root url. Eg: https://dataverse.scholarsportal.info
  -k KEY, --key KEY     API key for dataverse user
  -t TARGET, --target TARGET
                        Target dataverse short name
  -e USER, --email USER
                        Username for email addresswhich sends update notifications.
  -r RECIPIENTS, --recipient RECIPIENTS
                        Recipient of email notification
  -p PWD, --pwd PWD     Password for email account
  --server MAILSERV     Mail server. Eg. smtp.gmail.com
  --port PORT           Mail server port
  -c CONTACT, --contact CONTACT
                        Contact email for Dataverse records
  -n CNAME, --contact-name CNAME
                        Contact name for Dataverse records
  -v, --verbosity       Verbose output
  -i ROR, --ror ROR     Institutional ROR url. Eg: https://ror.org/03rmrcq20
  --tmpfile TMP         Temporary file location (if not /tmp)
  --db DBASE            Tracking database location and name if not $HOME/dryad_dataverse_monitor.sqlite3
```
