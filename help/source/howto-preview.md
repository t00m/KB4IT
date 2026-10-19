---
DocType: How-to guide
Feature: Building
HelpId: preview
Keyword: serve, preview, live reload, watch, port, browser, localhost
Level: basic
Order: 315
Related: howto-build.md, reference-command-line.md
Section: Build and preview
Summary: See your changes in the browser while you write, with kb4it serve.
---

# Preview while you write

`kb4it serve` builds the site, serves it on this computer and rebuilds it every time you save a document. Open pages reload by themselves.

## Start the preview {#start}

```bash
kb4it serve ~/mykb/config/repo.json
```

It prints the address, for example `Serving /home/me/mykb/target at http://127.0.0.1:8642/`. Open it in your browser, or add `--open` to let KB4IT open it.

Edit and save a document. About a second later the build runs again and the page reloads. Press `Ctrl+C` in the terminal to stop.

## What triggers a rebuild {#watch}

| Change | Rebuild |
|---|---|
| A document or a file under `source/` | Only what changed, as with `kb4it build` |
| `repo.json` | Everything |
| Your own theme (in `~/.kb4it` or set with `theme_path`) | Everything |

Changes to a bundled theme come with a new KB4IT version, so they are not watched.

## When a build fails {#errors}

The site you see stays as it was, and a red bar at the top of the page shows the first error. Fix the document and save; the bar goes away after the next good build. The terminal shows the full log.

## Options {#options}

| Option | Effect |
|---|---|
| `--port 9000` | First port to try. When it is busy, the next free one is used |
| `--host 0.0.0.0` | Let other computers on your network see the preview. Anyone who can reach the address can read the site |
| `--open` | Open the site in your browser |
| `--no-watch` | Serve only; do not rebuild |
| `--no-reload` | Rebuild, but do not reload pages in the browser |
| `--interval 2` | Check for changes every 2 seconds instead of every second |
| `--force` | Rebuild everything in the first build |

!!! note
    The reload script is added to the pages as they are sent to the browser. The files in `target/` never contain it, so you can publish them as they are.

!!! tip
    While `kb4it serve` runs, a `kb4it build` of the same knowledge base stops with `KB4IT is already working on this repository`. Stop the preview first, or let it do the building.
