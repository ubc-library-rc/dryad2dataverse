'''
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
'''

VERSION = (0, 6, 0)

__version__ = '.'.join([str(x) for x in VERSION])
