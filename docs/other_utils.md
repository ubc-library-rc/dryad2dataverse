---
layout: default
title:  
nav_order: 6
---

# Other useful dataverse utilities

### dv_bulk_releaser

While the dryad2dataverse library and utility doesn't automatically release files, that doens't necessarily mean that you don't want to do that. To facilitate rapid release, there is a simple command line utility available as a Python script in the [scripts folder on Github](https://github.com/ubc-library-rc/dryad2dataverse/blob/master/scripts/dv_bulk_releaser.py) and as a [binary file for Windows and Mac](https://github.com/ubc-library-rc/dryad2dataverse/tree/master/binaries)

Unlike the [dryadd](script.md) utility, the script doesn't technically require the installation of dryad2dataverse, requiring only the [requests](https://docs.python-requests.org/en/master/) library. Binaries, of course, are self-contained. This makes it more generally useful even for those not moving Dryad data around.

Basic usage is very straighforward. To release all the unreleased files in a dataverse called *test* on a host called *iheartdataverse.org*:

`dv_bulk_releaser -u https://iheartdataverse.org -k your-lengthy-apikey-string-here -d test`

Of course, depending on what you're using it could be invoked with `dv_bulk_releaser.exe` or `python dv_bulk_release.py`, etc.

The utility will wait for all locks to be removed from a study before continuing to the next, and pauses between lock checks and uploads to reduce server burden.

There are more options available:

```
usage: dv_bulk_releaser [-h] [-u URL] -k KEY [-i] [--time STIME] [-v] [-r] [-d DV | -p PID [PID ...]] [--version]

Bulk file releaser for unpublished Dataverse files. Either releases individual studies or all unreleased files in a single dataverse.

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     Dataverse base URL
  -k KEY, --key KEY     API key
  -i, --interactive     Manually confirm each release
  --time STIME, -t STIME
                        Time between release attempts in seconds. Default 10
  -v                    Verbose mode
  -r, --dry-run         Only output a list of studies to be released
  -d DV, --dv DV        Short name of Dataverse to process (eg: UBC_DRYAD)
  -p PID [PID ...], --pid PID [PID ...]
                        Handles or DOIs to delete in format hdl:11272.1/FK2/12345 or doi:10.80240/FK2/NWRABI. Multiple values OK
  --version             Show version number and exit
```
