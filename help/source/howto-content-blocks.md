---
DocType: How-to guide
Feature: Writing
HelpId: content-blocks
Keyword: code, copy, language, fold, table, sticky, search, sort, tabs, details, note, back to top
Level: basic
Order: 260
Related: howto-write-documents.md, reference-theme-techdoc.md
Section: Guides
Summary: Copy code, fold long blocks, search, sort and scroll tables, write author tabs and collapsible notes.
---

# Make code, tables and notes easier to read

The techdoc theme improves the content blocks of every document. You write plain Markdown; the theme adds the buttons and the layout. The other themes keep their own styles.

## Code blocks

A fenced code block gets a bar with the language from its info string and a copy button:

````markdown
```bash
systemctl --user restart kb4it
```
````

- The language label is the word after the opening fence (`bash`, `python`, `yaml`). A fence without a language gets the copy button and no label.
- **Copy** puts the code on the clipboard and says **Copied** for two seconds. It works from a local file too.
- A block with more than 30 lines shows the first 20 and a **Show all N lines** button. Nothing is removed: the reader opens it in place.
- Printing shows the whole block, without the copy button, the label or the show button.

Mermaid diagrams are not code blocks and get no copy button.

## Tables

Every table gets the theme's table style: padded cells, a line between rows, a light band on every other row and a highlight under the pointer. A wide table scrolls sideways inside its own box, so it never widens the page. A table with more than 15 rows keeps its header visible while the reader scrolls.

A table with more than 15 rows also gets a **Filter rows** box and the number of rows above it, and a click on a column heading sorts by that column (click again to reverse). A column of numbers, with or without a unit such as `10 GB` or `1,5 %`, sorts by the number. This needs a plain grid: one header row, no merged cells and the same number of cells in every row; any other table keeps only the style and the scrolling. `"table_filter": false` in the theme's `theme.json` turns the search and sort off.

On paper the table prints in full, every row even after a search, without the scrolling box or the search box.

Write an ordinary Markdown table; the theme does the rest:

```markdown
| Transaction | Purpose |
|---|---|
| SM21 | System log |
| ST22 | ABAP dumps |
```

## Author tabs

Tabs are for variants of the same content, such as Linux and Windows or Oracle and DB2. Do not use them to hide sections a reader may need: browser search does not find text in a hidden tab.

Tabs come from the `pymdown-extensions` package, which installs with KB4IT. Turn the two extensions on in `repo.json`:

```json
"markdown": {
  "extensions": ["pymdownx.tabbed", "pymdownx.details"],
  "extension_configs": {
    "pymdownx.tabbed": {"alternate_style": true}
  }
}
```

`alternate_style` is required: the techdoc styles target that markup. Write a tab set like this:

````markdown
=== "Linux"

    Run `dnf install httpd`.

=== "Windows"

    Run `winget install Apache.Httpd`.
````

The tab bar works without JavaScript, and the theme draws it like the tabs of the info card. On paper every panel prints, with its label as a bold line above it.

## Collapsible notes

A collapsible note looks like an admonition and opens when the reader clicks its title. It also needs `pymdown-extensions`, enabled as above:

```markdown
??? note "Read this first"

    The service restarts during the change.
```

The type after `???` sets the colour, as with `!!!`: `note`, `tip`, `warning`, `caution`, `success` and `danger`. A note prints open, even when the reader left it closed on screen.

## Back to top

On a long document a **Back to top** button appears at the bottom right after one screen of scrolling. It is not printed. The link in the page footer works at any time.
