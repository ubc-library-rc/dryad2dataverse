---
layout: default
title:  
nav_order: 6
---

# Compiling and/or packaging the dryadd script 

While binaries for Windows and Mac are [supplied](https://github.com/ubc-library-rc/dryad2dataverse/tree/master/binaries), should you wish to create them yourself from the dryadd.py script, you can so so following the procedure below. This can be done with either [nuitka](https://nuitka.net/) or [PyInstaller](https://pyinstaller.readthedocs.io/en/stable/).

Note that *nuitka* will compile to a C application, but PyInstaller packages everything to create a standalone application that is not a pure C application. Whether this matters is open for debate. 

### Windows

With *nuitka*:

```
nuitka --follow-imports --onefile --windows-product-name=dryadd --windows-product-version=0.1.1 --windows-company-name="University of British Columbia Library"  \path\to\dryad2dataverse\scripts\dryadd.py
```

Note that the --windows-product-[x] options are required, but there's nothing preventing you from using whatever information you prefer. Also, the version string listed on this page is only an example; use the current version.

with *PyInstaller*:

```
python -m PyInstaller -F \path\to\dryad2dataverse\scripts\dryadd.py
```
### Mac

with *nuitka*:

The *nuitka* `--onefile` option is currently not available for MacOS. It's possible to compile using the `--standalone` flag, but the utility of this is debatable.

```
nuitka  --follow-imports --standalone /path/to/dryad2dataverse/scripts/dryadd.py
```

with *PyInstaller*:

```
python -m PyInstaller -F \path\to\dryad2dataverse\scripts\dryadd.py
```

