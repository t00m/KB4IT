# First run: a new knowledge base that explains itself

Status: draft, waiting for approval.
Date: 2026-10-20
Scope: KB4IT 0.9.x. Themes techdoc, blog, bookshelf, apphelp. The `kb4it create` command and the TUI create screen.

## Intent

A person runs `kb4it create` for the first time. Right now they get an empty site, a few log lines, and no idea what to do next. They ask: where do my documents go, why is the site empty, and what is safe to delete?

After this work, a new knowledge base shows a real site on the first build. Sample documents show what good documents look like. Two or three plain lines after `create` say what to do next.

## Goals

1. A new techdoc, blog or bookshelf knowledge base builds to a site with real content.
2. Each sample document shows its theme's properties, and explains them in the text.
3. `kb4it create` ends with three plain next steps, not log lines.
4. The stray `EMPTY` file no longer reaches `source/` or `target/`.
5. The tutorial starts from the samples and no longer says "GNU/Linux only".
6. Each theme's minimum core is documented. This is done (see the theme READMEs).

## Non-goals

- Clearer `kb4it verify` messages. Second spec.
- A build warning when documents are left out. Second spec.
- The common property set across themes. Second spec.
- `kb4it serve` opening the saved page. Second spec.
- Changing how themes read `repo.json`. Done in part: blog no longer needs `tagline`.

## Anti-goals

- The samples must not look like a template with filler. A reader should be able to use one as a real starting point.
- The next steps must not repeat the whole help site. Three lines.
- A user must not lose their own documents. Nothing is deleted on their behalf.

## Current state

- `kb4it create techdoc` copies `apps/default/` into the new folder. The `source/` folder holds only an `EMPTY` file. The `EMPTY` file is also copied to `target/`.
- `blog` has the same `EMPTY` file.
- `bookshelf` has no documents in `source/`.
- `apphelp` has 10 sample pages and works already. It is the reference for the other three.
- After `create`, the log shows `HINT` lines for the bin script, `source/`, `target/`, `config/repo.json`, and `kb4it -h` (`kb4it/services/workflow.py`, around lines 349 to 354).
- The TUI create screen (`kb4it/tui/screens/create.py`) is not checked yet. Open question 2.

## Design

### 1. Sample documents

Each theme's `apps/default/source/` gets sample documents:

| Theme | Samples | What each one shows |
| --- | --- | --- |
| techdoc | One procedure (runbook), one incident | `Category`, `Date`, `DocType`, `Tag`, `Scope`, `Status` |
| blog | One post, one note | `Date`, `Category`, `Tag`, `Topic` |
| bookshelf | One chapter with its book and part | `Book`, `Part`, `Chapter` |

Rules:

- Each sample is real content: a short procedure, a short post. It is not "Lorem ipsum".
- Each sample has a short paragraph near the top that explains which properties it uses and what they do on the site. The paragraph says the sample can be copied and deleted.
- The `EMPTY` files are removed.
- Samples follow the rules in the theme README (`kb4it/resources/themes/<theme>/README.md`).
- apphelp is unchanged.

Decision (my call): the samples are English, because the bundled help is English.

### 2. Next steps after `create`

`create` prints three lines after the workflow ends. They replace the `HINT` log lines:

```text
Your knowledge base is ready at ~/mykb.
Write documents in ~/mykb/source/ and copy or delete the samples there.
Preview the site with: kb4it serve ~/mykb/config/repo.json
```

The text does not mention `bin/compile.sh`. The path to `config/repo.json` is always printed.

Decision (my call): plain `print`, not log lines, so the output is clear even when the log level is set to `ERROR`.

### 3. Clean folders

- Remove `apps/*/source/EMPTY` where the folder now has samples.
- `create` copies only what the theme ships. No `EMPTY` file reaches `source/` or `target/`. `source/` and `target/` are still created as empty folders.

### 4. Tutorial

`help/source/getting-started.md`:

- Line 14: drop "You need a GNU/Linux computer". Say "You need Python 3.11 or newer on Linux, macOS or Windows".
- Line 23: the example version is `0.8.0`. Use the version from the current release, or write "for example `KB4IT 0.9.1`" and keep it in sync with the release steps.
- Start the tutorial from the samples: "Your new knowledge base already has sample documents. Build it, then open one."

### 5. Minimum `repo.json`

Done. Each theme's README lists the minimum keys. The `create` command still writes the full sample `repo.json`. Changing that output is an open question (question 3).

## Acceptance checks

1. `kb4it create techdoc <path>`, then `kb4it build <path>/config/repo.json`: exit 0, and the site has at least two documents in the list.
2. Same for `blog` and `bookshelf`.
3. `kb4it create apphelp <path>`: unchanged.
4. The output of `create` has the three lines above and no `HINT` lines.
5. No `EMPTY` file exists under `source/` or `target/` after `create`.
6. `help/source/getting-started.md` has no GNU/Linux-only line.
7. Tests in `tests/themes` and `tests/blog` pass on the working tree.
8. The working tree is tested with `PYTHONPATH` set to the repo root, not the installed tool.

## Open questions

These need your answer. They change what gets built.

1. Should the samples say "delete me" in their text, or only explain the properties? My default: explain the properties and say they can be copied and deleted, without a "delete me" banner.
2. Does the TUI create screen also show the next steps? My default: yes, the same three lines in its status area.
3. Should `create` write the full sample `repo.json` as it does now, or the minimum keys with the rest commented out? My default: keep the full file, because the minimum file has no comments.

## What is left to the builder

- The exact sample text. It follows the style rules and the theme README.
- The exact wording of the three `create` lines, within the length above.
- Where the tests go. Put them next to the existing theme tests.
