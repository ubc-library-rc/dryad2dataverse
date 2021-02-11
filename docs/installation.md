---
layout: default
title: Installation  
nav_order: 5
---


# Installation

This is not a complete list of installation methods. For a complete guide to Python package installation, please see <https://packaging.python.org/tutorials/installing-packages/>.

### Requirements

* requests >= 2.21.0  
* requests-toolbelt >= 0.9.1
* nose >= 1.3.7 

Actually, it will probably work just fine with earlier versions, but that's what development started with.

### Pip from source

The source code for this project is available at <https://github.com/ubc-library-rc/dryad2dataverse>

To install, first clone the repository:

`git clone https://github.com/ubc-library-rc/dryad2dataverse.git`

Depending on your needs, you may wish to keep dryad2dataverse in a virtual environment.

In this case, you will need to perform the following steps to create your virtual environment. First, create a directory to hold your virtual environment:

`mkdir -p \path\to\sample_venv`

Create the virtual environment:

`python3 -m venv \path\to\sample_venv`

Finally, enable the virtual environment:

`source \path\to\sample_venv\bin activate`

Creating the virtual environment is not required if you don't mind having the prerequisites installed. More information on virtual environments can be found on the Python website: <https://docs.python.org/3.6/tutorial/venv.html>

Once it's downloaded:

```
cd dryad2dataverse
pip install .
```
