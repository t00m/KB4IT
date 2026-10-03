---
DocType: How-to guide
Feature: Writing, Building, Terminal interface
HelpId: tips
Layout: tips
Order: 650
Section: Reference
Summary: Small things that make writing and building with KB4IT easier.
---

# Tips

## Build with one command {#compile-script}

`kb4it create` writes `bin/compile.sh`. Run it, or bind it to a key in your editor. [More](howto-build.md)

## Start from a skeleton {#skeletons}

In techdoc, **Add document** fills a ready-made skeleton per category and copies it for you. [More](reference-theme-techdoc.md#pages)

## Let properties do the filing {#properties}

A `Product` or `Team` property gives readers a menu for free. Use it instead of a long list of tags. [More](explanation-properties.md#vocabulary)

## Check before you commit {#verify}

`kb4it verify` exits with status 1 on any problem, so it works as a git pre-commit hook. [More](howto-build.md#verify)

## Hide what is unique {#ignored-keys}

Add properties such as a ticket number to `ignored_keys`: they stay in the document but do not create one page per value. [More](reference-repo-json.md#optional)

## Preview over http {#preview}

**Browse via Web Server** in the terminal interface serves the site on `127.0.0.1`, closer to how readers will see it. [More](howto-use-tui.md#project)

## Link sections, not just pages {#anchors}

`[restore](restore-postgresql.md#steps)` opens the page at the right section. Set your own anchor with `## Steps {#steps}`. [More](reference-document-format.md#markdown)
