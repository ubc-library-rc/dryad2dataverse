---
layout: default
title: FAQ
nav_order: 20
---
# Frequently asked questions

#### **Why did dryadd just download everything again?**

The Dryad API has not yet reached a stable state and the output from the API is subject to format changes. This has the possibility of triggering a potentially false positive change indication in `dryad2dataverse.monitor.Monitor`.

Using _dryad2dataverse_ >= v0.3.1 uses (hopefully) a more robust change checking mechanism which will eliminate (or at least drastically reduce) the number of false positive hits. In addition _dryadd_ >= v0.4.1 includes a warning mechanism and auto-shutdown if the number of studies to be uploaded exceeds a user specified threshold, allowing the user to examine the nature of the problem to see if, in fact, there **are** multiple studies with changes.

Note that the false positives do not upload incorrect data; they will just create a new version of the _same_ data set. This is can be annoying and potentially use a lot of storage space, but for small collections it is more of an annoyance than a problem.

#### **Why is the upload script (dryadd.py) constantly crashing with SMTP errors?**

**Updated 7 December 2022**

Version 0.5.0 + should solve this issue. Google authentication using app passwords is now supported, but requires that the account use two-factor authentication.

**If you are not at v0.5.0+, the old, deprecated answer is:**

If you are using Gmail to send messages about your migration, there are a few potential hurdles.

1. You *must* enable [**less secure app access**](https://support.google.com/accounts/answer/6010255?hl=en).

2. Even when you do that, it can still crash with no obvious explanation or a mysterious authentication error. In this case, the script may be encountering a Captcha security measure. You can remove this by going to <https://accounts.google.com/DisplayUnlockCaptcha> before running your script (when logged into the account which you are using, of course).

3. The settings revert back to normal after some period of time of which I am not aware. Daily or weekly updates *should* be OK, but monthly ones will probably fail with SMTP errors as the service reverts to defaults.

Your other option is to not use Gmail.

**smtplib** exceptions will cause a script crash, so if you are experiencing persistent mail problems and still wish to use the script, you may wish disable emailing log messages.

This is easily accomplished by commenting out the section starting with `elog = email_log(` in `scripts/dryadd.py`. Obviously you can't do this if you're using a binary dryadd.

Currently email notifications are a mandatory part of the `dryadd.py` app, but this may be optional and/or more advanced mail handling may be available in later releases.

_All error messages are written to the log anyway,_ so if you disable emailing of log messages you can still see them in the transfer log.

#### **Why is the upload script (dryadd.py) is crashing with dryad2dataverse.exceptions.DownloadSizeError size errors?**

There are a few instances when the script will crash on an exception and this is one of them. This occurs when the download size does not match reported size of the file in Dryad.

There are two obvious alternatives here. The first is that the download was corrupted in some way. In this case, you should go to your temporary file location and delete the offending file(s). Run the script again and it should continue as normal.

The other, much more insidious error comes from Dryad. A very few Dryad studies have files with duplicate names. These are not visible on the web page for the study, but are visible via the file API. As the files are named on download with the names given to them by Dryad, this is a problem because two files cannot have the same name. Additionally, because only *one* of the files appears on the Dryad page *without* any associated metadata, it's not possible to tell which one is which without a manual inspection.

Presumably this should not be happening, as the number of files on the Dryad web page and the number of files available via API should match. There is no way to resolve this error without consulting the people at Dryad.

In this case, the only workable solution is to exclude the problematic Dryad study from the upload. Do this by noting the Dryad DOI and then using the `-x, --exclude` switch.

`python3 dryadd.py [bunch of stuff] -x doi:10.5061/dryad.7pd82 &`


#### **Why is the upload script (dryadd.py) is crashing with 404 errors for data files?**

Related to the error above, in a very few instances the Dryad web page is displaying an embargo on the page, but the Dryad JSON *does not* have `{curationStatus: Embargoed}`, which means that `dryad2dataverse.serializer.Serializer.embargo == False`.

This means that instead of skipping the download, it is attempted. But the embargo flag is incorrect and the files are unavailable, generating a 404 error. 

As there is no other way to determine embargo status other than by inspecting the Dryad study web page (and even then perhaps not), the solution is to exclude the DOI using the `-x` switch.

`python3 dryadd.py [bunch of stuff] -x doi:10.5061/dryad.b74d971 &`

#### **Why is my transfer to Dataverse not showing up as published?**

**dryad2dataverse** does not _publish_ the dataset. That must still be done via the Dataverse GUI or API. 

Publication functionality has been omitted _by design_:

* File size limits within a default Dataverse installation that do not apply to Dryad, so it's possible that some files need to be moved with the assistance of a Datverse system administrator

* Although every attempt has been made to map metadata schemas appropriately, it's undoubtedly not perfect. A quick once-over by a human can notice any unusual or unforeseen errors

* Metadata quality standards can vary between Dryad and a Dataverse installations. A manual curation step is sometimes desirable to ensure that all published records meet the same standards.

#### **But I don't want to manually curate my data**

It's possible to publish via the Dataverse API. If you *really* want to publish automatically, you can obtain a list of unpublished studies from Dataverse and publish them programatically. This is left as an exercise for the reader.

#### **Why does my large file download/upload fail?**

By default, Dataverse limits file sizes to 3 Gb, but that can vary by installation. `dryad2dataverse.constants.MAX_UPLOAD` contains the value which should correspond to the maximum upload size in Dataverse. If you don't know *what* the upload size is, contact the system administrator of your target Dataverse installation to find out.

To upload files exceeding the API upload limit, you will need to speak to a Dataverse administrator.

#### **Why does my upload of files fail halfway?**

Dataverse will automatically cease ingest and lock a study when encountering a file which is suitable for tabular processing. The only way to stop this behaviour is to prohibit ingest in the Dataverse configuration, which is probably not possible for many users of the software.

To circumvent this, dryad2dataverse attempts to fool Dataverse into not processing the tabular file, by changing the extension or MIME type at upload time. If this doesn't work and tabular processing starts anyway, by default the `dryadd.py` script will wait for tabular processing to finish before continuing with the next file. As you may imagine, that can add some time to the process.

*If you are a super-user*, you can attempt a forcible unlock allow uploads to continue. This process, unfortunately, is not perfect as for some reason Dataverse returns 403 errors instead of unlocking, albeit infrequently.

#### **Why is a file which should not be a tabular file a tabular file?**

As a direct result of the above, tabular file processing has (hopefully) been eliminated. It's still possible to create a tabular file by [reingesting it.](https://guides.dataverse.org/en/latest/api/native-api.html#reingest-a-file "Reingest via API")

Unless you are are the administrator of a Dataverse installation, you likely don't have control over what is or is not considered a tabular file. **dryad2dataverse** attempts to block all tabular file processing, but the process is imperfect. The only way to guarantee that tabular processing won't occur is to stop it on the Dataverse server.

If you are not a Dataverse super-user, then you are out of luck and my poor spoofing attempts are what you get.

 _Sic vita._

#### **Why does the code use camel case instead of snake case for variables?**

By the time I realized I should be using snake case, it was too late and I was already consistently using camel case. <https://www.python.org/dev/peps/pep-0008/#a-foolish-consistency-is-the-hobgoblin-of-little-minds>
