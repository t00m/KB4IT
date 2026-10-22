---
DocType: How-to guide
Feature: Writing
HelpId: editor
Keyword: editor, add page, techdoc, markdown, frontmatter, properties, toolbar, save, completion
Level: basic
Order: 215
Related: howto-write-documents.md, reference-theme-techdoc.md
Section: Guides
Summary: Write a new document in the editor of the techdoc Add page and save it into the source folder.
---

# Write a document in the editor

The Add page of a [techdoc](reference-theme-techdoc.md) site (`add.html`) is a Markdown editor that knows your repository. It suggests the properties and values you already use, warns about mistakes the build would report, and saves the file for you. It works offline, also from `file://`.

## Create the document {#create}

1. Open `add.html` and click **Create** on the card of a category. The editor opens with a skeleton for that category.
2. Write the title: the text of the `#` heading is already selected, so type to replace it.
3. Fill the properties in the **Properties** pane or in the text. Both stay in sync.
4. Write the body. Use the toolbar for headings, lists, tables, notes, diagrams and formulas.
5. Click **Save**.

## Fill the properties {#properties}

Each property of the frontmatter is a row in the Properties pane.

- Type in the value box to get suggestions from your repository, most used first, with counts. Press Enter or click a suggestion to add the value as a chip. Click the cross on a chip to remove it.
- To add a property, pick a name in the selector, or choose "New property..." and type a new one.
- Click a word in the cloud of a property to add that value.
- A value cannot contain a comma: KB4IT splits values on commas.
- A property written as a block list, over several lines, with an anchor, or with a number that YAML would rewrite (`1.50`, `010`) is read-only in the pane. It says "Edit this property in the text".
- If a property appears twice, the pane edits the last one, which is the one the build keeps.

Every change from the pane is one change in the editor, so `Ctrl+Z` undoes it. If the frontmatter has an error, the pane shows the reason and disables its inputs until you fix the text.

## Complete and check in the text {#text}

Inside the frontmatter, the editor completes property names at the start of a line and values after the colon. Typing a new name or value is always allowed.

The gutter on the left marks lines with problems. Hover over a mark to read it. Errors and warnings are what `kb4it verify` would report; see the [list of checks](reference-theme-techdoc.md#lint).

!!! note "The editor is not the build"
    The check can miss some malformed nested values, for example `A:` followed by `  b: [x`. Run `kb4it build` or `kb4it verify` after you add the file.

## Use the toolbar {#toolbar}

The toolbar inserts Markdown and KB4IT elements. With text selected, a button wraps it; without a selection, it inserts a template and selects the text to replace. One click is one undo step.

| Shortcut | Action |
|---|---|
| `Ctrl+B` | Bold |
| `Ctrl+I` | Italic |
| `Ctrl+E` | Inline code |
| `Ctrl+K` | Link |
| `Tab` / `Shift+Tab` | Indent / outdent (four spaces; on a selection, every selected line) |
| `Escape`, then `Tab` | Leave the editor, to reach the next control |

The buttons and shortcuts are disabled while the cursor is in the frontmatter. `Escape` inside the editor does not close the dialog.

## Save the file {#save}

- **Chrome, Edge and other Chromium browsers:** **Save** opens the system save dialog. After the first save the button reads **Save (name.md)** and writes the same file without asking.
- **Firefox and Safari:** **Save** downloads the file. Move it from your downloads folder.
- If you cancel the dialog or the write fails, the page offers to download the file instead.
- If the document has errors, the page asks you to confirm first.

The file is UTF-8 with LF line endings and one final newline. Nothing else is changed in your text.

**Copy** puts the same text on the clipboard.

Put the file in the `source/` folder of your repository, then run `kb4it build`. The file name becomes the page name, so use short names without spaces.
