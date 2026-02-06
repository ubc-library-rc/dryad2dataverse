---
layout: default
title: Installation  
nav_order: 5
---


# Installation

## Using pipx

Using [`pipx`](https://pipx.pypa.io/latest/installation/){:target="_blank"} is simple, reliable and easy:

`pipx install dryad2dataverse`

## Using pip

If you are attached to Python's native `pip` that's easy too:

`pip install dryad2dataverse`

### Installing from the Github repository

If you require a specific commit, branch, etc, you can install directly from Github using `pip`:

`pip install git+https://github.com/ubc-library-rc/dryad2dataverse.git@master`

Of course, you can also install other branches or specific commits as required; see the documentation for `pip` on how to do that.

## Manual Download

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

## Keeping up to date

Upgrades are similarly easy:

`pipx upgrade dryad2dataverse` 

or 

`pip install --upgrade dryad2dataverse.git`

---

This is not a complete list of installation methods. For a complete guide to Python package installation, please see <https://packaging.python.org/tutorials/installing-packages/>. 

