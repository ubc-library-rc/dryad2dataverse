# Dryad2dataverse changelog

Perfection on the first attempt is rare.

## v0.6.0 - 2 May 2023

* Updated to current Python packaging standards
* Installation can now be done straight from `pip` without resorting to `git+http. . .`
* Test framework now `unittest`
* Documentation updated

**dryad2dataverse.constants**

* `constants.dvurl` now defaults to <https://borealisdata.ca>
* `pathlib` instead of `os.path` for greater cross-platform compatibility.

## v0.5.8 - 10 February 2023

* Good lord I misspelled "February" initially
* certifi requirements updated
* somewhat better error logging for odd requests failures
* Dataverse JSON change to be in compliance with new standards for v5.12+

Note that  binaries will no longer be produced for dryad2dataverse. If you want one, you can either contact me and I will create one and add it to the release, or you can make one yourself using PyInstaller or Nuitka. The effort of making them vs the lack of downloads has led to this decision. If this is a problem please create an issue for discussion.


## v0.5.0 - 7 December 2022

**dataverse.handlers**

* New handler component
* Custom SSL log handler `SSLSMTPHandler` added which reduces frequency of email problems

**dryadd.py**

* Mail formatting changed to ensure lines are less than 1000 characters in length to adhere to [RFC 2825 4.5.3.5] (https://www.rfc-editor.org/rfc/rfc2821#section-4.5.3.1).
* Logging messages contain more information
* Default mail service changed to Yahoo mail
* Default dataverse server destination changed to `https://borealisdata.ca`
* Help text cleanup

## v0.3.1 - 4 February 2022

Changes to the Dryad API sparked a few changes to dryad2dataverse and dryadd.py. More specifically, the Dryad `/search` API endpoint can produce false positive results, which can result in bulk study replacement when none is required. Additionally, as file IDs are not unique in Dryad (contrary to the documentation), files are no longer identified on the basis of Dryad file ID.

**dryad2dataverse.serializer**

* `Serial.files` output now includes explicit hash type

**dryad2dataverse.monitor**

* `Monitor.status()` now returns values of `new, unchanged, updated, filesonly`
*  Monitor.status() now includes `notes` key
*  Monitor.diff\_files() now outputs a list of files for new studies using the `add` key instead of producing an empty dict.
*  Monitor.diff\_files() outputs of `hash_change` key listing files whose names and sizes are identical but have either a changed hash or a new one.. Note that this does not necessarily indicate a changed file as hashes have been added to existing files.
*  Monitor.get\_dv\_fid() now explicitly selects highest ROWID when returning a Dryad UID as UIDs are not considered persistent identifiers (as per email from Dryad January 2022)

**dryadd.py**

* Dates are now filtered by metadata `lastModificationDate` as Dryad search API endpoint does not respect date parameter (as per Dryad email, January 2022). 
* Databases are now backed up with suffix of `.YYYY-MM-DD-HHMM` instead of generic `.bak`
* Number of backups can be specified as a parameter
* Switch added to halt process on excessive number of study updates
* Study threshold added to specify what is considered "excessive"
* Recipients are emailed on halt due to excessive updates
* Verbosity increased
* Output now explicity includes lists of new files instead of empty dict
* Updates now skipped on report of `unchanged` or `lastmodsame`; ie. metadata is identical *or* the lastModificationDate field in the Dryad JSON unchanged.

**Other**

* Binary files are now only included as part of a Github release
* Binary release now includes linux x86-64
* Dataverse utilities scripts removed; use [dataverse_utils](https://github.com/ubc-library-rc/dataverse_utils) instead.

## v0.1.4 - 22 Sept 2021

**requirements.txt**

* Updated version requirements for `urllib3` and `requests` to plug dependabot alert hole.

**dryadd.py**

* Updated associated `dryadd.py` binaries to use newer versions of `requests` and `urllib3`

## v0.1.3 - 10 August 2021

**setup.py**

* Enhanced information

**dryadd.py**

* Script repair for better functioning on Windows platforms

## v0.1.2 - 4 May 2021

* fixed error in `setup.py`
* added binaries of `dryadd` for Windows and Mac

## v0.1.1 - 30 April 2021

**dryad2dataverse**

* improved versioning system

**dryad2dataverse.serializer**

* Fixed bug where keywords were only serialized when grants were present

**dryad2dataverse.transfer**

* Added better defaults for `transfer.set_correct_date`

**dryad2dataverse.monitor**

* Added meaningless change to `monitor.update` for internal consistency

**scripts/dryadd.py**

* Show version option added
* `transfer.set_correct_date()` added to set citation to match Dryad citation.

---

## v0.1.0 - 08 April 2021

* Initial release

