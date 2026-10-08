---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-08
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Draft
Tag: specification, roadmap, cross-platform
Topic: Architecture, Documentation
---

# KB4IT 0.9 specification: cross-platform support and roadmap

## Overview

This specification defines every change planned for KB4IT 0.9.0. It covers two goals:

1. Run KB4IT natively on GNU/Linux, macOS and Windows.
2. Close the gaps found in the comparison report `responses/KB4IT-SSG-COMPARISON.md`: live preview, configurable Markdown, full-text search, feeds and SEO metadata, template overrides, build hooks, backlinks and versioned help.

The base is release 0.8.0 (commit `d026df3`). Every change keeps existing repositories working without edits: all new `repo.json` keys are optional, and the default output only changes where this document says so (section "Compatibility").

Each requirement has an ID (`CP-02`, `SV-01`, ...). The implementation plan, the commits and the CHANGELOG entries will refer to these IDs.

### Delivery

- The code is delivered as a zip with a `git am` patch series (one `.patch` file per commit, made with `git format-patch`) and a `README-APPLY.md`.
- Apply with `git am --3way *.patch` on a branch created from `d026df3`.
- Every commit passes the test suite on its own, so the series can be bisected or partly applied.
- Commit messages follow the repository rules: one line, Conventional Commits, no trailers.

### Phases

| Phase | Name | IDs | Depends on |
|---|---|---|---|
| 0 | Foundation fixes | FX-01 to FX-03 | none |
| 1 | Cross-platform support | CP-01 to CP-10 | 0 |
| 2 | Live preview | SV-01, SV-02 | 0, 1 |
| 3 | Markdown pipeline | MD-01 to MD-03 | 0 |
| 4 | Full-text search | SR-01 to SR-03 | 0 |
| 5 | Publishing metadata | PB-01 to PB-04 | 0 |
| 6 | Customization and extension | CU-01, CU-02 | 0, 3 |
| 7 | Backlinks and link checks | KG-01, KG-02 | 0 |
| 8 | Versioned help (apphelp) | VH-01 to VH-03 | 5 |
| 9 | Documentation and packaging | DOC-01 to DOC-05 | all |

### Non-goals for 0.9

- Multilingual sites (i18n). Large change to the data model; planned separately.
- Built-in Mermaid diagrams and math rendering. They need large JavaScript bundles in every theme. Users can enable them with MD-01 (extensions) plus CU-01 (template overrides); the help site will show how.
- Image processing, minification, fingerprinted assets.
- Native packages (deb, rpm, Homebrew, winget). Installation stays `uv tool install KB4IT` or `pipx install KB4IT`.
- A plugin marketplace or plugin packaging format. CU-02 hooks are per repository.

## Conventions for all changes

- **Logging**: every new event uses `[<COMPONENT>] EVENT key=value`. New components: `[LOCK]`, `[SERVE]`, `[WATCH]`, `[SEARCH]`, `[FEED]`, `[SITEMAP]`, `[HOOKS]`, `[LINKS]`, `[VERSIONS]`.
- **Errors**: services raise `ConfigError`, `ThemeError`, `CompilationError` or `KB4ITError`; they never call `app.stop()`.
- **Stages**: any new stage method is decorated with `@timeit`.
- **Text files**: every text read or write in `kb4it/` names `encoding="utf-8"` (FX-02).
- **Paths**: built with `os.path.join` or `pathlib`, never by string concatenation with `/`. URLs in generated HTML always use `/`.
- **Tests**: every requirement has at least one pytest test. Tests that only make sense on one OS are marked with `pytest.mark.skipif`.
- **Docs**: each user-visible change updates the matching page in `help/source/`, `AGENTS.md`, `README.md` where relevant, and `CHANGELOG.md` under `## [Unreleased]`.

## Phase 0: Foundation fixes

### FX-01 Reset template caches for each build

**Problem.** `Builder.templates` and `Builder._xform_pairs` are class attributes. A second build in the same process (the TUI today, `kb4it serve` in SV-01) reuses templates loaded for the first build. Editing a template, or building two projects with different themes in one TUI session, can render stale or wrong templates. The theme logic module is already reloaded (`tests/core/test_theme_reload.py`); templates are not.

**Requirement.**

- The template cache and the transformation pairs belong to the build, not to the class. They are cleared when a `KB4IT` instance starts a build.
- A template file changed between two builds in the same process is rendered with its new content.
- `[BUILDER] CACHE_RESET` is logged at debug level when the caches are cleared.

**Acceptance.** A test builds twice in one process, changing `HTML_BODY.tpl` between builds, and finds the new content in the second output. A second test builds two repositories with two themes that share a template name and checks each output uses its own theme's template.

### FX-02 Explicit UTF-8 for all text I/O

**Problem.** Ten `open()` calls in the techdoc, blog and bookshelf themes have no `encoding`. On Windows, and on Linux with a non-UTF-8 locale, documents with non-ASCII text ("Tomás") fail or are written in the wrong encoding.

**Requirement.**

- Every text-mode `open()`, `Path.read_text()` and `Path.write_text()` under `kb4it/` passes `encoding="utf-8"`.
- A test parses every `.py` file under `kb4it/` with `ast` and fails when a text-mode `open()` or `read_text()`/`write_text()` call has no `encoding` argument. This keeps the rule from regressing.

**Acceptance.** The AST test passes. A build of a repository with accented titles under `PYTHONIOENCODING=latin-1 LC_ALL=C` produces correct UTF-8 HTML.

### FX-03 Stale dependency lists

**Problem.** `requirements.txt` lacks `PyYAML` and `Markdown`. `pixi.toml` only lists `linux-64`.

**Requirement.**

- `requirements.txt` matches the runtime dependencies in `pyproject.toml`, including any added in this release (MD-02 adds `Pygments`).
- `pixi.toml` lists `linux-64`, `osx-64`, `osx-arm64` and `win-64`.
- A test compares `requirements.txt` with `[tool.poetry.dependencies]` and fails when they differ.

## Phase 1: Cross-platform support

Target platforms: GNU/Linux (x86_64, aarch64), macOS 13 or later (Intel and Apple silicon), Windows 10 and 11 (x64). Python 3.11 to 3.13 on each.

### CP-01 Platform detection without hard exit

**Problem.** `kb4it/core/env.py:77` calls `platform.freedesktop_os_release()`, and when it fails prints "KB4IT only runs in GNU/Linux systems" and exits.

**Requirement.**

- New helper `platform_description()` in `kb4it/core/util.py` (or `env.py`): on systems with an os-release file it returns `PRETTY_NAME`; otherwise it returns `platform.platform()`. It never raises and never exits.
- `ENV["SYS"]["PLATFORM"]["OS"]` holds that value. A new `ENV["SYS"]["PLATFORM"]["FAMILY"]` holds `linux`, `darwin`, `windows` or `other` (from `sys.platform`).
- The "only runs in GNU/Linux" message and exit are removed.

**Acceptance.** Unit tests monkeypatch `platform.freedesktop_os_release` to raise `OSError` and check the fallback. CI (CP-09) runs `kb4it --version` on all three OSes.

### CP-02 Cross-platform process lock, scoped to the repository

**Problem.** `kb4it/core/main.py` imports `fcntl`, which does not exist on Windows, so KB4IT crashes at import. The lock is also global per user: two different repositories cannot build at the same time, and the TUI cannot build while a terminal build runs elsewhere.

**Requirement.**

- New module `kb4it/core/lock.py` with a `FileLock` class:
  - POSIX: `fcntl.flock(LOCK_EX | LOCK_NB)`.
  - Windows: `msvcrt.locking(LK_NBLCK, 1)` on byte 0 of the lock file.
  - Context manager; writes the holder's PID into the file; raises `LockBusyError(pid)` when the lock is held.
  - The lock is released when the process ends, also after a crash (both OS mechanisms guarantee this).
- Lock scope changes:

  | Action | Lock |
  |---|---|
  | `build`, `serve` | `<repo root>/var/kb4it.lock` for the whole run |
  | `verify`, `info` | none (read only) |
  | `create` | `<new repo path>/var/kb4it.lock` while creating; registry lock while writing `projects.json` |
  | `themes`, `apps`, `projects` | none |
  | TUI | no lock at start; each build takes the repository lock; project edits take the registry lock |

- Registry lock: `~/.kb4it/var/projects.lock`, held only while `projects.json` is read-modified-written.
- The global `~/.kb4it/var/kb4it.lock` is no longer used. An existing file is left alone.
- Busy lock: log `[LOCK] BUSY path=<path> pid=<pid>`, print `KB4IT is already building this repository (PID <pid>)`, exit code 1 (same code as today).

**Acceptance.** Tests on all OSes: a second `FileLock` on the same path raises `LockBusyError` with the first PID; two different repositories build concurrently in two subprocesses; a lock held by a killed process is acquirable.

### CP-03 User data directory

**Requirement.**

- The per-user root stays `~/.kb4it` on every OS, resolved with `Path.home()`. On Windows this is `%USERPROFILE%\.kb4it`. No migration needed.
- New optional environment variable `KB4IT_HOME` overrides the root. It is used by the test suite and is useful for portable installs.
- `tests/conftest.py` sets `KB4IT_HOME` (not only `HOME`), so tests never touch the real profile on Windows, where `HOME` is not used.

**Acceptance.** Test: with `KB4IT_HOME` set, `ENV["LPATH"]["ROOT"]` points there and nothing is written under `Path.home()`.

### CP-04 Build script written by `kb4it create`

**Problem.** `kb4it create` writes `bin/compile.sh` and sets Unix permission bits. On Windows the file is useless.

**Requirement.**

- POSIX: unchanged (`bin/compile.sh`, executable).
- Windows: writes `bin/compile.cmd` containing `kb4it -L INFO build "<config path>"`. No `chmod`.
- The config path in both scripts is quoted, so paths with spaces work. (Today `compile.sh` does not quote it; this is fixed on all platforms.)

**Acceptance.** Test checks the file name per `sys.platform`, and that the path is quoted.

### CP-05 TUI clipboard on macOS and Windows

**Requirement.** `_copy_to_clipboard` tries, in order: `wl-copy`, `xclip`, `xsel` (Linux), `pbcopy` (macOS), `clip.exe` (Windows, text passed as UTF-16LE), then OSC 52. Only commands that exist on `PATH` are tried (`shutil.which`).

**Acceptance.** Unit test with a fake `PATH` checks the order per platform.

### CP-06 Path and file name portability

**Requirement.**

- `kb4it/services/processor.py:189` builds the path with `os.path.join`.
- File name case clash: during stage 2, when two sources differ only by letter case (`Foo.md`, `foo.md`), log `[PROCESSOR] DOC_NAME_CLASH a=Foo.md b=foo.md` as a warning on every OS. Their pages would overwrite each other on macOS and Windows targets. With `fail_on_invalid: true` the clash fails the build.
- Reserved Windows names: a source whose stem is `CON`, `PRN`, `AUX`, `NUL`, `COM1` to `COM9` or `LPT1` to `LPT9` (any case) is reported as `[PROCESSOR] DOC_NAME_RESERVED doc=<name>` and left out of the site on every OS, since its page cannot exist on Windows.
- The `relocate_links` and `copydir` helpers are checked with Windows paths in tests.

**Acceptance.** Tests for the clash warning, the reserved name rule and Windows-style paths in `copydir` (using `ntpath` where the host is POSIX).

### CP-07 Line endings

**Requirement.**

- Sources with CRLF line endings parse exactly like LF sources: frontmatter, H1 title, body hash. (Text mode reading already translates CRLF; this requirement adds a test and fixes any path that reads bytes.)
- The body hash is computed on the LF-normalized text, so a repository checked out with `core.autocrlf=true` does not recompile every document after switching OS.
- A `.gitattributes` rule keeps `*.sh` files LF and `*.cmd` / `*.ps1` files CRLF in this repository.

**Acceptance.** Test: the same document with LF and with CRLF yields the same metadata and the same body hash.

### CP-08 Packaging metadata

**Requirement.**

- `pyproject.toml` classifiers: replace `Operating System :: POSIX :: Linux` with `Operating System :: OS Independent`.
- `README.md` badge and text: "GNU/Linux, macOS, Windows".
- `scripts/distribution/` (deb, rpm, docker) stays Linux only; only dependency lists are updated (MD-02 adds Pygments).

### CP-09 CI matrix

**Requirement.** `.github/workflows/kb4it.yml` runs a matrix:

| OS | Python |
|---|---|
| `ubuntu-latest` | 3.11, 3.13 |
| `macos-latest` | 3.11, 3.13 |
| `windows-latest` | 3.11, 3.13 |

Steps per job (with `shell: bash`, which GitHub provides on Windows too):

1. `uv tool install .` and `kb4it --version`.
2. The test suite (`scripts/devel/test.sh`, which gains a `--python` option so the matrix version is used).
3. Smoke build: for each bundled theme, `kb4it create <theme> <tmp>/<theme>` then `kb4it build <tmp>/<theme>/config/repo.json`, then a check that `index.html` exists.

Linux only (once): `check_themes.sh`, wheel build, `check_wheel_themes.py`.

**Acceptance.** All matrix jobs green on the final commit of the series.

### CP-10 Test suite portability

**Requirement.**

- Tests that build subprocess environments set `KB4IT_HOME` instead of only `HOME`.
- Tests that rely on POSIX permission bits are skipped on Windows with a reason.
- Tests compare paths with `os.path.normcase` / `Path` objects, not strings with `/`.

## Phase 2: Live preview

### SV-01 `kb4it serve`

**Command.**

```text
kb4it serve <config> [--host 127.0.0.1] [--port 8642] [--no-watch] [--no-reload] [--open] [--interval 1.0] [-f/--force]
```

**Behaviour.**

1. Takes the repository lock (CP-02) for the whole run.
2. Runs a normal build (with `--force` if given). If the first build fails, the server still starts and shows the error (see below).
3. Serves the target directory over HTTP on `host:port`. If the port is busy, tries the next 50 ports, like the TUI. Logs `[SERVE] LISTEN url=http://127.0.0.1:8642/`.
4. Watches, by polling every `--interval` seconds (no new dependency, same behaviour on every OS):
   - the source directory (`*.md`, `*.markdown`, and asset files),
   - `repo.json`,
   - the theme directory when it is not a bundled theme (user theme or `theme_path`),
   - the overrides directory (CU-01) and the hooks file (CU-02).
5. On change, waits 0.5 s for more changes (debounce), then rebuilds in the same process with a new `KB4IT` instance (requires FX-01). Logs `[WATCH] CHANGE files=<n>` and `[SERVE] REBUILD elapsed=<s> result=ok|failed`.
6. A change to `repo.json` or to the theme triggers a forced rebuild.
7. `Ctrl+C` stops cleanly: `[SERVE] STOP`.

**Live reload.**

- The server injects a small script before `</body>` in every HTML response it serves. Files on disk are not changed, so the deployed site never contains it.
- The script polls `/__kb4it/status` every second. The endpoint returns `{"build": <counter>, "ok": true|false, "error": "<message>"}`. When `build` changes, the page reloads.
- When the last build failed, the script shows a fixed banner at the top of the page with the error message, so the author sees it without looking at the terminal.
- `--no-reload` disables injection.
- Polling, not WebSockets: it works with the standard library `http.server`, behind simple proxies, and from every browser.

**Security.** Default host is `127.0.0.1`. Binding to another address logs `[SERVE] WARNING_PUBLIC host=<host>`. The server only serves files inside the target directory (standard `SimpleHTTPRequestHandler` with `directory=`).

**Code.** The web server code moves from `kb4it/tui/app.py` to a new module `kb4it/core/webserver.py`, used by both the TUI and `serve`.

**Acceptance.** Tests start `serve` on a free port in a subprocess, request `index.html`, check the injected script, edit a source, and wait for `/__kb4it/status` to report a new build and for the page to contain the change. A test checks the error banner after a broken frontmatter.

### SV-02 TUI integration

**Requirement.** The Project screen action "Browse via Web Server" uses `kb4it/core/webserver.py` and gains live reload: it watches and rebuilds like `serve`, and the Build screen log shows rebuilds. The plain "Browse Local" (`file://`) action is unchanged.

**Acceptance.** Existing TUI tests pass; a new test checks that the server object exposes the status endpoint.

## Phase 3: Markdown pipeline

### MD-01 Configurable Markdown extensions

**Configuration** (new optional `repo.json` block):

```json
"markdown": {
    "extensions": ["pymdownx.tasklist", "pymdownx.details", "def_list"],
    "extension_configs": {
        "pymdownx.tasklist": {"custom_checkbox": true}
    },
    "highlight": "client"
}
```

**Behaviour.**

- The built-in extensions are always on: `extra`, `admonition`, `toc`, `sane_lists`, and the KB4IT link rewriter. User extensions are appended in order; duplicates are ignored.
- At stage 1, every extension is imported once. A missing one raises `ConfigError` with `[COMPILER] MD_EXTENSION_MISSING name=<name> hint=pip install <package>`. A bad `extension_configs` entry raises `ConfigError` with the extension's own message.
- A change to the `markdown` block forces a full recompile. The processor stores a hash of the block in `kbdict.json`, next to the theme site signature.
- `kb4it verify` validates the block too.

**Dependencies.** `pymdown-extensions` is offered as an optional extra: `uv tool install "KB4IT[extras]"`. It is not a required dependency.

**Acceptance.** Tests: tasklist output appears with the extension; a missing extension fails the build with the hint; changing the block recompiles all documents.

### MD-02 Server-side code highlighting

**Configuration.** `markdown.highlight` takes:

| Value | Effect |
|---|---|
| `client` | Default. Unchanged: highlight.js in the browser (techdoc, blog). |
| `pygments` | Code blocks are highlighted at build time with Pygments (`codehilite`, CSS class `highlight`). Themes do not load highlight.js. |
| `none` | No highlighting at all. |

**Behaviour with `pygments`.**

- New required dependency: `Pygments`.
- The deployer writes `resources/common/css/pygments.css` with a light style and a dark style under `@media (prefers-color-scheme: dark)`. Style names are configurable: `markdown.pygments_style` (default `default`) and `markdown.pygments_style_dark` (default `monokai`).
- Fenced blocks without a language are not guessed (`guess_lang: false`).
- techdoc and blog templates include `pygments.css` and skip highlight.js when the value is `pygments`. bookshelf and apphelp, which have no highlighting today, gain it when the value is `pygments` and stay unchanged with `client`.

**Acceptance.** Tests: `pygments` output contains `<div class="highlight">` and no highlight.js script tag; `client` output is byte-identical to 0.8.0 for the same input (except the generator version).

### MD-03 Line ending and frontmatter robustness

Covered by CP-07. Listed here because the compiler's frontmatter stripping (`text.find("\n---", 3)`) is part of the pipeline: it must also accept a closing `---` followed by trailing spaces, as the frontmatter parser already does.

## Phase 4: Full-text search

### SR-01 Shared search engine

**Requirement.**

- The apphelp index builder and engine move to shared code:
  - `kb4it/core/search.py`: `extract_sections(html, container_xpath)`, `page_record(...)`, `render_index_js(records, var_name)`.
  - `kb4it/resources/common/js/kb4it-search.js`: the scoring engine now in `apphelp/framework/apphelp/js/search.js`.
- apphelp keeps its UI and behaviour; `apphelp_search.py` and its `search.js` become thin wrappers or are replaced by imports, and its existing tests pass unchanged.
- The index stays a `.js` file that sets a global, so search works from `file://`.

### SR-02 Search in techdoc, blog and bookshelf

**Behaviour.**

- New optional `repo.json` key `search` (default `true` for these three themes).
- After deploy, the theme writes `search-index.js` with one record per document page: URL, title, Category, Date, Tag, and per-section text from the article body. System pages (key and key/value pages, stats, about) are not indexed.
- Each theme header gets a search box. Typing shows up to 8 results in a dropdown; Enter opens `search.html` with the full result list and filters by Category and Tag.
- Index size above 5 MB logs `[SEARCH] INDEX_LARGE size=<bytes>` (same threshold idea as apphelp).
- `"search": false` removes the box, the page and the index file.

**Acceptance.** Tests: the index contains body text of a document; system pages are absent; with `search: false` no `search-index.js` exists in the target. A JavaScript engine test (like `tests/apphelp/test_search_js.py`) runs on the shared engine.

### SR-03 Incremental index

The index is rebuilt from the deployed HTML on every build (as apphelp does). Section extraction for unchanged pages is cached in `var/cache/search/` keyed by the page hash, so a build that compiles one document only re-parses that page.

## Phase 5: Publishing metadata

### PB-01 Site URL

New optional `repo.json` key `site_url`: the absolute public URL of the site, for example `https://t00m.github.io/blog/`. A trailing `/` is added when missing. Without it, the features below that need absolute URLs are skipped with one info line each: `[SITEMAP] SKIP reason=no_site_url`, `[FEED] SKIP reason=no_site_url`.

### PB-02 Sitemap and robots.txt

**Behaviour (all themes, when `site_url` is set).**

- `sitemap.xml` lists every deployed `.html` page, except `admin/`, `404.html` and pages a theme marks as not indexable. `lastmod` is the document `Date` when present, otherwise the page's build time.
- `robots.txt` is written with `Sitemap: <site_url>sitemap.xml`, unless the source directory already contains a `robots.txt`, which is then copied as is.
- New optional key `"sitemap": false` disables both.

**Acceptance.** Tests: valid XML with the expected URLs; no file without `site_url`; a user `robots.txt` wins.

### PB-03 Atom feed

**Behaviour.**

- `feed.xml` in Atom 1.0 format.
- blog: on by default when `site_url` is set. techdoc and bookshelf: off by default, on with `"feed": {"enabled": true}`. apphelp: no feed.
- Options: `"feed": {"enabled": true, "limit": 20, "categories": ["Post", "Note"], "full_content": true}`.
- Entries: dated documents, newest first, filtered by `Category` when `categories` is set. Each entry has title, link, `updated` from `Date`, author from `Author`, and either the full article HTML or the first paragraph.
- Each page head gets `<link rel="alternate" type="application/atom+xml" href="feed.xml">` when a feed exists.

**Acceptance.** Tests: the feed parses as XML, has the right number of entries, order and links; filtering by category works.

### PB-04 Page metadata (SEO and Open Graph)

**Behaviour.**

- New common template `HTML_HEAD_META.tpl` in `kb4it/resources/common/templates/`, included by every theme's page head. It emits:
  - `<meta name="description">` from the frontmatter key `Summary` when present, otherwise the first paragraph of the document cut to 160 characters at a word boundary. Key, key/value and system pages use the repository `tagline`.
  - `og:title`, `og:type` (`article` for documents, `website` otherwise), `og:site_name`, `og:description`.
  - With `site_url`: `<link rel="canonical">` and `og:url`.
  - With the new optional key `og_image` (a path inside the site): `og:image` as an absolute URL and `twitter:card` = `summary_large_image`; otherwise `twitter:card` = `summary`.
- The blog's fixed `<meta name="description" content="KB4IT document">` and `<meta name="author" content="KB4IT by t00m">` are replaced. The author meta uses the document `Author` when present.
- Themes can override `HTML_HEAD_META.tpl` like any template.

**Acceptance.** Tests on a built page check each tag, with and without `site_url`.

## Phase 6: Customization and extension

### CU-01 Per-repository template and static overrides

**Behaviour.**

- New lookup order for a template `<NAME>`:
  1. `<repo root>/overrides/templates/<NAME>.tpl`
  2. `<theme>/templates/<NAME>.tpl`
  3. `kb4it/resources/common/templates/<NAME>.tpl`
- `<repo root>/overrides/static/` is copied as is into the target root after the theme resources, so a site can add `custom.css` or replace an image.
- New optional key `overrides` changes the folder (resolved like `source`, relative to the repository root).
- Each override used is logged once: `[BUILDER] TEMPLATE_OVERRIDE name=<NAME> path=<path>`.
- A hash of the override files is part of the site signature, so changing an override recompiles every page.
- Required-template validation (`HTML_BODY`, `PAGE_INDEX`, ...) considers overrides.

**Acceptance.** Tests: an override of `HTML_FOOTER.tpl` appears in every page; removing it restores the theme's footer after the next build; a file in `overrides/static/` reaches the target.

### CU-02 Build hooks

**Configuration.** Optional key `"hooks": "hooks/hooks.py"` (path relative to the repository root). If absent and `<repo root>/hooks/hooks.py` exists, it is not loaded: hooks must be enabled explicitly.

**Hook functions** (all optional; a hook file defines only the ones it needs):

| Function | Called | Receives | Returns |
|---|---|---|---|
| `on_config(repo)` | after `repo.json` is loaded and validated | a copy of the config dict | the dict to use |
| `on_document(doc_id, meta, text)` | before a document is compiled | file name, metadata dict, Markdown body (without frontmatter) | new Markdown body |
| `on_page(doc_id, html)` | after the theme builds the page, before deploy | file name, full HTML | new HTML |
| `on_build_end(target, summary)` | after stage 8 | target path, dict with the build summary counters | nothing |

**Behaviour.**

- The file is loaded with `importlib` under a unique module name, so it cannot clash with theme modules.
- An exception inside a hook raises `CompilationError` naming the hook and the document: `[HOOKS] FAIL hook=on_page doc=foo.md error=<message>`.
- A hash of the hook file is part of the site signature.
- Hooks run with the same rights as KB4IT. The docs state this plainly: do not enable hooks from a repository you do not trust.
- `on_document` and `on_page` run in the compiler's worker threads; the docs say hook code must be thread safe.

**Acceptance.** Tests for each hook, for the failure path, and for the signature change.

## Phase 7: Backlinks and link checks

### KG-01 Backlinks

**Behaviour.**

- The processor extracts the outgoing `.md` links of each document during analysis (stage 3), using the same parser as the compiler (`MdLinkExtension`). For unchanged documents the links come from `kbdict.json`, so only changed documents are parsed.
- `kbdict.json` gains a `links` map: `{doc_id: [target_doc_id, ...]}`.
- From it the processor builds the inverse map (backlinks). When the set of backlinks of a document changes, that document is marked for recompilation even if its own text did not change.
- Themes receive `var['page']['backlinks']`, a list of `{title, href}` sorted by title. techdoc, blog and bookshelf show a "Linked from" section at the end of the page when the list is not empty. apphelp shows it in its "Related" area.
- New optional key `"backlinks": false` hides the section (the data is still computed for KG-02).

**Acceptance.** Tests: A links to B, so B's page lists A; removing the link from A rebuilds B and the section disappears; unchanged documents are not recompiled.

### KG-02 Link checks in `kb4it verify`

`kb4it verify` reports links to Markdown files that do not exist (`LINK_BROKEN`) as problems, using the link data from KG-01. Anchors (`#section`) are checked against the target's headings when the target is a source document. Broken links in `verify` count as problems (exit 1); during `build` they stay warnings, as today.

**Acceptance.** Test: `verify` exits 1 and names the source and the missing target.

## Phase 8: Versioned help (apphelp)

### VH-01 Versioned output

**Configuration.**

```json
"apphelp": {
    "version": "0.9",
    "versions": {"enabled": true, "latest": "0.9"}
}
```

**Behaviour.**

- With versions enabled, the build writes into `<target>/<version>/` instead of `<target>/`. The target root holds:
  - `versions.json` and `versions.js` (for `file://`): list of `{label, path}`, newest first, and the `latest` label.
  - `index.html` that redirects to `latest/` (or to the `latest` version folder).
  - `latest/`: a copy of the latest version folder (copy, not symlink, so it works on Windows and GitHub Pages).
- Older version folders already in the target are kept and listed. The build only replaces its own version folder.
- `helpids.js` exists per version; the root `helpids.js` points to `latest`.

### VH-02 Version switcher

The apphelp header shows a version selector (from `versions.js`) when more than one version exists. Switching keeps the current page when it exists in the other version, otherwise opens that version's landing page.

### VH-03 Publishing workflow

The help site workflow (`.github/workflows/help.yml`) gets a documented pattern: fetch the published `gh-pages` content into the target before building, so earlier versions are kept. Docs page `howto-publish-github-pages.md` explains it.

**Acceptance (VH).** Tests: two builds with versions `0.8` and `0.9` leave both folders, `versions.json` lists both with `0.9` as latest, the root redirects to it, the switcher markup appears.

## Phase 9: Documentation and packaging

### DOC-01 Help site pages

| Page | Change |
|---|---|
| `howto-install.md` | Windows and macOS instructions (uv in PowerShell; Homebrew or the uv installer on macOS); WSL noted as an alternative |
| `reference-command-line.md` | `serve` command and options |
| `reference-repo-json.md` | `markdown`, `search`, `site_url`, `sitemap`, `feed`, `og_image`, `overrides`, `hooks`, `backlinks`, `apphelp.version(s)` |
| New `howto-preview.md` | Writing with `kb4it serve` |
| New `howto-customize-templates.md` | Overrides, with a Mermaid example built on MD-01 + CU-01 |
| New `howto-hooks.md` | Hooks, with examples and the trust warning |
| `reference-theme-*.md` | Search, feeds, backlinks per theme |
| `howto-use-tui.md` | Live reload in the web server action |
| `troubleshooting.md` | Lock busy message, Windows reserved names, case clashes, missing Markdown extensions |

Every page passes `kb4it verify help/config/repo.json`.

### DOC-02 AGENTS.md and README.md

`AGENTS.md`: commands (`serve`), architecture (lock module, webserver module, search module, hooks), lookup order with overrides, new `repo.json` keys, new `kbdict` fields, supported platforms. `README.md`: platforms, `serve` in the quick start, feature list.

### DOC-03 Theme requirements

Themes that use new core features declare `"kb4it": ">=0.9.0"` in `theme.json` and bump their own `version`.

### DOC-04 CHANGELOG

One entry per requirement under `## [Unreleased]`, grouped in `### Added`, `### Changed`, `### Fixed`, `### Removed`.

### DOC-05 Release

The version stays `0.8.0` in the series. The release to `0.9.0` is done with `scripts/release.sh` after the series is merged, as `RELEASING.md` describes.

## Compatibility

Changes a user of 0.8.0 will notice without changing anything:

| Change | Why |
|---|---|
| Lock file moves from `~/.kb4it/var/kb4it.lock` to `<repo>/var/kb4it.lock` | CP-02; different repositories can build in parallel |
| `kb4it create` quotes the config path in `compile.sh` | CP-04 |
| Search box and `search.html` appear in techdoc, blog and bookshelf | SR-02; `"search": false` restores the old pages |
| Page heads gain description and Open Graph tags; blog's fixed description is replaced | PB-04 |
| "Linked from" section on documents that have backlinks | KG-01; `"backlinks": false` hides it |
| Documents named like Windows device names (`con.md`) are left out | CP-06 |
| `kb4it verify` exits 1 on broken links | KG-02 |

Everything else (`site_url`, feeds, sitemap, `markdown`, `pygments`, overrides, hooks, versions) only changes output when the new key is set. Existing `kbdict.json` files are upgraded on the first build; the new fields force one full rebuild.

## Decisions for review

These are the choices I made where more than one answer was reasonable. Each has my recommendation; change any of them in your review.

| # | Decision | Recommendation | Alternative |
|---|---|---|---|
| D-1 | File watching | Polling, no new dependency | `watchdog` package: faster on huge repositories, one more dependency |
| D-2 | Live reload transport | HTTP polling of `/__kb4it/status` | WebSockets: instant, needs a dependency or a hand-written server |
| D-3 | Default highlighting | `client` (unchanged look) | `pygments` by default: better output, visible change for existing sites |
| D-4 | `pymdown-extensions` | Optional extra | Required dependency, so every extension works out of the box |
| D-5 | Search on by default in techdoc, blog, bookshelf | Yes | Off by default, opt in with `"search": true` |
| D-6 | Feed format | Atom only | Atom and RSS 2.0 |
| D-7 | Hooks enabled by | Explicit `hooks` key only | Auto-load `hooks/hooks.py` when present |
| D-8 | Lock scope | Per repository | Keep one global lock, only make it cross-platform |
| D-9 | User data folder on Windows | `%USERPROFILE%\.kb4it` | `%LOCALAPPDATA%\KB4IT` (Windows convention) |
| D-10 | Versioned help | In 0.9 (phase 8, last) | Move to 0.10 to keep this release smaller |
| D-11 | Windows reserved names | Left out on every OS | Only warn |
| D-12 | Python versions in CI | 3.11 and 3.13 | 3.11, 3.12 and 3.13 (9 jobs instead of 6) |

## Testing summary

- Unit tests for every requirement, under `tests/core/`, `tests/themes/`, `tests/apphelp/`, `tests/tui/` and a new `tests/serve/`.
- The CI matrix (CP-09) runs everything on Linux, macOS and Windows.
- Byte-identical output check: a fixture repository per theme is built with 0.8.0 settings and compared to a stored snapshot (`scripts/devel/theme_snapshot.py` exists for this), except for the documented compatibility changes.
- I can run the full suite and the smoke builds on Linux in this environment. macOS and Windows are verified by the CI matrix once the series is pushed; I cannot run them here.

## Related Topics

- `responses/KB4IT-SSG-COMPARISON.md`: the comparison that produced the roadmap.
- `AGENTS.md`: architecture and contribution rules.
- `RELEASING.md`: release procedure.
