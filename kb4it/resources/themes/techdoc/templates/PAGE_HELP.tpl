## What is KB4IT?

KB4IT is a **static website generator** for technical knowledge bases.
It converts plain-text Markdown documents into a fully navigable HTML
website — no database, no server, no login required.

Every document is a `.md` file in your source directory.
Every property you add to a document's YAML frontmatter (Author, Category,
Status, …) becomes a navigable index automatically.
The result is a self-contained folder of HTML files you can open in any
browser, host on any web server, or check into a Git repository.

## Writing documents

### Document structure

Every KB4IT document has two sections:

1. **Header** — YAML frontmatter with the document properties
2. **Body** — free-form Markdown content (the title is the first `#` heading)

```markdown
---
Author:    Jane Doe
Category:  Runbook
Status:    Released
Scope:     Infrastructure
Team:      Platform
---

# Title of the document

## First section

Write your content here using Markdown syntax.
```

The frontmatter must start at the very first line with `---` and must be
closed with another `---` on its own line. Everything between those
delimiters is the header; everything below is the body.

### Properties

Properties are key-value pairs in the YAML frontmatter:

```yaml
PropertyName: Value
```

You can use any property name you like. KB4IT automatically creates an
index page for every property and a filtered page for every value — for
example `Category: Runbook` produces `Category.html` and
`Category_Runbook.html`.

Built-in properties recognised by KB4IT:

| Property | Meaning |
|---|---|
| `Title`     | Document title (set by the first `#` heading in the body) |
| `Author`    | Author name(s), comma-separated |
| `Category`  | Document category |
| `Status`    | Document status |
| `Scope`     | Scope or domain |
| `Team`      | Owning team |
| `Tag`       | Free-form tags, comma-separated |
| `Date`      | Publish or event date (YYYY-MM-DD) |
| `Bookmark`  | `Yes` to feature on the bookmarks page |

## Replacing system pages

System pages (`index`, `help`, `all`, `events`, `bookmarks`,
`properties`, `stats`, `add`) are generated automatically. You can
override any of them by placing a file with the same basename — for
example `help.md` or `index.md` — in your source directory. KB4IT will
use your version instead of generating one automatically.

## Getting help & reporting issues

| Resource | Link |
|---|---|
| Bug reports & feature requests | [github.com/t00m/KB4IT/issues](https://github.com/t00m/KB4IT/issues) |
| Source code | [github.com/t00m/KB4IT](https://github.com/t00m/KB4IT) |
| Markdown reference | [commonmark.org](https://commonmark.org) |

When opening an issue, please include:

- KB4IT version (`kb4it --version`)
- Operating system and Python version
- The command you ran
- Relevant lines from `~/.kb4it/var/log/`
