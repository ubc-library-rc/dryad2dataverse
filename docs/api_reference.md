---
layout: default
title: Detailed API reference
nav_order: 15
---

<a name="dryad2dataverse"></a>
# dryad2dataverse

Dryad to Dataverse utilities.

Modules included:

    dryad2dataverse.constants : "Constants" for all modules

    dryad2dataverse.serializer : Download and serialize Dryad 
    JSON to Dataverse JSON

    dryad2dataverse.transfer : metadata and file transfer
    utilities

    dryad2dataverse.monitor : Monitoring and database tools
    for persistent transfers

    dryad2dataverse.exceptions : Custom exceptions

<a name="dryad2dataverse.monitor"></a>
# dryad2dataverse.monitor

Dryad/Dataverse status tracker. Monitor creates a singleton object which
writes to a SQLite database. Methods will (generally) take either a
dryad2dataverse.serializer.Serializer instance or
dryad2dataverse.transfer.Transfer instance

<a name="dryad2dataverse.monitor.Monitor"></a>
## Monitor Objects

```python
class Monitor(object)
```

The Monitor object is a tracker and database updater, so that
Dryad files can be monitored and updated over time. Monitor is a singleton,
but is not thread-safe.

<a name="dryad2dataverse.monitor.Monitor.__new__"></a>
#### \_\_new\_\_

```python
 | __new__(cls, dbase=None, *args, **kwargs)
```

Creates a new singleton instance of Monitor

<a name="dryad2dataverse.monitor.Monitor.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(dbase=None, *args, **kwargs)
```

Initialize the Monitor instance.

dbase : str
    Complete path to desired location of tracking database
    (eg: /tmp/test.db)
    Defaults to dryad2dataverse.constants.DBASE

<a name="dryad2dataverse.monitor.Monitor.__del__"></a>
#### \_\_del\_\_

```python
 | __del__()
```

Commits all database transactions on object deletion

<a name="dryad2dataverse.monitor.Monitor.status"></a>
#### status

```python
 | status(serial)
```

Returns text output of 'new', 'unchanged', 'updated' or 'filesonly'
'new' is a completely new file
'unchanged' is no changes at all
'updated' is changes to lastModificationDate AND metadata changes
'filesonly' is changes to lastModificationDate only
(which presumably indicates a file change.

serial : dryad2dataverse.serializerinstance

<a name="dryad2dataverse.monitor.Monitor.diff_metadata"></a>
#### diff\_metadata

```python
 | diff_metadata(serial)
```

Analyzes differences in metadata between current serializer
instance and last updated serializer instance.
Returns a list of field changes

serial : dryad2dataverse.serializer.Serializer instance

<a name="dryad2dataverse.monitor.Monitor.diff_files"></a>
#### diff\_files

```python
 | diff_files(serial)
```

https://docs.python.org/3/library/stdtypes.html#frozenset.symmetric_difference

Also:
tuple from string:
https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string

needsdel = set(a).superset(set(b))
__returns False if all of a not in e__

if False:
    if not set(a) - (set(a) & set(b)):
        return set(a) - (set(a) & set(b))

needsadd = set(f).issuperset(set(a))
if True: return set(f) - (set(f) & set(a))

<a name="dryad2dataverse.monitor.Monitor.get_dv_fid"></a>
#### get\_dv\_fid

```python
 | get_dv_fid(url)
```

Returns str — the Dataverse file ID from parsing a Dryad
file download link.
Normally used for determining dataverse file ids for *deletion*
in case of dryad file changes.

url : str
    *Dryad* file URL in form of
    'https://datadryad.org/api/v2/files/385819/download'

<a name="dryad2dataverse.monitor.Monitor.get_dv_fids"></a>
#### get\_dv\_fids

```python
 | get_dv_fids(filelist)
```

Returns Dataverse file IDs from a list of Dryad file tuples.

filelist : list
    list of Dryad file tuples: eg:
    [('https://datadryad.org/api/v2/files/385819/download',
      'GCB_ACG_Mortality_2020.zip',
      'application/x-zip-compressed', 23787587),
     ('https://datadryad.org/api/v2/files/385820/download',
     'Readme_ACG_Mortality.txt',
     'text/plain', 1350)]
    Generally, you would use the output from
    dryad2dataverse.monitor.Monitor.diff_files['delete']

<a name="dryad2dataverse.monitor.Monitor.get_json_dvfids"></a>
#### get\_json\_dvfids

```python
 | get_json_dvfids(serial)
```

Return a list of Dataverse file ids for dryad JSONs which were
uploaded to Dataverse.
Normally used to discover the file IDs to remove Dryad JSONs
which have changed.

serial : dryad2dataverse.serializer.Serializer instance

<a name="dryad2dataverse.monitor.Monitor.update"></a>
#### update

```python
 | update(transfer)
```

Updates the Monitor database with information from a
dryad2dataverse.transfer.Transfer instance
If a Dryad primary metadata record has changes, it will be
deleted from the database.

This method should be called after all transfers are completed,
including Dryad JSON updates, as the last action for transfer.


transfer : dryad2dataverse.transfer.Transfer instance

<a name="dryad2dataverse.monitor.Monitor.set_timestamp"></a>
#### set\_timestamp

```python
 | set_timestamp(curdate=None)
```

Adds current time to the database table. Can be queried and be used for subsequent
checking for updates. To query time, use
dataverse2dryad.monitor.Monitor.lastmod attribute.

curdate : str
    UTC datetime string in the format suitable for the Dryad API.
    eg. 2021-01-21T21:42:40Z
    or .strftime('%Y-%m-%dT%H:%M:%SZ')

<a name="dryad2dataverse.constants"></a>
# dryad2dataverse.constants

<a name="dryad2dataverse.transfer"></a>
# dryad2dataverse.transfer

This module handles data downloads and uploads from a Dryad instance to a Dataverse instance

<a name="dryad2dataverse.transfer.url_logger"></a>
#### url\_logger

`whichever` date
date=('dateOfDeposit', depDate[0].text)[0]
ie, one of distributionDate, productionDate, dateOfDeposit
params = {'persistentId' : dvn4StdyId}
            newdate = requests.put(f'{DVN4}/datasets/:persistentId/\
            citationdate',
            headers=AUTHHEAD, data=date, params=params)

<a name="dryad2dataverse.transfer.Transfer"></a>
## Transfer Objects

```python
class Transfer(object)
```

Transfers data from Drayd installation to
Dataverse installation

<a name="dryad2dataverse.transfer.Transfer.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(dryad)
```

dryad : dryad.Dryad object

<a name="dryad2dataverse.transfer.Transfer.dvpid"></a>
#### dvpid

```python
 | @property
 | dvpid()
```

Returns Dataverse study persistent ID

<a name="dryad2dataverse.transfer.Transfer.auth"></a>
#### auth

```python
 | @property
 | auth()
```

Returns datavese authentication header

<a name="dryad2dataverse.transfer.Transfer.fileJson"></a>
#### fileJson

```python
 | @property
 | fileJson()
```

Despite what you may think, the uniquely identifying integer
describing a dataset is not dryadJson['id']

It's actually the integer part of
testCase._dryadJson['_links']['stash:version']['href']

<a name="dryad2dataverse.transfer.Transfer.files"></a>
#### files

```python
 | @property
 | files()
```

Returns a list of lists with:
[Download_location, filename, mimetype, size, description, md5digest]
This is mutable; downloading a file will add md5 info if not available

<a name="dryad2dataverse.transfer.Transfer.oversize"></a>
#### oversize

```python
 | @property
 | oversize()
```

Returns list of files exceeding Dataverse ingest limit
dryad2dataverse.constants.MAX_UPLOAD

<a name="dryad2dataverse.transfer.Transfer.doi"></a>
#### doi

```python
 | @property
 | doi()
```

Returns Dryad DOI

<a name="dryad2dataverse.transfer.Transfer.upload_study"></a>
#### upload\_study

```python
 | upload_study(url=None, apikey=None, timeout=45, **kwargs)
```

Uploads Dryad study metadata to target dataverse or updates existing.
targetDv kwarg creates new, dvpid kwarg updates.

url : str
    URL of Dataverse instance. Defaults to constants.DVURL
apikey : str
    API key of user. Defaults to contants.APIKEY
timeout : int
    timeout on POST request

KEYWORD ARGUMENTS
One of these is required. Supplying both or neither raises a NoTargetError
targetDv : str
    short name of target dataverse. Required if new dataset.
    Specify as targetDV=value
dvpid = str
    Dataverse persistent ID (for updating metadata)
    This is not required for new uploads, specify as dvpid=value
OPTIONAL KEYWORD ARGUMENTS

<a name="dryad2dataverse.transfer.Transfer.download_file"></a>
#### download\_file

```python
 | download_file(url, filename, tmp=None, size=None, chk=None, timeout=45)
```

Downloads file via requests streaming and saves to constants.TMP
returns md5sum on success and an exception on failure
url : str
    URL of download
filename : str
    Output file name
timeout: int
    Requests timeout
tmp : str
    Temporary directory for downloads.
    Defaults to dryad2dataverse.constants.TMP
size : int
    Reported file size in bytes.
    Defaults to dryad2dataverse.constants.MAX_UPLOAD
chk : str
    md5 sum of file (if available)

<a name="dryad2dataverse.transfer.Transfer.download_files"></a>
#### download\_files

```python
 | download_files(files=None)
```

Bulk downloader for files.
files: list
    items in list can be tuples or list with a minimum of:
    (dryaddownloadurl, filenamewithoutpath, [md5sum])

    md5 sum should be the last member of the tuple.

    Defaults to self.files

    Normally used without arguments to download all the associated
    files with a Dryad study

<a name="dryad2dataverse.transfer.Transfer.upload_file"></a>
#### upload\_file

```python
 | upload_file(dryadUrl=None, filename=None, mimetype=None, size=None, descr=None, md5=None, studyId=None, dest=None, fprefix=None, timeout=300)
```

Uploads file to Dataverse study. Returns a tuple of the
dryadFid (or None) and Dataverse JSON from the POST request.
Failures produce JSON with different status messages
rather than raising an exception.

filename : str
    Filename (not including path)
mimetype : str
    Mimetype of file
size : int
    Size in bytes
studyId : str
    Persistent study identifier for dataverse.
    Defaults to Transfer.dvpid
dest : str
    Destination dataverse installation url.
    Defaults to constants.DVURL
md5 : str
    md5 checksum for file
fprefix : str
    Path to file, not including a trailing slash
timeout : int
    Timeout in seconds for POST request
dryadUrl : str
    Dryad download URL if you want to include a dryad file id

<a name="dryad2dataverse.transfer.Transfer.upload_files"></a>
#### upload\_files

```python
 | upload_files(files=None, pid=None, fprefix=None)
```

Uploads multiple files to study with persistentId pid.
Returns a list of the original tuples plus JSON responses.

files: list
    list contains a tuple with
    (dryadDownloadURL, filename, mimetype, size)
pid : str
    defaults to self.dvpid, which is generated by calling
    dryad2dataverse.transfer.Transfer.upload_study()

<a name="dryad2dataverse.transfer.Transfer.upload_json"></a>
#### upload\_json

```python
 | upload_json(studyId=None, dest=None)
```

Uploads Dryad json as a separate file for archival purposes
pid : str
    Dataverse pid

<a name="dryad2dataverse.transfer.Transfer.delete_dv_file"></a>
#### delete\_dv\_file

```python
 | delete_dv_file(dvfid, dvurl=None, key=None)
```

Deletes files from Dataverse target given a dataverse file ID.
This information is unknowable unless discovered by
dryad2dataverse.monitor.Monitor or by other methods.

Returns 1 on success (204 response), or 0 on other response.

dvurl : str
    Base URL of dataverse instance.
    Defaults to dryad2dataverse.constants.DVURL

dvfid :
    Dataverse file ID number

<a name="dryad2dataverse.transfer.Transfer.delete_dv_files"></a>
#### delete\_dv\_files

```python
 | delete_dv_files(dvfids=None, dvurl=None, key=None)
```

Deletes all files in list of dataverese file file ids from dataverse.
dvfids : list
    List of dataverse fids.
    Defaults to dryad2dataverse.transfer.Transfer.fileDelRecord
dvurl : str
    Base URL of Dataverse. Defaults to dryad2dataverse.constants.DVURL
key : str
    API key for Dataverse. Defaults to dryad2dataverse.constants.APIKEY

<a name="dryad2dataverse.serializer"></a>
# dryad2dataverse.serializer

Serializes Dryad JSON to Dataverse JSON, with a few other
associated file utilities

<a name="dryad2dataverse.serializer.Serializer"></a>
## Serializer Objects

```python
class Serializer(object)
```

Serializes Dryad JSON to Dataverse JSON

<a name="dryad2dataverse.serializer.Serializer.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(doi)
```

doi : str
    DOI of Dryad study. Required for downloading.
    eg: 'doi:10.5061/dryad.2rbnzs7jp'

<a name="dryad2dataverse.serializer.Serializer.fetch_record"></a>
#### fetch\_record

```python
 | fetch_record(url=None, timeout=45)
```

Fetches Dryad study record JSON from Dryad V2 API at
https://datadryad.org/api/v2/datasets/
Saves to Dryad._dryadJson
url : str
    Dryad instance base URL (eg: 'https://datadryad.org')
timeout : int
    timeout in seconds. Default 45

<a name="dryad2dataverse.serializer.Serializer.id"></a>
#### id

```python
 | @property
 | id()
```

Returns Dryad unique ID.

The 'id' is not dryadjson['id']
It's actually the integer part of
testCase._dryadJson['_links']['stash:version']['href']

The documentation, naturally, is not clear that this is the case.

<a name="dryad2dataverse.serializer.Serializer.dryadJson"></a>
#### dryadJson

```python
 | @property
 | dryadJson()
```

Returns Dryad study JSON

<a name="dryad2dataverse.serializer.Serializer.dvJson"></a>
#### dvJson

```python
 | @property
 | dvJson()
```

Returns Dataverse study JSON

<a name="dryad2dataverse.serializer.Serializer.fileJson"></a>
#### fileJson

```python
 | @property
 | fileJson(timeout=45)
```

Returns JSON from call to Dryad API /files/{id},
where the ID is parsed from the Dryad JSON

<a name="dryad2dataverse.serializer.Serializer.files"></a>
#### files

```python
 | @property
 | files()
```

Returns a list of tuples with:
(Download_location, filename, mimetype, size, description,
digestType, md5sum)
At this time only md5 is supported

<a name="dryad2dataverse.serializer.Serializer.oversize"></a>
#### oversize

```python
 | @property
 | oversize(maxsize=None)
```

Returns a list of Dryad files whose size value
exceeds maxsize. Maximum size defaults to
dryad2dataverse.constants.MAX_UPLOAD

<a name="dryad2dataverse.exceptions"></a>
# dryad2dataverse.exceptions

Custom exceptions for error handling

<a name="dryad2dataverse.exceptions.Dryad2DataverseError"></a>
## Dryad2DataverseError Objects

```python
class Dryad2DataverseError(Exception)
```

Base exception class for Dryad2Dataverse errors

<a name="dryad2dataverse.exceptions.NoTargetError"></a>
## NoTargetError Objects

```python
class NoTargetError(Dryad2DataverseError)
```

No dataverse target supplied error

<a name="dryad2dataverse.exceptions.DownloadSizeError"></a>
## DownloadSizeError Objects

```python
class DownloadSizeError(Dryad2DataverseError)
```

Raised when download sizes don't match reported
Dryad file size.

<a name="dryad2dataverse.exceptions.HashError"></a>
## HashError Objects

```python
class HashError(Dryad2DataverseError)
```

Raised on hex digest mismatch

<a name="dryad2dataverse.exceptions.DatabaseError"></a>
## DatabaseError Objects

```python
class DatabaseError(Dryad2DataverseError)
```

Tracking database error

<a name="dryad2dataverse.exceptions.DataverseUploadError"></a>
## DataverseUploadError Objects

```python
class DataverseUploadError(Dryad2DataverseError)
```

Returned on not OK respose

<a name="dryad2dataverse.exceptions.DataverseDownloadError"></a>
## DataverseDownloadError Objects

```python
class DataverseDownloadError(Dryad2DataverseError)
```

Returned on not OK respose

