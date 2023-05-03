---
layout: default
title: Quickstart 
nav_order: 1
---


# dryad2dataverse -  translate, transfer and track

![dryad2dataverse logo](images/dryad2dataverseLogo.svg)
---

## Introduction

**dryad2dataverse** is an oddly specific [Python](https://python.org) package/library which comes with the highly-sought after [**console application**](script.md) which allows easier transfer of metadata and data from a Dryad data repository (ie, <https://datadryad.org>) to a [Dataverse](https://dataverse.org/ "Dataverse software main site") repository.

### The app is probably what you want 
----

If you're interested in moving Dryad studies to Dataverse, being notified on changes and largely automating everything, the [dryadd application](script.md) can do *all* of these things without requiring any knowledge of Python or programming. All you need is basic command line knowledge and a platform with enough storage to (temporarily) hold the contents of a few Dryad records.

----
## Quick install

```nohighlight
pip install dryad2dataverse
```

or, if you want to stay clear of anything related to a command line, download a compiled version of the migrator `dryadd` only for your computer system at the [releases page](https://github.com/ubc-library-rc/dryad2dataverse/releases). Note that binary releases are not available for all platforms, and if you want the most recent version you're better off using `pip`.

### I know how to program in Python. What does this do?

With these tools it’s possible to:

a) Serialize Dryad metadata to Dataverse JSON

b) Transfer Dryad studies to Dataverse without any knowledge of the somewhat complex Dataverse API

c) Monitor changes in status

#### So why would I need this?

* You are a researcher and you wish to deposit via API into Dataverse repository. You can use the tools with this package to that without needing to understand the APIs and formats of two separate platforms.

* You've used Dryad, but the Dataverse JSON and API is unfamiliar and [complex](https://guides.dataverse.org/en/latest/_downloads/dataset-create-new-all-default-fields.json "Complex Dataverse JSON"). 

* You want to write your Dryad JSON and have it convert automatically to Dataverse's much more complex one.

* Your institution has researchers who have deposited data into Dryad and you wish to copy them into the Dataverse repository which contains the bulk of your institution's research data (for example, the Dataverse repository at <https://borealisdata.ca>).

* And on top of that, you don't want to keep checking to see if there were any updates, so you wish to automate the process.

## Basic usage

#### Converting JSON
```nohighlight
>>> #Convert Dryad JSON to Dataverse JSON and save to a file
>>> import dryad2dataverse.serializer
>>> i_heart_dryad = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
>>> with open('dataverse_json.json', 'w') as f:
	f.write(f'{i_heart_dryad.dvJson}')
>>> #Or just view it this way in a Python session
>>> i_heard_dryad.dvJson
```

#### Transferring data

Note: a number of variables must be set [correctly] for this to work, such as your target dataverse. This example continues with the Serializer instance above.

```nohighlight
>>> import dryad2dataverse.transfer
>>> dv = dryad2dataverse.transfer.Transfer(i_heart_dryad)
>>> # Files must first be downloaded; there is no direct transfer
>>> dv.download_files()
>>> # 'dryad' is the short name of the target dataverse
>>> # Yours may be different
>>> # First, create the study metadata
>>> dv.upload_study(targetDv='dryad')
>>> # Then upload the files
>>> dv.upload_files()
```

#### Change monitoring

Because monitoring the status of something over time requires persistence, the dryad2dataverse.monitor.Monitor object uses an [SQLite3](https://sqlite.org) database, which has the enormous advantage of being a single file that is portable between systems. This allows monitoring without laborious database configuration on a host system, and updates can be run on any system that has sufficient storage space to act as an intermediary between Dryad and Dataverse. This is quite a simple database, as the [documentation on its structure](dbase_structure/index.html) shows.

If you need to change systems just swap the database to the new system.

In theory you could run it from a Raspberry Pi Zero that you have in a desk drawer, although that may not be the wisest idea. Maybe use your cell phone.

Monitoring changes requires both the `Serializer` and `Transfer` objects from above.

```nohighlight
>>> # Create the Monitor instance
>>> monitor = dryad2dataverse.monitor.Monitor()
>>> # Check status of your serializer object
>>> monitor.status(i_heart_dryad)
{'status': 'new', 'dvpid': None}
>>> # imagine, now that i_still_heart_dryad is a study
>>> # that was uploaded previously
>>> monitor.status(i_still_heart_dryad)
{'status': 'unchanged', 'dvpid': 'doi:99.99999/FK2/FAKER'}
>>> #Check the difference in files
>>> monitor.diff_files(i_still_heart_dryad)
{}
>>> # After the transfer dv above:
>>> monitor.update(transfer)
>>> # And then, to make your life easier, update the last time you checked Dryad
>>> monitor.set_timestamp()
```

### That's great! I'm going to use this for my very important data for which I have no backup.

The **dryad2dataverse** library is free and open source, released under the MIT license. It's also not written by anyone with a degree in computer science, so as the MIT license says: 

	Software is provided "as is", without warranty of any kind
