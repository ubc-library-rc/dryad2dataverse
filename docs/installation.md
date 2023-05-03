---
layout: default
title: Installation  
nav_order: 5
---


# Installation

This is not a complete list of installation methods. For a complete guide to Python package installation, please see <https://packaging.python.org/tutorials/installing-packages/>. As a baseline, you will need to install a version of [Python](https://python.org) >= 3.6.

## Simple installation using Pip

Once you've installed Python, installation via `pip` is very simple:

`pip install dryad2dataverse`

Of course, if you want to use a branch other than _master_, you can switch _master_ for the branch you want. This is not recommended, though, as the _master_ branch contains the most current [stable] release.

### Installing from the Github repository

If you require a specific commit, branch, etc, you can install directly from Github using `pip`:

`pip install git+https://github.com/ubc-library-rc/dryad2dataverse.git@master`

Of course, you can also install other branches or specific commits as required; see the documentation for `pip` on how to do that.

## Manual Download

### Precompiled binaries

Compiled versions of the `dryadd` migrator for selected operating systems and architectures are available at the [releases page](https://github.com/ubc-library-rc/dryad2dataverse/releases). Note that binary releases may lag behind the Python, and of course the binary files don't include the Python package.

### From local source code
The source code for this project is available at <https://github.com/ubc-library-rc/dryad2dataverse>

To install, first clone the repository:

`git clone https://github.com/ubc-library-rc/dryad2dataverse.git`

This will place the source at `whatever/directory/you/are/in/dryad2dataverse`

If you wish to install with `pip`, you can use:

```
cd dryad2dataverse
pip install .
```

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

`pip install --upgrade dryad2dataverse.git`
