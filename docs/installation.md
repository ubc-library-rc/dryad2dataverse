---
layout: default
title: Installation  
nav_order: 5
---


# Installation

This is not a complete list of installation methods. For a complete guide to Python package installation, please see <https://packaging.python.org/tutorials/installing-packages/>. As a baseline, you will need to install a version of [Python](https://python.org) >= 3.6.

## Simple installation using Pip

Once you've installed Python, installation via `pip` is very simple. Dryad2dataverse isn't on [PyPi](https://pypi.org/) yet, but you can still use Python's package manager, `pip`:

`pip install git+https://github.com/ubc-library-rc/dryad2dataverse.git@master`

Of course, if you want to use a branch other than _master_, you can switch _master_ for the branch you want. This is not recommended, though, as the _master_ branch contains the most current [stable] release.

## Manual Download

### Precompiled binaries

Compiled versions of the `dryadd` migrator for selected operating systems and architectures are available at the [releases page](https://github.com/ubc-library-rc/dryad2dataverse/releases). Note that binary releases may lag behind the Python, and of course the binary files don't include the Python package.

### Source code
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

If you have installed with pip, upgrading is easy and very similar to the normal upgrade procedure:

`pip install --upgrade git+https://github.com/ubc-library-rc/dryad2dataverse.git@master`

If you used one of the other methods, you should upgrade manually.
