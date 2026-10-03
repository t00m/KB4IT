---
DocType: Reference
Feature: Themes, Configuration
HelpId: apphelp
Keyword: help, application, help id, go.html, embed, contract, offline search, doctype, layout, faq, tips, troubleshooting
Level: advanced
Order: 550
Section: Themes
Summary: The apphelp theme for application help sites, its page properties, help ids and settings.
---

# apphelp

apphelp builds the help of an application, like the site you are reading. The same files work opened from disk, on a web server under any path such as GitHub Pages, and inside the application.

![The apphelp sample site](resources/images/apphelp.webp)

## What you get {#features}

- A sidebar of sections, built from the pages' `Section` and `Order`.
- Search that runs in the browser, with filters, and needs no server.
- A **Topics** page listing pages by feature.
- Help ids: the application opens `go.html?id=rename` and lands on the right page or section.
- `?embed=1` hides the header and sidebar, for a help viewer inside the application.
- Strict checks: a page with a missing or unknown property fails the build, so the help never ships half written.

## Page properties {#properties}

| Key | Required | Meaning |
|---|---|---|
| `DocType` | yes | `Tutorial`, `How-to guide`, `Reference` or `Explanation`; a page without it is left out |
| `Section` | yes | Sidebar group |
| `Order` | yes | Position in the section; sections follow their lowest `Order` |
| `Summary` | yes | One sentence, at most 160 characters, for search results and lists |
| `Feature` | yes | One or more values from the `Feature` vocabulary |
| `Layout` | no | `faq`, `tips` or `troubleshooting`, see below |
| `HelpId` | no | Ids the application opens with `go.html?id=<id>` |
| `Keyword` | no | Words readers search for that the text does not use |
| `Level` | no | From the `Level` vocabulary |
| `Since` | no | Version that introduced the feature; pages for the current version are listed as new |
| `Related` | no | Pages listed first under **Related pages** |

`index.md` is the home page and needs none of them. `search.md`, `topics.md`, `go.md` and `404.md` are reserved.

## Layouts {#layouts}

| `Layout` | Each `##` heading becomes |
|---|---|
| `faq` | A question that opens on click |
| `tips` | A card |
| `troubleshooting` | A problem, with `### Cause` and `### Fix` styled |

Tutorials number their `##` steps by themselves.

## Settings {#settings}

The `apphelp` block of `repo.json`:

```json
"apphelp": {
    "strict": true,
    "lang": "en",
    "accent": "#0f766e",
    "about": false,
    "contract": "config/contract.txt",
    "vocabulary": {
        "Feature": ["Getting started", "Documents", "Settings"],
        "Level": ["basic", "advanced"]
    }
}
```

| Key | Meaning |
|---|---|
| `strict` | `true` by default: metadata problems and help ids pointing nowhere fail the build |
| `lang` | Language of the pages |
| `accent` | Accent colour |
| `about` | `true` adds an about page |
| `contract` | A file listing, one per line, the help ids and anchors the application opens; a missing one fails the build |
| `vocabulary` | Allowed values per property |
| `labels` | Your own texts for the interface |

Edit links use `"git": true` and `git_server` without `https://`, for example `github.com`.

## Start a help site {#start}

```bash
kb4it create apphelp myapp/help
```

The sample shows every page type. Use `kb4it verify myapp/help/config/repo.json` while writing: it reports every page that breaks a rule. The help of [MiAZ](https://t00m.github.io/MiAZ/) and this site are built with apphelp; their sources are good examples.
