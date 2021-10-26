---
layout: default
title: Installation  
nav_order: 5
---


# Installation

This is not a complete list of installation methods. For a complete guide to Python package installation, please see <https://packaging.python.org/tutorials/installing-packages/>. As a baseline, you will need to install a version of [Python](https;//python.org) >= 3.6.

## Simple installation using Pip

Once you've installed Python, installation via `pip` is very simple. Dryad2dataverse isn't on [PyPi](https://pypi.org/) yet, but you can still use Python's package manager, `pip`:

`pip install git+https://github.com/ubc-library-rc/dryad2dataverse.git@master`


## Manual Download
The source code for this project is available at <https://github.com/ubc-library-rc/dryad2dataverse>

To install, first clone the repository:

`git clone https://github.com/ubc-library-rc/dryad2dataverse.git`

If you wish to install with `pip`, you can use:

`pip install .'

or, if you are planning to tinker with the source code:

`pip install -e .`

### Using dryad2dataverse with a virtual environment

1. First create a directory that will hold your virtual environment

2. In a terminal, change to that directory

3. install the virtual environment using: `python3 -m venv .`

4. Activate the virtual environment: `source bin/activate` (Linux and Mac) or `.\Scripts\activate` on Windows.

5. Install as per one of the methods above.

More information on virtual environments can be found on the Python website: <https://docs.python.org/3.6/tutorial/venv.html>

## Keeping up to date

If you have installed with pip, upgrading is easy:

`pip install --upgrade git+https://github.com/ubc-library-rc/dryad2dataverse.git@master`

If you used one of the other methods, you should upgrade manually.
