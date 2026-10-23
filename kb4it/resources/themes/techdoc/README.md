# Techdoc theme

Techdoc builds a site for technical documents: runbooks, changes, incidents, meetings and notes. Create a site with `kb4it create techdoc <path>`.

## Minimum core

A new `config/repo.json` needs these four keys:

```json
{
    "source": "source",
    "target": "target",
    "theme": "techdoc",
    "title": "My Knowledge Base"
}
```

| Key | Meaning |
| --- | --- |
| `source` | Folder with your Markdown documents |
| `target` | Folder where the site is written |
| `theme` | Must be `techdoc` |
| `title` | Site name, shown in the header and the browser tab |

Tested: a folder with these four keys and one valid document builds.

## Document properties

Techdoc uses these properties from each document:

| Property | Used for |
| --- | --- |
| `Category` | Groups the document; `Change`, `Incident`, `Meeting`, `Note`, `Post`, `Procedure`, `Report` and `Task` appear in the calendar |
| `Date` | Dates the document; it appears in the calendar when its `Category` is listed in `events` |
| `DocType` | Fills the dashboard cards |

Every other property is optional. Add `Tag`, `Topic`, `Scope`, `Status` and the rest when you need them.

## Optional keys

These keys are optional. Add one to `repo.json` only to change it.

| Key | Without it | Effect of setting it |
| --- | --- | --- |
| `datatable` | Columns `Date` and `Title` | Sets the columns of the document table |
| `events` | No calendar | Lists the `Category` values that appear in the calendar, for example `["Incident", "Meeting"]` |
| `editor` | `true` | `false` removes the Add page (`add.html`) and the link to it. The cards come from `templates/skeletons/skeletons.json` |
| `admin` | `false` | `true` builds the admin pages after deploy |

The navigation menu is built from the properties your documents use. It is not set in `repo.json`.

See [reference-repo-json.md](../../../../help/source/reference-repo-json.md) for every key.
