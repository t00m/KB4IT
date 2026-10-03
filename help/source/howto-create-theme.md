---
DocType: How-to guide
Feature: Themes, Development
HelpId: create-theme
Keyword: custom theme, template, mako, theme.json, Builder, build_page, verify.py
Level: advanced
Order: 560
Related: explanation-themes.md, dev-architecture.md
Section: Themes
Summary: Make your own theme, starting from a bundled one or from a small working example.
---

# Create your own theme

A theme is a folder with a description, some Python and some templates. Start from a copy of a bundled theme, or from the small example below.

## Start from a bundled theme {#copy}

1. Find where KB4IT keeps its themes:

    ```bash
    kb4it -L DEBUG themes 2>&1 | grep THEME_SEARCH_GLOBAL
    ```

2. Copy one into your own themes folder under a new name, replacing `<path>` with the folder the first command printed:

    ```bash
    mkdir -p ~/.kb4it/opt/resources/themes
    cp -r <path>/techdoc ~/.kb4it/opt/resources/themes/mytheme
    ```

3. In `mytheme/theme.json`, set `"id": "mytheme"` and a new `name`.
4. Set `"theme": "mytheme"` in the `repo.json` of a knowledge base and build it with `--force`.

`kb4it themes` now lists it with `scope=local`. Change the templates and CSS step by step and rebuild.

## What a theme contains {#layout}

```text
mytheme/
├── theme.json        # id, name, description, version, KB4IT it needs
├── logic/theme.py    # class Theme: builds the pages
├── templates/*.tpl   # Mako templates
├── framework/        # CSS, JavaScript, fonts, images
└── apps/default/     # optional sample knowledge base for kb4it create
```

## A small working theme {#example}

This theme, `plain`, makes a home page that lists every document and wraps each document in a simple layout. Create these files in `~/.kb4it/opt/resources/themes/plain/`.

`theme.json`:

```json
{
    "id": "plain",
    "name": "Plain",
    "author": "Ann Lopez",
    "email": "ann@example.com",
    "website": "",
    "description": "One page per document and a list of them",
    "version": "0.1.0",
    "kb4it": ">=0.7.10",
    "metadata_pages": false
}
```

`"metadata_pages": false` skips the pages per property and per value, so the theme needs no templates for them.

`logic/theme.py`:

```python
"""Plain theme: a home page listing every document, and one page per document."""

import os

from kb4it.core.util import html_id_for
from kb4it.services.builder import Builder


class Theme(Builder):

    def build(self):
        """Build the pages that do not come from a document: here, the home page."""
        var = self.get_theme_var()
        var["docs"] = [
            {"url": html_id_for(doc), "title": self.srvdtb.get_values(doc, "Title")[0]}
            for doc in self.srvdtb.get_documents()
            if not self.srvdtb.is_system(doc)
        ]
        self.distribute_md("index", self.template("PAGE_INDEX").render(var=var))
        self.srvdtb.add_document("index.md")
        self.srvdtb.add_document_key("index.md", "Title", var["repo"]["title"])
        self.srvdtb.add_document_key("index.md", "SystemPage", "Yes")

    def build_page(self, path_md):
        """Wrap each compiled page in the layout of HTML_BODY.tpl."""
        path_html = html_id_for(path_md)
        with open(path_html, encoding="utf-8") as fh:
            body = fh.read()
        var = self.get_theme_var()
        var["body"] = body
        var["title"] = self.srvdtb.get_values(os.path.basename(path_md), "Title")[0]
        with open(path_html, "w", encoding="utf-8") as fh:
            fh.write(self.template("HTML_BODY").render(var=var))
```

`templates/HTML_BODY.tpl`, the layout of every page:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${var['title']} · ${var['repo']['title']}</title>
  <link rel="stylesheet" href="resources/themes/plain/framework/plain.css">
</head>
<body>
  <header><a href="index.html">${var['repo']['title']}</a></header>
  <main>${var['body']}</main>
</body>
</html>
```

`templates/PAGE_INDEX.tpl`, the home page:

```html
<h1>${var['repo']['title']}</h1>
<ul>
% for doc in var['docs']:
  <li><a href="${doc['url']}">${doc['title']}</a></li>
% endfor
</ul>
```

`framework/plain.css`:

```css
body { max-width: 46rem; margin: 2rem auto; font-family: sans-serif; line-height: 1.6; }
header a { font-weight: bold; text-decoration: none; }
```

KB4IT copies the theme folder to `target/resources/themes/plain/`; that is why the layout links the CSS from there.

## How the pieces fit {#hooks}

| Part | Role |
|---|---|
| `build()` | Builds the pages that do not come from a document: home, lists, calendars |
| `build_page(path_md)` | Receives each compiled document and writes its final HTML |
| `build_page_key(key, values)`, `build_page_key_value(kvpath)` | Build the pages per property and per value, unless `metadata_pages` is `false` |
| `post_activities()`, `post_deploy_activities()` | Run after compilation and after the copy to `target/` |
| `site_signature()` | Returns a value that changes when every page must be rebuilt, for example when the navigation changes |
| `self.srvdtb` | The documents and their properties: `get_documents()`, `get_values(doc, key)` |
| `self.distribute_md(name, html)` | Adds a page the theme rendered |
| `self.template(name)` | Loads a template from `templates/`, or from KB4IT's shared ones |

Templates use [Mako](https://www.makotemplates.org/): `${var['repo']['title']}` prints a value, and `% for` ... `% endfor` repeats a block. `var['repo']` holds every key of `repo.json`.

`HTML_BODY` and `PAGE_INDEX` are always required, and `PAGE_KEY` and `PAGE_KEY_VALUE` too unless `metadata_pages` is `false`. A missing one stops the build with `TEMPLATE_MISSING`.

## Options in theme.json {#options}

| Key | Meaning |
|---|---|
| `kb4it` | The KB4IT versions the theme works with, such as `">=0.7.10"` or `">=0.7.10, <0.9"` |
| `metadata_pages` | `false` skips the pages per property and per value |
| `deploy_dirs` | Only these folders of the theme are copied to the website, for example `["framework"]` |

## Add your own checks {#verify}

A file `logic/verify.py` with a function `verify(repo, docs)` runs during `kb4it verify`. `docs` maps each file name to its properties. Return a list of problem messages, empty when all is well.

## Share it {#share}

- Put the theme in `source/resources/themes/<name>/` of a knowledge base to ship it with the documents.
- Or point `"theme_path"` in `repo.json` at its folder.
