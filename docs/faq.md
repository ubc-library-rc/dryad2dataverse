---
layout: default
title: FAQ
nav_order: 20
---

**Why is my transfer to Dataverse not showing up as published?**

**dryad2dataverse** does not _publish_ the dataset. That must still be done via the Dataverse GUI or API. 

Publication functionality has been intentionally omitted as there are file size limits within a default Dataverse installation that do not apply to Dryad, and Dataverse installations are [more] often subject to manual data curation.

**Why does my large file download/upload fail?**

By default, Dataverse limits file sizes to 3 Gb, but that can vary by installation. `dryad2dataverse.constants.MAX_UPLOAD` contains the value which should correspond to the maximum upload size in Dataverse. If you don't know *what* the upload size is, contact the system administrator of your target Dataverse installation to find out.

**Why does my upload fail halfway?**

Dataverse will automatically cease ingest and lock a study when encountering a file which is suitable for tabular processing. The only way to stop this behaviour is to prohibit ingest in the Dataverse configuration, which is probably not possible for many users of the software.

To circumvent this, dryad2dataverse attempts to fool Dataverse into not processing the tabular file, by changing the extension or MIME type at upload time. This process, unfortunately, is not foolproof.

**Why is a file which should be a tabular file not a tabular file?**

As a direct result of (3) above, tabular file processing has (hopefully) been eliminated. It's still possible to create a tabular file by [reingesting it.](https://guides.dataverse.org/en/latest/api/native-api.html#reingest-a-file "Reingest via API")

**Why does the code use camel case instead of snake case for variables?**

By the time I realized I should be using snake case, it was too late and I was already consistently using camel case. <https://www.python.org/dev/peps/pep-0008/#a-foolish-consistency-is-the-hobgoblin-of-little-minds>
