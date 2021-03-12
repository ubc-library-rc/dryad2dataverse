### Uploading a study to dataverse via JSON

How to upload data to dataverse is not inherently obvious.

```
import json
import requests
DV = 'https://some.dataverse.invalid/api'
KEY = 'keygoeshere'
TARGET = 'targetshortname'
#alternately, you can have a dict to pass as sample

with open('path-to-json') as f:
	sample = json.load(f)


upload = requests.post(f'{DV}/dataverses/{TARGET}/datasets', headers=AUTH, json=sample)
```
