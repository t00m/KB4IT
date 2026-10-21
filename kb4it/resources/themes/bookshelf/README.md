# Bookshelf theme

The bookshelf theme builds a study library. It arranges your notes as books, parts and chapters on a shelf. Create a site with `kb4it create bookshelf <path>`.

## Minimum core

A new `config/repo.json` needs these four keys:

```json
{
    "source": "source",
    "target": "target",
    "theme": "bookshelf",
    "title": "My Study Library"
}
```

| Key | Meaning |
| --- | --- |
| `source` | Folder with your Markdown documents |
| `target` | Folder where the site is written |
| `theme` | Must be `bookshelf` |
| `title` | Library name, shown in the header and the browser tab |

Tested: these four keys and one plain document build with exit code 0.

## Document properties

Bookshelf places each document with these properties:

| Property | Used for |
| --- | --- |
| `Book` | The book the note belongs to |
| `Part` | The part of the book |
| `Chapter` | The chapter of the part |

Documents without these properties still build, but they may show up in the wrong place or not at all. Set them for every note you want on the shelf.

## Optional keys

These keys are optional. Add one to `repo.json` only to change it.

| Key | Without it | Effect of setting it |
| --- | --- | --- |
| `tagline` | No tagline | Short site description |

The bundled `default` app has no sample documents. Your first `kb4it build` produces an empty library until you add documents.

See [reference-theme-bookshelf.md](../../../../help/source/reference-theme-bookshelf.md) for the full theme reference.
