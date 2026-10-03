---
DocType: How-to guide
Feature: Development
HelpId: dev-help
Keyword: documentation, help pages, apphelp, github pages, workflow
Level: advanced
Order: 740
Section: Development
Summary: Add or change a page of this help, check it locally and get it published.
---

# Write these pages

This help is a KB4IT knowledge base in the `help/` folder of the repository, built with the [apphelp theme](reference-theme-apphelp.md).

```text
help/
├── config/repo.json          # apphelp settings and the Feature vocabulary
└── source/
    ├── index.md              # the home page
    ├── getting-started.md    # one file per page
    └── resources/images/     # screenshots and the logo
```

## Write for the reader {#style}

- Start from what the reader wants to do, not from how the code is organised.
- One page, one goal. Give it a `DocType`: a tutorial teaches, a how-to guide solves one problem, a reference lists facts, an explanation gives the why.
- Short sentences and plain words. Show the command, then what it prints.
- Check every command and every claim against the code before you publish it.

## Add a page {#add}

1. Copy a page of the same type and rename it: `howto-…`, `reference-…`, `explanation-…`, `dev-…`.
2. Set its properties: `DocType`, `Section`, `Order`, `Summary`, `Feature` and, if useful, `HelpId`, `Keyword` and `Related`.
3. Add it to the home page in `index.md` if readers should find it there.

`Feature` and `Level` values must be in the vocabulary of `help/config/repo.json`; add a value there before you use it.

## Check it {#check}

```bash
kb4it verify help/config/repo.json
kb4it build help/config/repo.json
xdg-open help/target/index.html
```

The help is strict: a missing property, an unknown value or a help id that points nowhere stops the build. Broken links are reported as warnings; fix them too.

## Screenshots {#screenshots}

Keep them in `help/source/resources/images/` as WebP, 1280 pixels wide or less. Use sample data, never real names or paths from your computer.

## Publish {#publish}

`.github/workflows/help.yml` builds the help with the KB4IT of the same commit on every push that touches `help/` or the code, and publishes it to GitHub Pages from `master`. On other branches it only builds, so a broken page fails the pull request instead of the site.
