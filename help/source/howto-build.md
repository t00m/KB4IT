---
DocType: How-to guide
Feature: Building
HelpId: build
Keyword: compile, force, rebuild, verify, log, summary, workers
Level: basic
Order: 310
Related: howto-use-tui.md, troubleshooting.md
Section: Build and preview
Summary: Build a website, rebuild only what changed, force a full rebuild, check documents and read the build log.
---

# Build and rebuild a website

## Build {#build}

Point `kb4it build` at the settings file of the knowledge base:

```bash
kb4it build ~/mykb/config/repo.json
```

Or run the script `kb4it create` made for you: `~/mykb/bin/compile.sh`.

The website is written to the `target/` folder. Open `target/index.html` in a browser, or see [Publish on any web server](howto-publish-web-server.md) to share it.

## Read the summary {#summary}

Every build ends with a summary line:

```text
[WORKFLOW] SUMMARY docs_total=120 compiled=3 skipped=116 invalid=1 keys_compiled=2 kv_pages_compiled=5
```

| Field | Meaning |
|---|---|
| `docs_total` | Documents found in `source/` |
| `compiled` | Documents converted in this build |
| `skipped` | Unchanged documents reused from the last build |
| `invalid` | Documents KB4IT could not read; [why](reference-document-format.md#invalid) |
| `keys_compiled`, `kv_pages_compiled` | Property pages refreshed |

## Rebuild after a change {#rebuild}

Run the same command again. KB4IT compares every document with the last build and compiles only the ones you changed, added or removed, plus the property pages they appear on.

## Rebuild everything {#force}

```bash
kb4it build --force ~/mykb/config/repo.json
```

Use it after you change a template of your own theme, or when the site looks out of date. `--force` deletes KB4IT's cache in `var/`; it never touches `source/` or `target/`.

## Check documents without building {#verify}

```bash
kb4it verify ~/mykb/config/repo.json
```

It reads every document and lists those KB4IT cannot use, with the reason. Some themes add their own checks here; apphelp, for example, checks its required properties. The command exits with status 1 when it finds a problem, so you can run it in CI or in a git hook.

## See more detail {#debug}

```bash
kb4it -L DEBUG build ~/mykb/config/repo.json
```

`-L` takes `DEBUG`, `INFO` (the default), `WARNING` or `ERROR`. Whatever you choose on screen, the full log of the last build is in `var/log/kb4it.log` inside the knowledge base, and the one before it in `kb4it.log.old`.

## Make large builds faster {#workers}

KB4IT converts several documents at a time, by default half the number of processor cores. Change it with `"workers"` in `repo.json`. Use fewer workers if the computer runs short of memory.

!!! note
    Only one KB4IT runs at a time. A second one stops with `KB4IT is already running (PID 1234)`.
