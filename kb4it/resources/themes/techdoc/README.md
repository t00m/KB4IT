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
| `Category` | The form of the document: `Procedure`, `Note`, `Report`, `Template`, `Post`, `Record` or `Minutes` |
| `WorkType` | The type of work a record holds: `Change`, `Incident`, `Task` or `Meeting`. Drives the latest changes and incidents, **Open items** and the calendar |
| `Date` | Dates the document; it appears in the calendar when its `WorkType` (or, without one, its `Category`) is listed in `events` |
| `DocType` | `Tutorial`, `How-to guide`, `Reference` or `Explanation`; fills the dashboard cards and the quality score |
| `Status` | `Draft` shows a draft banner; `Obsolete`, `Deprecated`, `Withdrawn` and `Rejected` mark the document as retired |
| `Summary` | One line shown under the title |

A change, incident or task record has `Category: Record`; meeting notes have `Category: Minutes`. Every other property is optional. Add `Tag`, `Topic`, `Scope`, `Priority` and the rest when you need them.

## Optional keys

These keys are optional. Add one to `repo.json` only to change it.

| Key | Without it | Effect of setting it |
| --- | --- | --- |
| `datatable` | Columns `Date` and `Title` | Sets the columns of the document table |
| `events` | No calendar | Lists the work types (or, for older documents, categories) that appear in the calendar, for example `["Incident", "Meeting"]` |
| `editor` | `true` | `false` removes the Add page (`add.html`) and the link to it. The cards come from `templates/skeletons/skeletons.json` |
| `admin` | `false` | `true` builds the admin pages after deploy |
| `quality` | `true` | `false` turns off the quality score of every document |

The navigation menu is built from the properties your documents use. It is not set in `repo.json`.

## Sample apps

`kb4it create techdoc <path>` starts from the `default` app; `kb4it create techdoc sapbasis <path>` from `sapbasis`. Every sample uses the sections of its skeleton on the Add page, so each one is also a model of a well-scored document. Names, hosts and system ids in them are made up.

| App | Samples |
|---|---|
| `default` | A daily backup check (procedure), a disk full incident, the change that followed it, the weekly operations meeting, an open certificate renewal task, a note on RAID levels and a draft capacity report |
| `sapbasis` | Checking failed background jobs (`SM37`), analysing a short dump (`ST22`), a memory dump incident in a nightly job, a planned kernel update and a note on the transport landscape (`STMS`). The menu adds SAP properties such as `SID`, `Transaction`, `Job` and `Dump` |

Copy a sample to start a new document, or delete the samples once you have your own.

See [reference-repo-json.md](../../../../help/source/reference-repo-json.md) for every key.
