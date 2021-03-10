---
layout: default
title: API Reference Notes 
nav_order: 10
---

# General Reference

This page covers material that isn't automatically generated from the source code, that is, the API reference section. Information regarding specific modules is below.


## dryad2dataverse.constants  
<a name="dryad2dataverse.constants"></a>

And by "constants", you should change these as required. This module contains the information that configures all the parameters required to transfer data from Dryad to Dataverse. As 'constants' don't generally change, there's a non-zero chance that the name of this module will change.

### General variables  
<a name="General variables"></a>

**RETRY_STRATEGY**  
	+ This is a `urllib3.util` `Retry` object which controls the connection attemps of a `requests.Session` object. Not all connections are guaranteed to be successful the first time round, and the `Retry` object will allow multiple connection attempts before raising an exception.  
	+ Default: 10 attempts, with exponentially increased times between attempts.  
	+ For more information/a tutorial on how to use the Retry object, please see <https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#retry-on-failure>  

**DRYURL**  
	+ Base URL for the Dryad data repository.  
	+ Default = 'https://datadryad.org'  

It's unlikely you will ever change this, but Dryad is an open source project, so it's not out of the realm of possibility that there will be another Dryad-style repository.

**TMP**  
	+ Temporary file download location. Note that downloaded files have the potential of being very large, so select a directory which has sufficient space. 	  
	+ Default ='/tmp'  

This is configured for \*nix style environments. Windows does not, by default, have `/tmp` directory, for instance.

### Data transfer variables
<a name="Data transfer variables"></a>
**DVURL**  
	+ Base URL for dataverse installation  
	+ Default = 'https://dataverse.scholarsportal.info'  

Obviously, if you are not transferring your data to the [Scholars Portal](https://dataverse.scholarsportal.info), you will need to change this.

**APIKEY**   
	+ Dataverse API key for user performing transfer. Sufficient privileges for upload and metadata manipulation must be attached to the user. See [Dataverse API documentation](https://guides.dataverse.org/en/latest/api/index.html) for an explanation of the privilege level required.   
	+ Default = None  

To avoid issues, using an API key which has administrator privileges for the target dataverse is the easiest apprach.

**MAX_UPLOAD**  
	+ Maximum upload file size in bytes. Files exceeding this size will be ignored. By default, Dataverse has a 3GB upload size limit  
	+ Default = 3221225472   

Files will not be downloaded or uploaded if their (reported) size exceeds this limit.

**DV_CONTACT_EMAIL**   
	+ Dataverse "Contact" email address. Required as part of Dataverse metadata. This would generally be the email address of the data set curator  
	+ Default= None  

API uploads to Dataverse fail without a contact email. While dryad2dataverse attempts to read email addresses from Dryad records, they are not required in Dryad.

**DV_CONTACT_NAME**   
	+ Dataverse "Contact" name. Required as part of Dataverse metadata. Generally the name of the data set curator, whether individual or an organization  
	+ Default = None  

As with contact email addresses, contact names are required in Dataverse, but not in Dryad.

**NOTAB**  
	+ File extensions which should have tabular processing disabled. Lower case only.  
	+ Dataverse will immediately cease ingest and lock a dataset when encountering a file which can be processed to .tab format. This causes upload crashes unless disabled.  
	+ Files may be converted to .tab format after upload using Dataverse's `reingest` endpoint: <https://guides.dataverse.org/en/latest/api/native-api.html#reingest-a-file>  
	+ Default = ['.sav', '.por', '.zip', '.csv', '.tsv', '.dta', '.rdata', '.xslx']  


If one of the files in the upload triggers tabular processing the upload will suddenly cease and fail. This behaviour is built into Dataverse (unfortunately), and can be only overcome through workarounds such as double-zipping files, or, in this case, spoofing MIME types and extensions. Because Dataverse's tabular file processing capabilities are subject to change, this is not an exhaustive list and some files may be processed regardless. See also dryad2dataverse.transfer.Transfer.force_notab_unlock().

#Monitoring database variables
<a name="Monitoring database variables"></a>

**HOME**  
	+ Home directory path for user 	  
	+ Default = os.path.expanduser('~')  

Home directory for the user. There is probably no reason to change this.

**DBASE**  
	+ Full path for transfer monitoring sqlite3 database  
	+ Default = HOME + os.sep + 'dryad_dataverse_monitor.sqlite3'  

By default, the monitoring/tracking database will be created in the user's home directory, which is convenient but not necessarily not ideal. The location can also be set on instantiation of `dryad2dataverse.monitor.Monitor`: eg `monitor = dryad2dataverse.monitor.Monitor('/path/to/tracking/directory/databasename.sqlite3')`

