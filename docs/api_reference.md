# API reference

This is a general guide as to how to use the dryad2dataverse package in your own Python software.

## Basic usage

#### Converting JSON
```python
>>> #Convert Dryad JSON to Dataverse JSON and save to a file
>>> import dryad2dataverse.serializer
>>> i_heart_dryad = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
>>> with open('dataverse_json.json', 'w') as f:
	f.write(f'{i_heart_dryad.dvJson}')
>>> #Or just view it this way in a Python session
>>> i_heart_dryad.dvJson
```

#### Transferring data

Note: a number of variables must be set [correctly] for this to work, such as your target dataverse. This example continues with the Serializer instance above.


```python
>>> import dryad2dataverse.config
>>> import dryad2dataverse.auth
>>> import dryad2dataverse.transfer
>>> config = dryad2dataverse.config.Config()
>>> # Now go and edit the config file which is saved at your system's default location
>>> # Alternately, you can fill out the config object like a dict
>>> config = dryad2dataverse.config.Config() #you are reloading it
>>> config['token'] = dryad2dataverse.auth.Token(**config)
>>> dv = dryad2dataverse.transfer.Transfer(i_heart_dryad, **config)
>>> # Files must first be downloaded; there is no direct transfer
>>> dv.download_files()
>>> # 'dryad' is the short name of the target dataverse
>>> # Yours may be different
>>> # First, create the study metadata
>>> dv.upload_study(targetDv='dryad', **config)
>>> # Then upload the files
>>> dv.upload_files(**config)
```

#### Change monitoring

Because monitoring the status of something over time requires persistence, the dryad2dataverse.monitor.Monitor object uses an [SQLite3](https://sqlite.org) database, which has the enormous advantage of being a single file that is portable between systems. This allows monitoring without laborious database configuration on a host system, and updates can be run on any system that has sufficient storage space to act as an intermediary between Dryad and Dataverse. This is quite a simple database, as the [documentation on its structure](dbase_structure/index.html) shows.

If you need to change systems just swap the database to the new system.

In theory you could run it from a Raspberry Pi Zero that you have in a desk drawer, although that may not be the wisest idea. Maybe use your cell phone.

Monitoring changes requires both the `Serializer` and `Transfer` objects from above.

```python
>>> # Create the Monitor instance
>>> monitor = dryad2dataverse.monitor.Monitor(**config) #config as above
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

## Python package API 

::: dryad2dataverse
::: dryad2dataverse.config
::: dryad2dataverse.auth
::: dryad2dataverse.serializer
::: dryad2dataverse.transfer
::: dryad2dataverse.monitor
::: dryad2dataverse.handlers
::: dryad2dataverse.exceptions
