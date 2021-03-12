## Dryad API

### Get datasets

`/datasets` - Get list of all datasets

```
x=requests.get('https://datadryad.org/api/v2/datasets', headers={'Content-Type':'application/json', 'Accept':'application/json'})
```

### Get dataset with DOI


No API key appears to be required

```
headers={'accept': 'application/json', 'Content-Type': 'application/json'}
doi=doi:10.5061/dryad.bzkh1896v

#take your pick of doi2 or 3
doi2 =doi.replace('/','%2F').replace(':','%3A')
doi3  = urllib.parse.quote(doi, safe='')

x=requests.get(f'https://datadryad.org/api/v2/datasets/{doi3}', headers=headers)

```


##Notes:

It looks like it may not be too bad. The Dryad JSON isn’t exceedingly complex:

<https://github.com/CDL-Dryad/dryad/blob/master/documentation/sample_dataset.json>

which would likely need to be mapped to this:

<http://guides.dataverse.org/en/latest/_downloads/dataset-create-new-all-default-fields.json>

A minimal JSON is here:

<http://guides.dataverse.org/en/latest/_downloads/dataset-finch1.json>


Problems with Dryad relatedWorks field:

From <https://github.com/CDL-Dryad/dryad-app/blob/main/documentation/apis/dataset_metadata.md>

"relatedWorks - Relationships to other objects may be specified by giving a relationship and identifier information. The allowed values for relationship are: undefined, article, dataset, preprint, software, supplemental_information"

This isn't actually true.

