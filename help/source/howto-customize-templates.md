---
DocType: How-to guide
Feature: Themes
HelpId: customize-templates
Keyword: overrides, template, footer, css, static, mermaid, customize, change one page
Level: advanced
Order: 555
Related: explanation-themes.md, howto-create-theme.md, reference-repo-json.md
Section: Themes
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

## Add your own files {#static}

Everything in `overrides/static/` is copied, as it is, into the website root. Put stylesheets, scripts or images there, for example `overrides/static/css/site.css`, and link them from an overridden template.

Use another folder than `overrides` with `"overrides": "my-folder"` in `repo.json`.

## Example: diagrams with Mermaid {#mermaid}

[Mermaid](https://mermaid.js.org/) draws diagrams from text in the browser. To use it in techdoc:

1. Download `mermaid.min.js` into `overrides/static/js/`.
2. Copy techdoc's `HTML_FOOTER.tpl` into `overrides/templates/` and add these lines just before its `</body>` line (anything after `</html>` is dropped):

        <script src="js/mermaid.min.js"></script>
        <script>mermaid.initialize({startOnLoad: true});</script>

3. Write each diagram in a document as an HTML block. Markdown keeps HTML blocks as they are:

        <div class="mermaid">
        graph LR
          Write --> Build --> Publish
        </div>

The same works for other browser libraries, such as KaTeX for formulas.
