#Design decisions in Dryad to Dataverse conversion

Design decisions not included in the crosswalk documentation or those that require expansion.


## Dryad contact
daniella.lowenberg@ucop.edu

**Dryad DOI**

Dryad DOI will go into Dataverse's Other ID fields:

Agency: Dryad
Identifier: DOI

**Geospatial**

Dryad points are converted to size 0 Dataverse bounding boxes

Bounding boxes remain boxes

Dryad place maps to "Other" as there is no consistency in naming.

**Contact information**

Not all Dryad records contain author email addresses, but this is a *required* component of a Dataverse record.

As such, by default contact information is appended to the generated Dryad contact list (and appears by itself if no contact information is found).

```
constants.DV_CONTACT_NAME
constants.DV_CONTACT_EMAIL
```

**Tabular processing**

Because tabular processing halts file ingestion, any tabular data has its mimetype and extension changed on the fly to bypass automated ingest processing. This means that if any tabular data is to be processed, it must be done after the fact via the Dataverse API.

**Large files**

Any files which have a reported size of in excess of the `constants.MAX_UPLOAD` value will not be uploaded to a Dataverse installation. Maximum size will be dependent upon the Dataverse installation configuration.

**Subsettable file processing**

Although spoofing MIME type and file extension works to prevent tabular file processing in a majority of cases, it does not work in all of them (more's the pity). Because tabular file ingest immediately ceases further file ingests, there needs to be a step in the ingest process to check for an ingest lock and remove it so that file uploads can continue.

Unfortunately, if a tabular file begins ingest, the file description in the dataverse GUI is replaced by a graphic stating "tabular file ingest in process". Removing the lock does not remove the notification, nor does cancelling the ingest, as the ingest is not flagged as tabular until the ingest is completed.

The only way to remove this unseemly status bar is to forcibly reingest after all of the files have been uploaded, and either keep the ingested file as tabular OR then uningest.

Please see <https://groups.google.com/g/dataverse-community/c/tEldk5-pXAE/m/KQkNg01CAwAJ> in the Dataverse Community in Google Groups for further details.
