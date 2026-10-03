---
DocType: How-to guide
Feature: Writing
HelpId: write
Keyword: frontmatter, yaml, markdown, admonition, note, warning, image, link, table, code
Level: basic
Order: 210
Related: reference-document-format.md, explanation-properties.md
Section: Write
Summary: Write a document with properties, a title, sections, links to other documents, notes, code, tables and images.
---

# Write a document

A document is a `.md` file in the `source/` folder of your knowledge base. File names become page names: `backup-check.md` is published as `backup-check.html`, so pick short names without spaces.

## Start with the properties {#properties}

Every document starts with a block of properties between two `---` lines, one `Key: value` per line:

```markdown
---
Author: Ann Lopez
Category: Procedure
Date: 2026-10-03
Tag: backup, postgresql
---
```

- Give a property several values by separating them with commas.
- Use any property names you like. Keep them singular and capitalised (`Tag`, `Team`, `Product`): `Tag` and `tag` are different properties.
- `Date` is optional. Write it as `2026-10-03` or `2026-10-03 14:30`.

!!! warning "Quote values that contain a colon followed by a space"
    `Summary: Backups: how they run` breaks the document. Write `Summary: "Backups: how they run"`.

Which properties to use depends on what you write and on the theme. The [techdoc theme](reference-theme-techdoc.md), for example, reacts to `Category`, `Priority` and `Status`.

## Give it a title {#title}

After the properties, leave an empty line and write the title as a level 1 heading. Every document needs exactly this one `#` heading:

```markdown
# Check last night's backups
```

The title comes from this line. A `Title:` property is ignored.

## Organise it in sections {#sections}

Use `##` for sections and `###` for subsections. Themes use them for the table of contents, and techdoc lets readers fold them.

```markdown
## Steps

### On the primary server
```

## Link to other documents {#links}

Link to the Markdown file; KB4IT rewrites the link to the published page:

```markdown
See [the restore procedure](restore-postgresql.md#steps).
```

If the target does not exist, the build warns with `LINK_BROKEN` and names both documents.

## Add notes and warnings {#admonitions}

Start a line with `!!!`, a type and an optional title, and indent the text by four spaces:

```markdown
!!! warning "Stop the application first"
    The restore replaces every table in the database.
```

Common types are `note`, `tip`, `important`, `warning` and `danger`.

## Show commands and code {#code}

Fence code with three backticks and name the language:

````markdown
```bash
pg_restore -d appdb appdb.dump
```
````

## Add tables {#tables}

```markdown
| Server | Role    |
|--------|---------|
| db01   | primary |
| db02   | replica |
```

## Add images {#images}

Put images in `source/resources/images/`. KB4IT copies `source/resources/` to the website as it is, so link to them like this:

```markdown
![Backup report](resources/images/backup-report.png)
```

## Check your work {#check}

Build the site, or check the documents without building:

```bash
kb4it verify ~/mykb/config/repo.json
```

It lists every document KB4IT cannot read and why. [Document format](reference-document-format.md) explains each reason.
