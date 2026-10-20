# Blog theme

The blog theme builds a site of dated posts with an index, a timeline and tags. Create a site with `kb4it create blog <path>`.

## Minimum core

A new `config/repo.json` needs these four keys:

```json
{
    "source": "source",
    "target": "target",
    "theme": "blog",
    "title": "My Blog"
}
```

| Key | Meaning |
| --- | --- |
| `source` | Folder with your Markdown documents |
| `target` | Folder where the site is written |
| `theme` | Must be `blog` |
| `title` | Blog name, shown in the header and the browser tab |

Tested on the working tree: these four keys and one valid document build with exit code 0.

## Document properties

The blog reads these properties from each document:

| Property | Used for |
| --- | --- |
| `Date` | Orders the posts and places them in the archive |
| `Category` | With `strict` on, only `Category: Post` documents are shown as posts |

Every other property is optional.

## Optional keys

These keys are optional. Add one to `repo.json` only to change it.

| Key | Without it | Effect of setting it |
| --- | --- | --- |
| `index_posts` | `10` | Number of posts on the home page |
| `strict` | `false` | `true` uses the post layout only for `Category: Post` documents |
| `tagline` | Empty footer line | Text shown in the footer |

See [reference-theme-blog.md](../../../../help/source/reference-theme-blog.md) for the full theme reference.
