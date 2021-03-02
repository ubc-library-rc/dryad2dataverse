# Table of Contents

* [dryad2dataverse](#dryad2dataverse)
* [dryad2dataverse.constants](#dryad2dataverse.constants)
* [dryad2dataverse.serializer](#dryad2dataverse.serializer)
  * [Serializer](#dryad2dataverse.serializer.Serializer)
    * [\_\_init\_\_](#dryad2dataverse.serializer.Serializer.__init__)
    * [fetch\_record](#dryad2dataverse.serializer.Serializer.fetch_record)
    * [id](#dryad2dataverse.serializer.Serializer.id)
    * [dryadJson](#dryad2dataverse.serializer.Serializer.dryadJson)
    * [dryadJson](#dryad2dataverse.serializer.Serializer.dryadJson)
    * [embargo](#dryad2dataverse.serializer.Serializer.embargo)
    * [dvJson](#dryad2dataverse.serializer.Serializer.dvJson)
    * [fileJson](#dryad2dataverse.serializer.Serializer.fileJson)
    * [files](#dryad2dataverse.serializer.Serializer.files)
    * [oversize](#dryad2dataverse.serializer.Serializer.oversize)
* [dryad2dataverse.transfer](#dryad2dataverse.transfer)
  * [Transfer](#dryad2dataverse.transfer.Transfer)
    * [\_\_init\_\_](#dryad2dataverse.transfer.Transfer.__init__)
    * [dvpid](#dryad2dataverse.transfer.Transfer.dvpid)
    * [auth](#dryad2dataverse.transfer.Transfer.auth)
    * [fileJson](#dryad2dataverse.transfer.Transfer.fileJson)
    * [files](#dryad2dataverse.transfer.Transfer.files)
    * [oversize](#dryad2dataverse.transfer.Transfer.oversize)
    * [doi](#dryad2dataverse.transfer.Transfer.doi)
    * [set\_correct\_date](#dryad2dataverse.transfer.Transfer.set_correct_date)
    * [upload\_study](#dryad2dataverse.transfer.Transfer.upload_study)
    * [download\_file](#dryad2dataverse.transfer.Transfer.download_file)
    * [download\_files](#dryad2dataverse.transfer.Transfer.download_files)
    * [force\_notab\_unlock](#dryad2dataverse.transfer.Transfer.force_notab_unlock)
    * [upload\_file](#dryad2dataverse.transfer.Transfer.upload_file)
    * [upload\_files](#dryad2dataverse.transfer.Transfer.upload_files)
    * [upload\_json](#dryad2dataverse.transfer.Transfer.upload_json)
    * [delete\_dv\_file](#dryad2dataverse.transfer.Transfer.delete_dv_file)
    * [delete\_dv\_files](#dryad2dataverse.transfer.Transfer.delete_dv_files)
* [dryad2dataverse.monitor](#dryad2dataverse.monitor)
  * [Monitor](#dryad2dataverse.monitor.Monitor)
    * [\_\_new\_\_](#dryad2dataverse.monitor.Monitor.__new__)
    * [\_\_init\_\_](#dryad2dataverse.monitor.Monitor.__init__)
    * [\_\_del\_\_](#dryad2dataverse.monitor.Monitor.__del__)
    * [lastmod](#dryad2dataverse.monitor.Monitor.lastmod)
    * [status](#dryad2dataverse.monitor.Monitor.status)
    * [diff\_metadata](#dryad2dataverse.monitor.Monitor.diff_metadata)
    * [diff\_files](#dryad2dataverse.monitor.Monitor.diff_files)
    * [get\_dv\_fid](#dryad2dataverse.monitor.Monitor.get_dv_fid)
    * [get\_dv\_fids](#dryad2dataverse.monitor.Monitor.get_dv_fids)
    * [get\_json\_dvfids](#dryad2dataverse.monitor.Monitor.get_json_dvfids)
    * [update](#dryad2dataverse.monitor.Monitor.update)
    * [set\_timestamp](#dryad2dataverse.monitor.Monitor.set_timestamp)
* [dryad2dataverse.exceptions](#dryad2dataverse.exceptions)
  * [Dryad2DataverseError](#dryad2dataverse.exceptions.Dryad2DataverseError)
  * [NoTargetError](#dryad2dataverse.exceptions.NoTargetError)
  * [DownloadSizeError](#dryad2dataverse.exceptions.DownloadSizeError)
  * [HashError](#dryad2dataverse.exceptions.HashError)
  * [DatabaseError](#dryad2dataverse.exceptions.DatabaseError)
  * [DataverseUploadError](#dryad2dataverse.exceptions.DataverseUploadError)
  * [DataverseDownloadError](#dryad2dataverse.exceptions.DataverseDownloadError)

<a name="dryad2dataverse"></a>
# dryad2dataverse

Dryad to Dataverse utilities. No modules are loaded by default, so

>>> import dryad2dataverse

will work, but will have no effect.

Modules included:

    dryad2dataverse.constants : "Constants" for all modules. URLs, API keys,
    etc are all here.

    dryad2dataverse.serializer : Download and serialize Dryad
    JSON to Dataverse JSON.

    dryad2dataverse.transfer : metadata and file transfer
    utilities.

    dryad2dataverse.monitor : Monitoring and database tools
    for maintaining a pipeline to Dataverse without unnecessary
    downloading and file duplication.

    dryad2dataverse.exceptions : Custom exceptions.

<a name="dryad2dataverse.constants"></a>
# dryad2dataverse.constants

This module contains the information that configures all the parameters
required to transfer data from Dryad to Dataverse.

"Constants" may be a bit strong, but the only constant is the
presence of change.

<a name="dryad2dataverse.serializer"></a>
# dryad2dataverse.serializer

Serializes Dryad study JSON to Dataverse JSON, as well as
producing associated file information.

<a name="dryad2dataverse.serializer.Serializer"></a>
## Serializer Objects

```python
class Serializer()
```

Serializes Dryad JSON to Dataverse JSON

<a name="dryad2dataverse.serializer.Serializer.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(doi)
```

Creates Dryad study metadata instance.

----------------------------------------

**Arguments**:

  
  doi : str
  — DOI of Dryad study. Required for downloading.
- `eg` - 'doi:10.5061/dryad.2rbnzs7jp'
  ----------------------------------------

<a name="dryad2dataverse.serializer.Serializer.fetch_record"></a>
#### fetch\_record

```python
 | fetch_record(url=None, timeout=45)
```

Fetches Dryad study record JSON from Dryad V2 API at
https://datadryad.org/api/v2/datasets/.
Saves to self._dryadJson. Querying Serializer.dryadJson
will call this function automatically.

----------------------------------------

**Arguments**:

  
  url : str
  — Dryad instance base URL (eg: 'https://datadryad.org').
  
  timeout : int
  — Timeout in seconds. Default 45.
  ----------------------------------------

<a name="dryad2dataverse.serializer.Serializer.id"></a>
#### id

```python
 | @property
 | id()
```

Returns Dryad unique *database* ID, not the DOI.

Where the original Dryad JSON is dryadJson, it's the integer
trailing portion of:

`self.dryadJson['_links']['stash:version']['href']`

<a name="dryad2dataverse.serializer.Serializer.dryadJson"></a>
#### dryadJson

```python
 | @property
 | dryadJson()
```

Returns Dryad study JSON. Will call Serializer.fetch_record() if 
no JSON is present.

<a name="dryad2dataverse.serializer.Serializer.dryadJson"></a>
#### dryadJson

```python
 | @dryadJson.setter
 | dryadJson(value=None)
```

Fetches Dryad JSON from Dryad website if not supplied.

If supplying it, make sure it's correct or you will run into trouble
with processing later.

----------------------------------------

**Arguments**:

  
  value : dict
  — Dryad JSON.

<a name="dryad2dataverse.serializer.Serializer.embargo"></a>
#### embargo

```python
 | @property
 | embargo()
```

Check embargo status. Returns boolean True if embargoed.

<a name="dryad2dataverse.serializer.Serializer.dvJson"></a>
#### dvJson

```python
 | @property
 | dvJson()
```

Returns Dataverse study JSON as dict.

<a name="dryad2dataverse.serializer.Serializer.fileJson"></a>
#### fileJson

```python
 | @property
 | fileJson(timeout=45)
```

Returns a list of file JSONs from call to Dryad API /files/{id},
where the ID is parsed from the Dryad JSON. Dryad file listings
are paginated, so the return consists of a list of dicts, one
per page.

----------------------------------------

**Arguments**:

  
  timeout : int
  — Request timeout in seconds.
  ----------------------------------------

<a name="dryad2dataverse.serializer.Serializer.files"></a>
#### files

```python
 | @property
 | files()
```

Returns a list of tuples with:

(Download_location, filename, mimetype, size, description,
digestType, md5sum)

At this time only md5 is supported.

<a name="dryad2dataverse.serializer.Serializer.oversize"></a>
#### oversize

```python
 | @property
 | oversize(maxsize=None)
```

Returns a list of Dryad files whose size value
exceeds maxsize. Maximum size defaults to
dryad2dataverse.constants.MAX_UPLOAD

----------------------------------------

**Arguments**:

  
  maxsize : int
  — Size in bytes in which to flag as oversize.
- `Default` - constants.MAX_UPLOAD.
  ----------------------------------------

<a name="dryad2dataverse.transfer"></a>
# dryad2dataverse.transfer

This module handles data downloads and uploads from a Dryad instance to a Dataverse instance

<a name="dryad2dataverse.transfer.Transfer"></a>
## Transfer Objects

```python
class Transfer()
```

Transfers metadata and data files from a
Drayd installation to Dataverse installation.

<a name="dryad2dataverse.transfer.Transfer.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(dryad)
```

Creates a dryad2dataverse.transfer.Transfer instance.

----------------------------------------

**Arguments**:

  dryad : dryad2dataverse.serializer.Serializer instance
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.dvpid"></a>
#### dvpid

```python
 | @property
 | dvpid()
```

Returns Dataverse study persistent ID as str.

<a name="dryad2dataverse.transfer.Transfer.auth"></a>
#### auth

```python
 | @property
 | auth()
```

Returns datavese authentication header dict.
ie: `{X-Dataverse-key' : 'APIKEYSTRING'}`

<a name="dryad2dataverse.transfer.Transfer.fileJson"></a>
#### fileJson

```python
 | @property
 | fileJson()
```

Returns a list of file JSONs from call to Dryad API /files/{id},
where the ID is parsed from the Dryad JSON. Dryad file listings
are paginated.

<a name="dryad2dataverse.transfer.Transfer.files"></a>
#### files

```python
 | @property
 | files()
```

Returns a list of lists with:

[Download_location, filename, mimetype, size, description, md5digest]

This is mutable; downloading a file will add md5 info if not available.

<a name="dryad2dataverse.transfer.Transfer.oversize"></a>
#### oversize

```python
 | @property
 | oversize()
```

Returns list of files exceeding Dataverse ingest limit
dryad2dataverse.constants.MAX_UPLOAD.

<a name="dryad2dataverse.transfer.Transfer.doi"></a>
#### doi

```python
 | @property
 | doi()
```

Returns Dryad DOI.

<a name="dryad2dataverse.transfer.Transfer.set_correct_date"></a>
#### set\_correct\_date

```python
 | @staticmethod
 | set_correct_date(url, hdl, d_type='distributionDate', apikey=None)
```

Sets "correct" publication date for Dataverse.

Note: dryad2dataverse.serializer maps Dryad 'publicationDate'
to Dataverse 'distributionDate' (see serializer.py ~line 675).

Dataverse citation date default is ":publicationDate". See
Dataverse API reference:
https://guides.dataverse.org/en/4.20/api/native-api.html#id54.

----------------------------------------

**Arguments**:

  
  url : str
  — Base URL to Dataverse installation.
  
  hdl : str
  — Persistent indentifier for Dataverse study.
  
  d_type : str
  — Date type. One of  'distributionDate', 'productionDate',
  'dateOfDeposit'. Default 'distributionDate'.
  
  apikey : str
  — Default dryad2dataverse.constants.APIKEY.
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.upload_study"></a>
#### upload\_study

```python
 | upload_study(url=None, apikey=None, timeout=45, **kwargs)
```

Uploads Dryad study metadata to target Dataverse or updates existing.
Supplying a `targetDv` kwarg creates a new study and supplying a
`dvpid` kwarg updates a currently existing Dataverse study.

----------------------------------------

**Arguments**:

  
  url : str
  — URL of Dataverse instance. Defaults to constants.DVURL.
  
  apikey : str
  — API key of user. Defaults to contants.APIKEY.
  
  timeout : int
  — timeout on POST request.
  
  **KEYWORD ARGUMENTS**
  
  One of these is required. Supplying both or neither raises a NoTargetError
  
  targetDv : str
  — Short name of target dataverse. Required if new dataset.
  Specify as targetDV=value.
  
  dvpid = str
  — Dataverse persistent ID (for updating metadata).
  This is not required for new uploads, specify as dvpid=value
  
  **OPTIONAL KEYWORD ARGUMENTS**

<a name="dryad2dataverse.transfer.Transfer.download_file"></a>
#### download\_file

```python
 | download_file(url, filename, tmp=None, size=None, chk=None, timeout=45)
```

Downloads a file via requests streaming and saves to constants.TMP.
returns md5sum on success and an exception on failure.

----------------------------------------

**Arguments**:

  
  url : str
  — URL of download.
  
  filename : str
  — Output file name.
  
- `timeout` - int
  — Requests timeout.
  
  tmp : str
  — Temporary directory for downloads.
  Defaults to dryad2dataverse.constants.TMP.
  
  size : int
  — Reported file size in bytes.
  Defaults to dryad2dataverse.constants.MAX_UPLOAD.
  chk : str
  - md5 sum of file (if available and known).
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.download_files"></a>
#### download\_files

```python
 | download_files(files=None)
```

Bulk downloader for files.
----------------------------------------

**Arguments**:

  
- `files` - list
  — Items in list can be tuples or list with a minimum of:
  
  (dryaddownloadurl, filenamewithoutpath, [md5sum])
  
  The md5 sum should be the last member of the tuple.
  
  Defaults to self.files.
  
  Normally used without arguments to download all the associated
  files with a Dryad study.

<a name="dryad2dataverse.transfer.Transfer.force_notab_unlock"></a>
#### force\_notab\_unlock

```python
 | force_notab_unlock(study, dv_url, fid, apikey=None)
```

Checks for a study lock and forcibly unlocks and uningests
to prevent tabular file processing. Required if mime and filename
spoofing is not sufficient.

----------------------------------------

**Arguments**:

  
  study : str
  — Persistent indentifer of study.
  
  dv_url : str
  — URL to base Dataverse installation.
  
  fid : str
  — File ID for file object.
  
  apikey : str
  — API key for user.
  If not present authorization defaults to self.auth.
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.upload_file"></a>
#### upload\_file

```python
 | upload_file(dryadUrl=None, filename=None, mimetype=None, size=None, descr=None, md5=None, studyId=None, dest=None, fprefix=None, timeout=300)
```

Uploads file to Dataverse study. Returns a tuple of the
dryadFid (or None) and Dataverse JSON from the POST request.
Failures produce JSON with different status messages
rather than raising an exception.

----------------------------------------

**Arguments**:

  
  filename : str
  — Filename (not including path).
  
  mimetype : str
  — Mimetype of file.
  
  size : int
  — Size in bytes.
  
  studyId : str
  — Persistent Dataverse study identifier.
  Defaults to Transfer.dvpid.
  
  dest : str
  — Destination dataverse installation url.
  Defaults to constants.DVURL.
  
  md5 : str
  — md5 checksum for file.
  
  fprefix : str
  — Path to file, not including a trailing slash.
  
  timeout : int
  - Timeout in seconds for POST request. Default 300.
  
  dryadUrl : str
  - Dryad download URL if you want to include a Dryad file id.
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.upload_files"></a>
#### upload\_files

```python
 | upload_files(files=None, pid=None, fprefix=None)
```

Uploads multiple files to study with persistentId pid.
Returns a list of the original tuples plus JSON responses.

----------------------------------------

**Arguments**:

  
- `files` - list
  — List contains tuples with
  (dryadDownloadURL, filename, mimetype, size).
  
  pid : str
  — Defaults to self.dvpid, which is generated by calling
  dryad2dataverse.transfer.Transfer.upload_study().
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.upload_json"></a>
#### upload\_json

```python
 | upload_json(studyId=None, dest=None)
```

Uploads Dryad json as a separate file for archival purposes.

----------------------------------------

**Arguments**:

  
  pid : str
  — Dataverse persistent identifier.
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.delete_dv_file"></a>
#### delete\_dv\_file

```python
 | delete_dv_file(dvfid, dvurl=None, key=None)
```

Deletes files from Dataverse target given a dataverse file ID.
This information is unknowable unless discovered by
dryad2dataverse.monitor.Monitor or by other methods.

Returns 1 on success (204 response), or 0 on other response.

----------------------------------------

**Arguments**:

  
  dvurl : str
  — Base URL of dataverse instance.
  Defaults to dryad2dataverse.constants.DVURL.
  
  dvfid : str
  — Dataverse file ID number.
  ----------------------------------------

<a name="dryad2dataverse.transfer.Transfer.delete_dv_files"></a>
#### delete\_dv\_files

```python
 | delete_dv_files(dvfids=None, dvurl=None, key=None)
```

Deletes all files in list of Dataverse file ids from
a Dataverse installation.

----------------------------------------

**Arguments**:

  
  dvfids : list
  — List of Dataverse file ids.
  Defaults to dryad2dataverse.transfer.Transfer.fileDelRecord.
  
  dvurl : str
  — Base URL of Dataverse. Defaults to dryad2dataverse.constants.DVURL.
  
  key : str
  — API key for Dataverse. Defaults to dryad2dataverse.constants.APIKEY.
  ----------------------------------------

<a name="dryad2dataverse.monitor"></a>
# dryad2dataverse.monitor

Dryad/Dataverse status tracker. Monitor creates a singleton object which
writes to a SQLite database. Methods will (generally) take either a
dryad2dataverse.serializer.Serializer instance or
dryad2dataverse.transfer.Transfer instance

The monitor's primary function is to allow for state checking
for Dryad studies so that files and studies aren't downloaded
unneccessarily.

<a name="dryad2dataverse.monitor.Monitor"></a>
## Monitor Objects

```python
class Monitor()
```

The Monitor object is a tracker and database updater, so that
Dryad files can be monitored and updated over time. Monitor is a singleton,
but is not thread-safe.

<a name="dryad2dataverse.monitor.Monitor.__new__"></a>
#### \_\_new\_\_

```python
 | __new__(cls, dbase=None, *args, **kwargs)
```

Creates a new singleton instance of Monitor.

Also creates a database if existing database is not present.

----------------------------------------

**Arguments**:

  
  dbase : str
  — Path to sqlite3 database. That is:
  /path/to/file.sqlite3
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(dbase=None, *args, **kwargs)
```

Initialize the Monitor instance if not instantiated already (ie, Monitor
is a singleton).

----------------------------------------

**Arguments**:

  
  dbase : str
  — Complete path to desired location of tracking database
- `(eg` - /tmp/test.db).
  
  Defaults to dryad2dataverse.constants.DBASE.
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.__del__"></a>
#### \_\_del\_\_

```python
 | __del__()
```

Commits all database transactions on object deletion and closes database.

<a name="dryad2dataverse.monitor.Monitor.lastmod"></a>
#### lastmod

```python
 | @property
 | lastmod()
```

Returns last modification date from monitor.dbase.

<a name="dryad2dataverse.monitor.Monitor.status"></a>
#### status

```python
 | status(serial)
```

Returns a dictionary with keys 'status' and 'dvpid'.
`{status :'updated', 'dvpid':'doi://some/ident'}`.

`status` is one of 'new', 'unchanged', 'updated' or 'filesonly'.

'new' is a completely new file.

'unchanged' is no changes at all.

'updated' is changes to lastModificationDate AND metadata changes.

'filesonly' is changes to lastModificationDate only
(which presumably indicates a file change.

`dvpid` is a Dataverse persistent identifier.
`None` in the case of status='new'

----------------------------------------

**Arguments**:

  
  serial : dryad2dataverse.serializer instance
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.diff_metadata"></a>
#### diff\_metadata

```python
 | diff_metadata(serial)
```

Analyzes differences in metadata between current serializer
instance and last updated serializer instance.
Returns a list of field changes consisting of:

[{key: (old_value, new_value}] or None if no changes.

For example:

----------------------------------------
```
[{'title':
('Cascading effects of algal warming in a freshwater community',
 'Cascading effects of algal warming in a freshwater community theatre')}
]
```

**Arguments**:

  
  serial : dryad2dataverse.serializer.Serializer instance
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.diff_files"></a>
#### diff\_files

```python
 | diff_files(serial)
```

Returns a dict with additions and deletions from previous Dryad
to dataverse upload.

Because checksums are not necessarily included in Dryad file
metadata, this method uses dryad file IDs, size, or
whatever is available.

If dryad2dataverse.monitor.Monitor.status()
indicates a change it will produce dictionary output with a list
of additions or deletions, as below:

`{'add':[dyadfiletuples], 'delete:[dryadfiletuples]}`

----------------------------------------

**Arguments**:

  
  serial : dryad2dataverse.serializer.Serializer instance
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.get_dv_fid"></a>
#### get\_dv\_fid

```python
 | get_dv_fid(url)
```

Returns str — the Dataverse file ID from parsing a Dryad
file download link.  Normally used for determining dataverse
file ids for *deletion* in case of dryad file changes.

----------------------------------------

**Arguments**:

  
  url : str
  — *Dryad* file URL in form of
  'https://datadryad.org/api/v2/files/385819/download'.
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.get_dv_fids"></a>
#### get\_dv\_fids

```python
 | get_dv_fids(filelist)
```

Returns Dataverse file IDs from a list of Dryad file tuples.
Generally, you would use the output from
dryad2dataverse.monitor.Monitor.diff_files['delete']
to discover Dataverse file ids for deletion.

----------------------------------------

**Arguments**:

  
  filelist : list
  — List of Dryad file tuples: eg:
  
  ```
  [('https://datadryad.org/api/v2/files/385819/download',
  'GCB_ACG_Mortality_2020.zip',
  'application/x-zip-compressed', 23787587),
  ('https://datadryad.org/api/v2/files/385820/download',
  'Readme_ACG_Mortality.txt',
  'text/plain', 1350)]
  ```
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.get_json_dvfids"></a>
#### get\_json\_dvfids

```python
 | get_json_dvfids(serial)
```

Return a list of Dataverse file ids for Dryad JSONs which were
uploaded to Dataverse.
Normally used to discover the file IDs to remove Dryad JSONs
which have changed.

----------------------------------------

**Arguments**:

  
  serial : dryad2dataverse.serializer.Serializer instance
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.update"></a>
#### update

```python
 | update(transfer)
```

Updates the Monitor database with information from a
dryad2dataverse.transfer.Transfer instance.

If a Dryad primary metadata record has changes, it will be
deleted from the database.

This method should be called after all transfers are completed,
including Dryad JSON updates, as the last action for transfer.

----------------------------------------

**Arguments**:

  
  transfer : dryad2dataverse.transfer.Transfer instance
  ----------------------------------------

<a name="dryad2dataverse.monitor.Monitor.set_timestamp"></a>
#### set\_timestamp

```python
 | set_timestamp(curdate=None)
```

Adds current time to the database table. Can be queried and be used
for subsequent checking for updates. To query last modification time,
use the dataverse2dryad.monitor.Monitor.lastmod attribute.

----------------------------------------

**Arguments**:

  
  curdate : str
  — UTC datetime string in the format suitable for the Dryad API.
  eg. 2021-01-21T21:42:40Z
  or .strftime('%Y-%m-%dT%H:%M:%SZ').
  ----------------------------------------

<a name="dryad2dataverse.exceptions"></a>
# dryad2dataverse.exceptions

Custom exceptions for error handling.

<a name="dryad2dataverse.exceptions.Dryad2DataverseError"></a>
## Dryad2DataverseError Objects

```python
class Dryad2DataverseError(Exception)
```

Base exception class for Dryad2Dataverse errors.

<a name="dryad2dataverse.exceptions.NoTargetError"></a>
## NoTargetError Objects

```python
class NoTargetError(Dryad2DataverseError)
```

No dataverse target supplied error.

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

Raised on hex digest mismatch.

<a name="dryad2dataverse.exceptions.DatabaseError"></a>
## DatabaseError Objects

```python
class DatabaseError(Dryad2DataverseError)
```

Tracking database error.

<a name="dryad2dataverse.exceptions.DataverseUploadError"></a>
## DataverseUploadError Objects

```python
class DataverseUploadError(Dryad2DataverseError)
```

Returned on not OK respose (ie, not requests.status_code == 200).

<a name="dryad2dataverse.exceptions.DataverseDownloadError"></a>
## DataverseDownloadError Objects

```python
class DataverseDownloadError(Dryad2DataverseError)
```

Returned on not OK respose (ie, not requests.status_code == 200).

