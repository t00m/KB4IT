---
DocType: How-to guide
Feature: Building, Writing, Themes
HelpId: troubleshooting
Layout: troubleshooting
Order: 630
Section: Questions
Summary: What to do when a document is missing, a link is broken, a theme is refused or the build stops.
---

# Troubleshooting

## A document is missing from the site {#doc-missing}

### Cause

KB4IT could not read it. The build log shows `DOC_INVALID doc=<file> reason=...` and the summary counts it as `invalid=`.

### Fix

Run `kb4it verify CONFIG` to list every such document and the reason, then see [why a document is rejected](reference-document-format.md#invalid). The most common one is a value with `: ` that needs quotes.

## The build warns LINK_BROKEN {#link-broken}

### Cause

A document links to a `.md` file that is not in `source/`.

### Fix

The warning names both documents. Correct the file name in the link, or create the missing document. `kb4it verify` lists every broken link at once, and also links to a section that does not exist (`ANCHOR_MISSING`); it ends with exit status 1 when it finds any, so it can stop a publishing workflow.

## The build stops with CONFIG_KEY_MISSING {#config-key}

### Cause

`repo.json` lacks `title`, `theme`, `source` or `target`.

### Fix

Add the key the message names. See [repository settings](reference-repo-json.md#required).

## The build stops with THEME_NOT_FOUND {#theme-not-found}

### Cause

No theme has the name in `"theme"`.

### Fix

Run `kb4it themes` and use one of the names it lists. For your own theme, check its folder name and the `id` in its `theme.json`.

## The build fails with TEMPLATE_COMPILE_FAIL {#template-compile}

### Cause

A template in `overrides/templates/` or in your own theme has a Mako syntax error, such as a `% if` without its `% endif`. Every page that uses it fails.

### Fix

Open the file in `path=` and fix the line the message names (`at line: N`). The build stops on such a template instead of falling back to the theme's own.

## A theme is refused with THEME_REQUIREMENT_UNMET {#requirement}

### Cause

The theme needs a newer KB4IT than the one installed.

### Fix

[Upgrade KB4IT](howto-install.md#upgrade). The message shows the version the theme asks for and the one you have.

## The build stops with SOURCE_MISSING {#source-missing}

### Cause

The `source` folder in `repo.json` does not exist.

### Fix

Create it, or correct the path. Relative paths start at the knowledge base folder, the one that holds `config/`.

## KB4IT is already working on this repository {#lock}

### Cause

Another `kb4it build`, or a build started from the terminal interface, is working on the same knowledge base. The message names its process id (PID).

### Fix

Wait for it to finish. Only one build of a knowledge base runs at a time, so two builds never write the same files. Other knowledge bases are not affected.

If no KB4IT is running, the lock was left by a process that no longer exists and the next build takes it. The lock file is `var/kb4it.lock` inside the knowledge base.

## The build stops with MD_EXTENSION_MISSING {#md-extension}

### Cause

`repo.json` asks for a Markdown extension, in the `markdown` block, that is not installed where KB4IT runs.

### Fix

Install the package the message names, in the same environment as KB4IT. For PyMdown Extensions: `uv tool install --force "KB4IT[extras]"`. Or remove the extension from `markdown.extensions`.

## The build warns DOC_NAME_CLASH or leaves out a document with DOC_NAME_RESERVED {#names}

### Cause

`DOC_NAME_CLASH`: two documents would publish pages whose names differ only by letter case or extension, such as `Note.md` and `note.md`. macOS and Windows treat them as the same file, so one page would overwrite the other.

`DOC_NAME_RESERVED`: the file cannot be a document. Two kinds of name are reserved:

- A Windows device name (`con`, `prn`, `aux`, `nul`, `com1` to `com9`, `lpt1` to `lpt9`). Windows cannot create its page.
- A page the theme writes itself. techdoc, blog and bookshelf write `404.html`, so a document named `404.md` is left out. apphelp has its own reserved names.

### Fix

Rename the file. `kb4it verify` lists every such name.

## Text between dollar signs shows as a formula {#dollar-sign}

### Cause

`$...$` is formula syntax. The text between two dollar signs is drawn as a formula, so a line such as "The plans cost \$5/\$10" shows a formula instead of text. A dollar sign counts as an opening one when a non-space character follows it, and as a closing one when a non-space character comes before it and no other `$` is in between. "costs \$5 and \$10" stays text because of the spaces; "\$5/\$10" does not.

### Fix

- Write `\$` for a literal dollar sign: `The plans cost \$5/\$10`.
- Or put the text in inline code, where nothing changes: `` `$5/$10` ``.

See [formulas](reference-document-format.md#formulas) for the exact rules.

## The page shows a red bar "KB4IT build failed" {#serve-error}

### Cause

`kb4it serve` (or **Browse via Web Server** in the terminal interface) rebuilt the site after a change, and the build failed. The bar shows the first error.

### Fix

Correct the document or setting the message names and save it. The next good build removes the bar.

## The site does not show my latest change {#stale}

### Cause

The browser shows a cached page, or the change was in a theme template, which KB4IT does not watch.

### Fix

Reload the page without the cache (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>). After editing a theme, build with `--force`.

## Still stuck? {#still-stuck}

Ask on [GitHub issues](https://github.com/t00m/KB4IT/issues). Say what you ran, what you expected, and paste the log or the message you got.
