# Various programming notes and links
## Creating a singleton object
### dryad2dataverse.monitor.Monitor

<https://stackoverflow.com/questions/12305142/issue-with-singleton-python-call-two-times-init>

**monitor.diff_files()**
        '''https://docs.python.org/3/library/stdtypes.html#frozenset.symmetric_difference

        Also:
        tuple from string:
        https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string

        needsdel = set(a).superset(set(b))
        # returns False if all of a not in e
        if False:
            if not set(a) - (set(a) & set(b)):
                return set(a) - (set(a) & set(b))

        needsadd = set(f).issuperset(set(a))
        if True: return set(f) - (set(f) & set(a))

        '''

**dryad2dataverse.serializer._assemble_json()
#TODO see https://github.com/CDL-Dryad/dryad-app/blob/31d17d8dab7ea3bab1256063a1e4d0cb706dd5ec/stash/stash_datacite/app/models/stash_datacite/related_identifier.rb

