---
DocType: How-to guide
Feature: Themes
HelpId: customize-templates
Keyword: overrides, template, footer, css, static, library, customize, change one page
Level: advanced
Order: 555
Related: explanation-themes.md, howto-create-theme.md, reference-repo-json.md
Section: Guides
Summary: Change one template of a theme, or add your own CSS and scripts, without copying the whole theme.
---

# Change one template of a theme

A knowledge base can replace single templates of its theme and add its own files to the website. The theme stays as it is, so it keeps receiving the updates of new KB4IT versions.

## Replace a template {#template}

1. Create the folder `overrides/templates/` next to `config/` and `source/`.
2. Copy the template you want to change from the theme into it, keeping its name. The bundled themes are in the KB4IT package; this prints the folder of techdoc:

        python3 -c "import kb4it, os; print(os.path.join(os.path.dirname(kb4it.__file__), 'resources', 'themes', 'techdoc', 'templates'))"

3. Edit the copy and build. The build log shows `TEMPLATE_OVERRIDE name=<template>`, and every page is rebuilt.

KB4IT looks for a template in this order and uses the first it finds:

1. `overrides/templates/` of the knowledge base.
2. The `templates/` folder of the theme.
3. The common templates of KB4IT.

Delete the copy to go back to the theme's template.

!!! warning
    A template you copied does not change when the theme does. After upgrading KB4IT, compare your copy with the theme's new version.

## Change the Add page {#editor}

With the [editor](howto-write-document-editor.md) on, the Add page uses two shared templates.

- `PAGE_ADD.tpl` makes the cards. You can replace it, like any other template, from `overrides/templates/`.
- `EDITOR_DIALOGS.tpl` makes the dialogs and the data the editor reads. Do not replace it: the editor scripts depend on its markup. A card page prints it once with `${var['page']['editor_dialogs'] | n}`.

To change the skeletons, put your own files in `overrides/templates/skeletons/`. They replace the skeletons of the theme completely; see [Use your own skeletons](howto-write-document-editor.md#skeletons).

!!! warning
    A `PAGE_ADD.tpl` override written before the editor came to every theme still renders, but it has no editor: its buttons do nothing. Delete it, or copy the current template and apply your changes again.

## Add your own files {#static}

Everything in `overrides/static/` is copied, as it is, into the website root. Put stylesheets, scripts or images there, for example `overrides/static/css/site.css`, and link them from an overridden template.

Use another folder than `overrides` with `"overrides": "my-folder"` in `repo.json`.

## Example: a browser library of your own {#library}

Mermaid diagrams and KaTeX formulas are built in; see [diagrams](reference-document-format.md#diagrams). For another browser library, such as a chart or a map:

1. Put the library file in `overrides/static/js/`.
2. Copy techdoc's `HTML_FOOTER.tpl` into `overrides/templates/` and add the script lines just before its `</body>` line (anything after `</html>` is dropped):

        <script src="js/library.min.js"></script>
        <script>startLibrary();</script>

3. Write what the library needs in a document as an HTML block. Markdown keeps HTML blocks as they are.
