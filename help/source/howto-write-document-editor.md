---
DocType: How-to guide
Feature: Writing
HelpId: editor
Keyword: editor, add page, edit document, skeletons, skeletons.json, repo.json, markdown, frontmatter, properties, toolbar, save, completion
Level: basic
Order: 215
Related: howto-write-documents.md, reference-repo-json.md, reference-theme-techdoc.md, howto-customize-templates.md
Section: Guides
Summary: Turn on the Add page, write a new document or edit an existing one in its editor, use your own skeletons and save the file into the source folder.
---

# Write a document in the editor

The Add page (`add.html`) is a Markdown editor that knows your repository. It suggests the properties and values you already use, warns about mistakes the build would report, and saves the file for you. It works offline, also from `file://`.

Every bundled theme can have it: [techdoc](reference-theme-techdoc.md), [blog](reference-theme-blog.md), [bookshelf](reference-theme-bookshelf.md) and [apphelp](reference-theme-apphelp.md). It is on by default in techdoc and off in the others.

## Turn it on {#enable}

Set `editor` in `repo.json`:

```json
{
    "editor": true
}
```

- `true` builds the Add page and links to it from the site.
- `false` removes `add.html` and the link. Use it to take the page out of a techdoc site.
- Without the key, the theme decides: techdoc on; blog, bookshelf and apphelp off.
- Any other value stops the build with `repo.json 'editor' must be true or false`.

The link is in the header menu of techdoc, the footer of blog, a plus button in the header of bookshelf and the sidebar of apphelp ("Add a page", a translatable label).

With the editor on, a source document named `add.md` is reserved: it is left out and logged as `DOC_NAME_RESERVED`, and `kb4it verify` lists it as `reserved_name`. With the editor off, `add.md` is a normal name. See [repo.json](reference-repo-json.md#optional).

## Create the document {#create}

1. Open `add.html` and click **Create** on a card. The editor opens in a dialog with the skeleton of that card.
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
- A property written as a block list, over several lines or with an anchor is read-only in the pane. It says "Edit this property in the text".
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

A **Person profile** names its file from the start: the dialog title and the button read `person-<name>.md`, such as **Save (person-jane-doe.md)**, and follow the `Person` value as you edit it. Save it in `source/` and rebuild: the person's page then shows the profile. Any file name works, as long as the file has the `Person` property.

## Edit an existing document {#edit}

In techdoc, every document page has an **Edit in the editor** button in the title menu (hover over the title), and an **Edit in the editor** link in the History tab of the info card. Both open the Add page with the document's Markdown in an **Edit** dialog, with the same toolbar, checks and properties pane. The cursor starts below the title.

**Save** suggests the document's own file name, such as `backup-check.md`: save it over the file in the `source/` folder (in Firefox and Safari, move the download there), then run `kb4it build`. Closing with unsaved changes asks first, as for a new document.

The text travels in the address of the Add page, so it works from `file://`, from `kb4it serve` and from any web server, with no network and nothing stored in the browser. The address is cleared as soon as the dialog opens, so reloading the page does not open the document again. The editor shows the source the site was built from: if you changed the file since the last build, rebuild first or edit the file itself.

The button needs the editor (`"editor": true`, the default in techdoc). With `"git": true`, the **Edit** button that opens the file on your git server stays next to it.

## Use your own skeletons {#skeletons}

The page shows one card per skeleton. KB4IT takes the skeletons from the first of these folders that holds at least one `*-SKELETON.md` file:

1. `overrides/templates/skeletons/` in your repository.
2. `templates/skeletons/` of the theme.
3. The common set of KB4IT, with one generic `DOCUMENT` skeleton.

The sets are never merged: a folder of yours replaces the theme's skeletons completely. The file `TASK-SKELETON.md` makes the card `TASK`.

To choose the names, the order and the look of the cards, add a `skeletons.json` next to the files. It is a list; the order of the list is the order of the cards:

```json
[
    {"id": "task", "name": "Task", "description": "Something to do, with an owner and a due date", "color": "#1e87f0", "icon": "check"},
    {"id": "note", "name": "Note", "description": "A short note"}
]
```

| Field | Meaning |
|---|---|
| `id` | Required. Lowercase letters, digits and hyphens, starting with a letter (`^[a-z][a-z0-9-]*$`). It matches the file `<ID>-SKELETON.md`, in capitals |
| `name` | The title of the card |
| `description` | A line under the title |
| `color` | A CSS colour for the card, such as `#1e87f0` |
| `icon` | The icon of the card; only techdoc shows it |

An error in the file stops the build and names the file. A skeleton file that is not listed is ignored, and the build logs `[BUILDER] SKELETON_UNLISTED`. Without a `skeletons.json`, the id comes from the file name, the name is the id capitalised and the cards are sorted by id.

In techdoc, a skeleton is also the standard the [quality score](reference-theme-techdoc.md#quality) checks: a document is expected to have the `##` sections of the skeleton of its Category (records: of their WorkType), and an example line left unchanged costs points. A References, Documentation or Related section counts once, under Connected. Give your own skeletons a first section that gives context (Introduction, Description or Overview) and a References section.

In apphelp, completion also offers the values of the `vocabulary` lists in `repo.json`, the `DocType` names and the `Layout` names, even before a document uses them.

To change the page itself, see [Change one template of a theme](howto-customize-templates.md#editor).
