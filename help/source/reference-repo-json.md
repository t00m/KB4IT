---
DocType: Reference
Feature: Configuration
HelpId: repo-json
Keyword: settings, config, repo.json, title, theme, source, target, workers, ignored_keys, publish_sources, fail_on_invalid, theme_path, force
Level: basic
Order: 620
Section: Reference
Summary: Every setting of config/repo.json shared by all themes, with its default.
---

# Repository settings

Each knowledge base has its settings in `config/repo.json`. `kb4it create` writes a complete one for the theme you chose.

```json
{
    "title": "Ops Knowledge Base",
    "tagline": "Runbooks, incidents and changes",
    "theme": "techdoc",
    "source": "source",
    "target": "target"
}
```

## Required {#required}

| Key | Meaning |
|---|---|
| `title` | Name of the site, shown in the header and the browser tab |
| `theme` | Theme name, see [Themes](explanation-themes.md) |
| `source` | Folder with the documents |
| `target` | Folder where the website is written |

A missing key stops the build with `CONFIG_KEY_MISSING key=...`.

`source` and `target` are relative to the knowledge base folder, the one that holds `config/`. Absolute paths, `~` and `$VARIABLES` also work.

## Optional {#optional}

| Key | Default | Meaning |
|---|---|---|
| `tagline` | | Short subtitle |
| `logo`, `logo_alt` | theme logo | Logo image, relative to the website, and its text |
| `workers` | half the processor cores | Documents converted at the same time |
| `force` | `false` | Rebuild everything on every build, like `--force` |
| `ignored_keys` | `[]` | Properties that get no pages; see [properties](explanation-properties.md#excluded) |
| `publish_sources` | `true` | Copy the `.md` files to the website, in `target/sources/` |
| `fail_on_invalid` | `false` | Stop the build when a document cannot be read |
| `theme_path` | | Use the theme in this folder instead of searching by name |
| `git`, `git_server`, `git_user`, `git_repo`, `git_branch`, `git_path` | `false` | Edit links to your git server; see each theme for the format |

## Theme settings {#theme}

Each theme reads its own keys as well:

- [techdoc](reference-theme-techdoc.md#settings): `datatable`, `events`, `admin`
- [blog](reference-theme-blog.md#settings): `index_posts`, `strict`, `datatable`
- [bookshelf](reference-theme-bookshelf.md#settings): `datatable`
- [apphelp](reference-theme-apphelp.md#settings): the `apphelp` block

Sample apps from older versions also contain `menu`, `sort`, `timeline` and `webserver`. KB4IT no longer reads them; you can leave them or delete them.
