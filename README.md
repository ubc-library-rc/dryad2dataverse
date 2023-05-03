# dryad2dataverse

**dryad2dataverse** is a [Python](https://python.org) package and an associated console line application which allows easier transfer of metadata and data from a Dryad data repository (ie, <https://datadryad.org>) to a [Dataverse](https://dataverse.org/ "Dataverse software main site") repository. Dryad2dataverse is pure Python and should run on any platform which supports Python 3.6 or greater.

Data transfers between repositories require local storage, so not all platforms will be equally suitable.

## Installing

`pip install dryad2dataverse`

## Usage

Most users will likely just want to use the command line transfer and monitor tool (`dryadd`) but the tools are available in any Python environment

### Command line application

`dryadd [all the various options]`

see all the options available with

`dryadd -h`

Initiate a transfer from a [Dryad](https://datadryad.org) repository to a [Dataverse](https://dataverse.org) repository.

### Using the package

```
#Serializer
import dryad2dataverse.serializer
#Transfer
import dryad2dataverse.transfer
#Monitor
#import dryad2dataverse.monitor

i_heart_dryad = dryad2dataverse.serializer.Serializer('doi:10.5061/dryad.2rbnzs7jp')
dv = dryad2dataverse.transfer.Transfer(i_heart_dryad)
dv.download_files()
dv.upload_study(targetDv='dryad')
dv.upload_files()

#For an explanation look at the more detailed docs
#You know, like where your API key goes.
```

## Documentation

This very terse description is by no means the entirety of the documentation. Complete plain text documentation is available in the `docs` directory of (https://github.com/ubc-library-rc/dryad2dataverse), beginning with `index.md`.

A (much) more user-friendly version of the documentation is available at <https://ubc-library-rc.github.io/dryad2dataverse>, including full `dryadd` documentation and API information.

Or if you've cloned the git repostory above, you can use [mkdocs](https://www.mkdocs.org/) and `mkdocs serve` to have a local server version of the documentation. 
