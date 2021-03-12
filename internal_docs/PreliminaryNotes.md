Dryad overview

## Purpose
To move/copy UBC dryad collections to Scholars portal

1. Can SP harvest Dryad? If yes, problem solved
2. If no, metadata/data must be harvested from Dryad and inserted into SP dataverse

## Should there be no automated harvesting

* Metadata is available via JSON
	`GET /datasets/{doi}`

* File downloads:
	`GET /datasets/{doi}/download`

* Mappings of DryadJSON to Dataverse JSON would be required

* Target dataverse must be supplied

* Mandatory dataverse subject must be supplied

* Contact info must be supplied

* Rights must be available in dryad

* Upload converted JSON to dataverse target dataverse 

* Upload package may be added as is, or tags generated from zipfile structure

* Files can presumably be released on upload.

## Further considerations

* Authors have not necessarily considered dataverse as an option. Should an automated script be kept running to update as required?

* Other non-canonical DOIs will be generated

* What of embargo status/in process data sets?




