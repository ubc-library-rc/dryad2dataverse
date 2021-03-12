##Dryad to Dataverse mirroring outline

### Introduction

The Dryad data repository (<https://datadryad.org/stash>) contains data sets and research data created by UBC affiliated researchers. To consolidate UBC's data and facilitate discovery by other platforms such as FRDR (<https://frdr.ca>), UBC research data will be harvested by Dryad and deposited into UBC's dataverse collection at Scholars Portal (<https://dataverse.scholarsportal.info/dataverse/ubc_rd/>).

### Project goals

The end result of the project should be a self-sustaining harvester which automatically deposits UBC research data from Dryad into dataverse, including any updates to metadata and files. Where possible, the harvester should reduce the amount of manual intervention required by UBC Library Research Commons staff. 

Both Dataverse and Dryad have application programming interfaces (APIs) which should allow for automation of most, if not all, steps involved in migration.

However, if metadata is to be curated by UBC to meet its Research Data Management (RDM) standards, manual intervention will be required.

Once a sustainable harvester is created, software could be released to the public for use by other institutions.

### Proposed workflow

[Start loop]

* Identify new or changed UBC data sets in Dryad

* Determine if the end-user license allows insertion of data into Scholars Portal

	Note: From <https://datadryad.org/stash/best_practices>: "All files submitted to Dryad must abide by the terms of the Creative Commons Zero (CC0 1.0)

* Harvest metadata from Dryad using the Dryad API

* Convert Dryad metadata JSON to Dataverse JSON

* Download and verify Dryad data sets

* Structure downloaded datafiles into a format suitable for Dataverse ingest

* Upload and verify file data sets

* Save Dryad metadata, file signatures and other relevant data to allow for change montoring

* Notify UBC Research Commons staff of new data upload

* Manual cleaning of metadata within dataverse

* Release of data at Scholars Portal

[End loop]

## Identification of issues with potential workflow

* There does not appear to be a search endpoint in the Dryad API:
	
	<https://datadryad.org/api/v2/docs/#/default/get_datasets> 
	"Items returned may depend on user or permission and are paged. Search API to come later."

* What about versions? Do we need to get them all, or just new ones?

* Currently, no Dryad to Dataverse metadata crosswalk exists. A crosswalk will need to be created to allow ingest into Dataverse

* What would the status be of material that does not allow migration into Scholars Portal (ie, restricted license data sets)
DOUG: Metadata only? And how many of these exist, if Dryad mandates CC0 for deposits?

* If metadata is rewritten manually on ingest into Dataverse, how will metadata changes on Dryad data sets be handled?

* Are there any data sets which exceed Dataverse's file upload size limit? If so, is there an alternative workflow?
DOUG: Currently 3.5 GB per file. But we should consider our total storage usage on Dataverse. So this is something we need to unpack further.

* Continual harvesting and file change comparisons will require mechanisms and servers on which to hold this data. Ideally, such mechanisms should be portable to allow for easy migration between servers and even desktops.

* Multiple DOIs will be created for the same data set.

* Do researchers need to be notified that their data sets are mirrored in another repository?

	Tentatively, this answer is "no", as the license should allow mirroring of data. However, should UBC, as a courtesy to researchers, notify them when data has been mirrored?
DOUG: Probably.

## Proposed technical details

* Migration script to be written in Python

* Data to be stored in a portable sqlite3 database

* Use a UBC server and cron to run the migrator/checker at predefined times

* The software will automatically create a new study version should data or metadata change

* The software will email a user-configurable list of people on the ingest of any data into Scholars Portal

* Testing to be performed on either Scholars Portal Demo Dataverse <https://demodv.scholarsportal.info> or UBC's test dataverse instance.

## Dryad API

API: <https://datadryad.org/api/v2/docs/>

Documentation: <https://github.com/CDL-Dryad/dryad/tree/master/documentation>
