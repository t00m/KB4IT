---
DocType: Explanation
Feature: Getting started, Building
Keyword: static site generator, incremental, cache
Level: basic
Order: 120
Section: Get started
Summary: Files in, website out. What KB4IT does with your documents and why rebuilds are fast.
---

# How KB4IT works

KB4IT is a static website generator. It reads a folder of Markdown files and writes a folder of HTML pages. Nothing runs on the server: the result is plain files you can open from disk or put on any web server.

## Your documents stay plain files {#plain-files}

Each document is a `.md` file you can edit with any editor, keep in git and read without KB4IT. There is no database to back up and nothing to migrate: the `source/` folder is the whole knowledge base.

## Properties become pages {#properties}

At the top of each document you list properties such as `Author`, `Category` or `Tag`. KB4IT collects them from every document and builds a page for each property and for each of its values. A document tagged `backup` appears on the `backup` page next to every other document with that tag, without you maintaining any index. [More about properties](explanation-properties.md).

## A theme decides the look {#themes}

The same documents can become a technical knowledge base, a blog, a study library or the help of an application. The theme is set in `config/repo.json`, and changing it changes the whole site. [Choose a theme](explanation-themes.md).

## Only what changed is rebuilt {#incremental}

KB4IT remembers a fingerprint of every document's text and properties. On the next build it compiles only the documents that changed, and refreshes only the property pages they appear on. A knowledge base with thousands of documents rebuilds in seconds after a small edit.

The fingerprints live in `var/` inside your knowledge base. Delete that folder, or build with `--force`, and everything is compiled again.

## What a build does {#stages}

1. Check the settings, the folders and the theme.
2. Read every document and its properties.
3. Decide what needs compiling.
4. Let the theme build its own pages (index, calendars, statistics).
5. Convert the Markdown to HTML, several documents at a time.
6. Let the theme finish the pages.
7. Copy the result to `target/`.
8. Let the theme add extras, such as backups or a search index.

You see these stages in the build output as `STAGE n=1` to `n=8`. Developers find the details in [How KB4IT is built](dev-architecture.md).
