# Dryad2dataverse changelog

Perfection on the first attempt is rare.

### v.0.1.3 - 22 Sept 2021

**requirements.txt**

* Updated version requirements for urllib3 and requests to plug dependabot alert hole.

**dryadd.py**

* Updated associated dryadd.py binaries

## v.0.1.2 - 4 May 2021

* fixed error in setup.py
* added binaries of `dryadd` for Windows and Mac

## v0.1.1 - 30 April 2021

**dryad2dataverse**

* improved versioning system

**dryad2dataverse.serializer**

* Fixed bug where keywords were only serialized when grants were present

**dryad2dataverse.transfer**

* Added better defaults for `transfer.set_correct_date`

**dryad2dataverse.monitor**

* Added meaningless change to `monitor.update` for internal consistency

**scripts/dryadd.py**

* Show version option added
* `transfer.set_correct_date()` added to set citation to match Dryad citation.

---

## v0.1.0 - 08 April 2021

* Initial release

