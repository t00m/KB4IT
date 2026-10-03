---
DocType: Tutorial
Feature: Getting started
HelpId: first-steps
Level: basic
Order: 110
Related: howto-write-documents.md, howto-build.md
Section: Get started
Summary: Install KB4IT, create a knowledge base, write a document and open your first website.
---

# Get started with KB4IT

This tutorial takes you from nothing to a working website in about ten minutes. You need a GNU/Linux computer with Python 3.11 or newer.

## Install KB4IT {#install}

The quickest way is [uv](https://docs.astral.sh/uv/):

```bash
uv tool install KB4IT
kb4it --version
```

The second command prints the version, for example `KB4IT 0.8.0`. Other ways to install are in [Install KB4IT](howto-install.md).

## Create a knowledge base {#create}

A knowledge base is a folder. KB4IT creates it from a theme, here `techdoc`:

```bash
kb4it create techdoc ~/mykb
```

You get this layout:

```text
mykb/
├── bin/compile.sh      # builds the site with one command
├── config/repo.json    # title, theme and other settings
├── source/             # your Markdown documents go here
└── target/             # the generated website appears here
```

Open `~/mykb/config/repo.json` and change `"title"` to the name of your site.

## Write your first document {#write}

Create `~/mykb/source/backup-check.md` with any text editor:

```markdown
---
Author: Ann Lopez
Category: Procedure
Date: 2026-10-03
Tag: backup
---

# Check last night's backups

## Steps

1. Open the backup report.
2. Check that every job ended with status OK.
```

The block between the two `---` lines holds the document's properties. The `#` line is its title. Everything else is ordinary Markdown.

## Build the website {#build}

```bash
kb4it build ~/mykb/config/repo.json
```

The last lines tell you what happened:

```text
[WORKFLOW] SUMMARY docs_total=1 compiled=1 skipped=0 invalid=0 ...
[WORKFLOW] URL /home/ann/mykb/target/index.html
```

## Open it {#open}

```bash
xdg-open ~/mykb/target/index.html
```

Your document is there, and so are pages you did not write: one for the author `Ann Lopez`, one for the category `Procedure`, one for the tag `backup`, a calendar of events and statistics. That is the idea behind KB4IT: [properties become navigation](explanation-properties.md).

## Next steps {#next}

- [Write documents](howto-write-documents.md) with notes, links, tables and images.
- Rebuild after every change; it is fast because [only what changed is rebuilt](howto-build.md).
- Prefer menus to commands? Run `kb4it` alone to open the [terminal interface](howto-use-tui.md).
- [Publish the site](howto-publish-github-pages.md) when you are ready.
