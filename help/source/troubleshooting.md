---
DocType: How-to guide
Feature: Building, Writing, Themes
HelpId: troubleshooting
Layout: troubleshooting
Order: 630
Section: Reference
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

The warning names both documents. Correct the file name in the link, or create the missing document.

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

## KB4IT is already running {#lock}

### Cause

Another `kb4it` command, or the terminal interface, is running.

### Fix

Wait for it to finish or close it. Only one KB4IT runs at a time, so two builds never write the same files.

## The site does not show my latest change {#stale}

### Cause

The browser shows a cached page, or the change was in a theme template, which KB4IT does not watch.

### Fix

Reload the page without the cache (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>). After editing a theme, build with `--force`.
