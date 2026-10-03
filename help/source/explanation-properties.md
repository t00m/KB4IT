---
DocType: Explanation
Feature: Writing, Configuration
Keyword: metadata, key, value, navigation, ignored_keys, index
Level: basic
Order: 220
Section: Write
Summary: Every property you use becomes a page, and every value becomes a list of the documents that share it.
---

# How properties become navigation

In KB4IT you never maintain an index by hand. The properties you write at the top of each document are the index.

## A page for each property and each value {#pages}

Take three documents:

| Document | Category | Tag |
|---|---|---|
| `restore-postgresql.md` | Procedure | backup, postgresql |
| `check-backups.md` | Procedure | backup |
| `disk-full.md` | Incident | postgresql |

KB4IT builds:

- `Category.html`, listing the values `Procedure` and `Incident`.
- `Category_Procedure.html`, listing the two procedures.
- `Tag.html`, plus `Tag_backup.html` and `Tag_postgresql.html`.

Add a property to one document and its pages appear on the next build. Remove the last document that uses a value and its page goes away.

## Your vocabulary, your structure {#vocabulary}

There is no fixed list of properties. A team that writes runbooks may use `Server`, `Product` and `Team`; a reading list may use `Author` and `Genre`. Whatever you use consistently becomes the way readers browse the site.

A few habits keep the navigation clean:

- Use the same spelling every time: `PostgreSQL` and `Postgresql` are two values.
- Prefer a specific property to a generic tag: `Product: nginx` gives readers a Product menu, while `Tag: nginx` hides it among other tags.
- Keep property names singular: `Tag`, not `Tags`.

## Properties that do not get pages {#excluded}

- `Title` comes from the `#` heading and is never a property page.
- `Date` sorts documents and feeds calendars; it has no value pages.
- Properties listed in `ignored_keys` in `repo.json` stay in the documents but get no pages. Use it for values that are unique per document, such as a ticket number.

## Rebuilds follow your properties {#rebuilds}

When you change a property, KB4IT recompiles the document and every page that lists it, so a renamed category never leaves stale lists behind. This is why changing properties takes a little longer than changing text.
