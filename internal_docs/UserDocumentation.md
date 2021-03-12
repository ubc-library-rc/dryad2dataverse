## Documentation

A good example of a user guide is here: <https://pydataverse.readthedocs.io/en/latest/developer.html>

### Pydoc-markdown

This option gives control over the order in which things are arranged in the API document:

`pydoc-markdown -I ./ -m dryad2dataverse -m dryad2dataverse.constants -m dryad2dataverse.serializer -m dryad2dataverse.transfer -m dryad2dataverse.monitor -m dryad2dataverse.exceptions --render-toc > api_reference.md`

or, after it's installed (with pip -e ./)

`pydoc-markdown -p dryad2dataverse >  api_reference.md`

or 

`pydoc-markdown -p dryad2dataverse --render-toc >  api_reference.md`

Edit manually as required (but hopefully not)

Write the `_config.yml` and `pydoc-markdown.yml` manually

HTML hierarchies are automatically created with a top level heading (`#`) and subheadings.

In the case of pydoc markdown, it's useful to create the docmentation as above, and then add an extra (`#`) to the headings. Then add a heading for the entire page. This is because each source file will create its own `<h1>` tag.

If local, you can switch to the top dir and run `mkdocs serve`, and/or automatically create github pages by using `mkdocs gh-deploy`. See <https://www.mkdocs.org/user-guide/deploying-your-docs/>

