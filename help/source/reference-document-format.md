---
DocType: Reference
Feature: Writing
HelpId: document-format
Keyword: DOC_INVALID, yaml_error, missing_h1_title, frontmatter, date format
Level: basic
Order: 230
Section: Write
Summary: The rules a source document must follow, the date formats KB4IT reads and the reasons a document is rejected.
---

# Document format

## Files {#files}

| Rule | Detail |
|---|---|
| Location | Directly in the `source/` folder of the knowledge base |
| Extension | `.md` or `.markdown` |
| Encoding | UTF-8, with or without a byte order mark |
| Line endings | LF or CRLF; both give the same page and do not trigger a rebuild when a checkout changes them |
| Published name | Same name with `.html` |
| Other files | `source/resources/` is copied to the website unchanged |

## Structure {#structure}

1. A line with `---`.
2. Properties, one `Key: value` per line, in YAML.
3. A line with `---`.
4. A level 1 heading `# Title`.
5. The body in Markdown.

The title is the first `# ` line outside code blocks: a `# comment` in a fenced or indented code block is never taken for it. That line is shown in the page header, not in the body.

## Property values {#values}

| You write | KB4IT reads |
|---|---|
| `Tag: backup` | one value, `backup` |
| `Tag: backup, postgresql` | two values |
| `Tag:` | no values |
| `Summary: "Backups: how they run"` | one value; the quotes are needed because of `: ` |

## Dates {#dates}

`Date` accepts, with an optional time (`14:30` or `14:30:00`):

| Form | Example |
|---|---|
| Year first | `2026-10-03`, `2026/10/03`, `2026.10.03` |
| Day first | `03-10-2026`, `03/10/2026`, `03.10.2026` |
| ISO with `T` | `2026-10-03T14:30:00`, `2026-10-03T14:30:00Z` |
| Compact | `20261003`, `20261003143000` |

A document without a valid date is still published. It is listed after the dated ones, with an empty date.

## Markdown {#markdown}

KB4IT uses [Python-Markdown](https://python-markdown.github.io/) with these extensions:

| Extension | Gives you |
|---|---|
| `extra` | tables, fenced code, footnotes, definition lists, attributes |
| `admonition` | `!!! note` blocks |
| `toc` | heading anchors; `## Heading {#my-anchor}` sets your own |
| `sane_lists` | lists that behave as you expect |

Add more extensions with the [`markdown` setting](reference-repo-json.md#markdown).

### Code inside a note or a list {#code-in-blocks}

With these extensions a fenced block (```` ``` ````) only works at the start of a line. Inside an admonition or a list item, indent the code by four more spaces instead of fencing it:

```markdown
!!! note
    Run:

        kb4it build config/repo.json
```

To fence code there, enable `pymdownx.superfences` (from `KB4IT[extras]`) in the [`markdown` setting](reference-repo-json.md#markdown). Without it, `kb4it verify` warns with `MD_FENCE_IN_BLOCK doc=... lines=...`.

## Why a document is rejected {#invalid}

A document KB4IT cannot read is left out of the site. The build logs `DOC_INVALID` with a reason, counts it as `invalid=` in the summary, and `kb4it verify` lists it.

| Reason | Meaning | Fix |
|---|---|---|
| `missing_frontmatter` | The file does not start with `---` | Add the property block |
| `missing_frontmatter_close` | The second `---` is missing | Close the property block |
| `invalid_frontmatter` | The block is not a list of properties | Write one `Key: value` per line |
| `yaml_error line=2 col=17 ...` | YAML cannot read a line | Look at that line; usually a value with `: ` that needs quotes |
| `missing_h1_title` | No `# Title` after the properties | Add the title line |
| `reserved_name` | The file is named like a Windows device (`con`, `prn`, `aux`, `nul`, `com1` to `com9`, `lpt1` to `lpt9`), so its page cannot exist on Windows | Rename the file |

Two files whose pages differ only by letter case or extension (`Note.md` and `note.md`, or `note.md` and `note.markdown`) overwrite each other's page on macOS and Windows. The build logs `DOC_NAME_CLASH` as a warning, and `kb4it verify` reports the second file as `name_clash_with=<first>`. Rename one of them.

Set `"fail_on_invalid": true` in `repo.json` to make such a document, or a name clash, stop the build instead.
