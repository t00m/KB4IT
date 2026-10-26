---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-26
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT, RHEL, uv, pipx
Scope: Development
Status: Draft
Tag: specification, versioning, packaging, fingerprint, venv
Topic: Installation, Upgrade
---

# KB4IT 0.10 specification: build identity, theme versions and the source installer

## Overview

Three problems showed up while installing the 0.10.0 branch on a RHEL 8.10 server with Python 3.11:

1. `scripts/install/local/install_kb4it_from_source.sh` produced an incomplete installation. A plain venv with `pip install` of the wheel built by `scripts/distribution/build/build_python.sh` worked.
2. Every build of the branch reports `0.10.0`. An installed copy cannot tell which commit it was built from.
3. Themes carry no version of their own. `Frontend.theme_load()` overwrites `theme["version"]` with the KB4IT version, and a theme change does not rebuild the pages that are already in the cache.

This specification defines three work packages:

| ID | Work package | Fixes |
|---|---|---|
| `BI` | Build identity: stamp the commit into every package, show it everywhere KB4IT shows a version | Problem 2, and part of the stale cache |
| `TV` | Theme version and fingerprint: a declared version plus a hash of the theme files, part of the core signature | Problem 3, and the rest of the stale cache |
| `SI` | Source installer: build the wheel, check it, install it with uv, pipx or a plain venv, verify the result | Problem 1 |

Each requirement has an ID (`BI-01`, `TV-01`, `SI-01`, ...). The plan, the commits and the CHANGELOG entries refer to these IDs. The base is branch `0.10.0` at `0a71990`.

## Findings

### Confirmed

| # | Where | Problem | Effect |
|---|---|---|---|
| F1 | `install_kb4it_from_source.sh` | Installs from the working tree (`uv tool install .`, `pip install .`) and never runs `scripts/help/build_offline.py` | The installation has no `kb4it/resources/help/`: `kb4it help` and the first-run notice find no offline help. Reproduced: the installed `kb4it/resources/` holds `bases common editor render themes`, no `help` |
| F2 | `kb4it/core/main.py` `version_text()` | `git describe` is read only when the package runs from a checkout that has `.git` | Every installed copy (uv, pipx, venv, `.deb`, `.rpm`, container) prints the bare `KB4IT 0.10.0` |
| F3 | `kb4it/services/backend.py:302` | The cache is dropped only when `kb4it_version` changes, and it holds the bare `X.Y.Z` | Installing a newer commit of the same version reuses every cached page. Reproduced: `6892218~1` then `0a71990` gives `compiled=0 skipped=2`, and 13 of 42 pages have the new Search link; `-f` gives 42 of 42 |
| F4 | `Processor.signature_parts()` | Theme templates, theme logic, the template base and the common templates are not part of the core signature, and techdoc does not override `site_signature()` | A theme change never rebuilds cached pages, also within a single install |
| F5 | `kb4it/services/frontend.py:132`, `kb4it/tui/projects.py:67` | `theme["version"] = ENV["APP"]["version"]` | A theme never has a version of its own; a user theme looks as new as KB4IT |
| F6 | `install_kb4it_from_source.sh` verify step | Runs whatever `kb4it` comes first on `PATH` and prints only the version | A stale copy (old `pip --user`, another pipx home, `/usr/bin/kb4it` from an rpm) passes as success, and since every build says `0.10.0` the user cannot see the difference |
| F7 | `install_kb4it_from_source.sh` pipx branch | Reuses the venv only at `~/.local/share/pipx/venvs/kb4it`; pipx older than 1.3 keeps it at `~/.local/pipx/venvs/kb4it` | On older pipx the "fast" path is skipped silently, and an existing venv is reused whatever Python it was made with |
| F8 | `install_kb4it_from_source.sh` | No plain venv method; needs uv or pipx | On RHEL 8 the method that works (Python 3.11 venv) is not offered |
| F9 | `install_kb4it_from_source.sh` | Builds from whatever is in the tree: local-only themes (`manual`, `basico`, `kb4miaz`), uncommitted edits | The installed package differs from what CI checks and from the release wheel, and nothing says so |
| F10 | `.github/workflows/publish.yml` | Runs `uv build` directly, not `build_python.sh` | Any build-time step added to `build_python.sh` is skipped in releases unless the workflow calls it too |

### Suspected, not reproduced

| # | Where | Problem |
|---|---|---|
| S1 | uv older than the 0.4 series | Builds of a local directory were cached on `pyproject.toml`, `setup.py` and `setup.cfg` only, so `uv tool install . --force` could reinstall a stale wheel. uv 0.11.32 rebuilds correctly. Installing a wheel file (SI-03) removes the question |
| S2 | pipx from EPEL on RHEL 8 | May run on the system Python 3.6, so `pipx install` without `--python` makes a venv KB4IT cannot run in |

## BI: build identity

### Version strings

KB4IT keeps two strings:

- **Release version**: `X.Y.Z` from `kb4it/VERSION`. It stays the package version in `pyproject.toml`, the wheel name and PyPI, and it is what theme requirements (`"kb4it": ">=0.10.0"`) are checked against.
- **Build version**: the release version plus where it came from.

| Build | Build version | Example |
|---|---|---|
| Release: a clean tree at tag `vX.Y.Z` | `X.Y.Z` | `0.10.0` |
| Any other commit | `X.Y.Z-dev+<n>.g<sha7>` | `0.10.0-dev+42.g0a71990` |
| Uncommitted changes | `...+<n>.g<sha7>.dirty` | `0.10.0-dev+42.g0a71990.dirty` |
| No git information at all | `X.Y.Z+unknown` | `0.10.0+unknown` |

`<n>` is the number of commits since the previous release tag (from `git describe --tags`). When it cannot be read (no tags, shallow clone), it is left out: `0.10.0-dev+g0a71990`.

### Requirements

| ID | Requirement |
|---|---|
| BI-01 | New script `scripts/devel/stamp_build.py` writes `kb4it/BUILD.json`: `version`, `build_version`, `commit` (full SHA), `describe`, `branch`, `dirty` (bool), `date` (UTC, ISO 8601), `source` (`release` or `dev`). Without git it writes `commit: null` and `build_version: X.Y.Z+unknown`. Writes atomically with `json_save` |
| BI-02 | `kb4it/BUILD.json` is git-ignored and listed in the `pyproject.toml` `include` table, like `kb4it/VERSION`, so it ships in the wheel and sdist |
| BI-03 | `build_python.sh` runs `stamp_build.py` before the build. `publish.yml`, the `packages` CI job, `docker/build.sh` and the deb and rpm scripts get the stamp through `build_python.sh` or call `stamp_build.py` before `uv build` |
| BI-04 | `publish.yml` checks that the stamped `source` is `release` and `dirty` is false; otherwise it fails before publishing |
| BI-05 | `kb4it/core/version.py` gets `build_info(root)`. Order: a live `git describe` when the package runs from a checkout with `.git` (the checkout is the truth, a `BUILD.json` left in it may be old), then `BUILD.json`, then `X.Y.Z+unknown`. Read once at start-up |
| BI-06 | `ENV["APP"]["version"]` stays `X.Y.Z`. New sealed keys `ENV["APP"]["build_version"]` (string) and `ENV["APP"]["build"]` (the `BUILD.json` fields) |
| BI-07 | `kb4it --version` prints `KB4IT <build_version>`, with the commit and build date on a second line, for example `KB4IT 0.10.0-dev+42.g0a71990` and `commit 0a71990c... built 2026-10-26T08:12:03Z`. `version_text()` stays the single place that formats it |
| BI-08 | The build version replaces the bare version in: `kb4it info`, the `[CONTROLLER] START` and `END` log lines, the `<meta name="generator">` of every theme, `PAGE_ABOUT_KB4IT.tpl`, the bookshelf footer, the TUI title, and the `[WORKFLOW] SUMMARY` line as `kb4it=<build_version>` |
| BI-09 | `kbdict.json` stores `kb4it_version` (release) and a new `kb4it_build` (build version). A change of either one forces a full rebuild and logs `[BACKEND] KBDICT_BUILD_MISMATCH stored=... current=...`. This fixes F3: the first build after installing another commit compiles everything once |
| BI-10 | A dirty build compares as its commit plus a hash of `git diff HEAD` (kept in `BUILD.json` as `diff_hash`), so two different uncommitted states do not share a cache |
| BI-11 | `tests/core/test_version_sources.py` stays green: the build version is computed, never written by hand in a tracked file |

## TV: theme version and fingerprint

### Requirements

| ID | Requirement |
|---|---|
| TV-01 | `theme.json` gets an optional `version` key (`X.Y.Z`). Every bundled theme declares one. `Frontend` stops overwriting it (F5); the KB4IT version moves to `theme["kb4it_version"]` where code still needs it |
| TV-02 | A theme without `version` loads and logs `[FRONTEND] THEME_VERSION_MISSING id=...` once per build; it is shown as `unversioned` |
| TV-03 | New `theme_fingerprint(theme_path)`: a blake2b hash (12 hex) of every file that shapes the pages: the theme folder (`logic/`, `templates/`, `framework/`, `theme.json`; not `apps/`, not `__pycache__`), its template base and `kb4it/resources/common/templates/`. Paths sorted, file names hashed with contents, so a rename counts. Cached per build |
| TV-04 | The theme identity is `<id> <version>+<fingerprint>`, for example `techdoc 1.0.0+3f9a1c0b7e21`. It is shown by `kb4it themes` (new columns Version and Fingerprint), `kb4it info`, the TUI Themes screen, the log (`[FRONTEND] THEME_LOADED id= version= fingerprint= path=`), and the generator meta: `KB4IT 0.10.0-dev+42.g0a71990; techdoc 1.0.0+3f9a1c0b7e21` |
| TV-05 | `Processor.signature_parts()` gets an entry `"theme": theme_fingerprint(...)`. A theme change logs `[PROCESSOR] CORE_SIGNATURE_CHANGED` and rebuilds everything, with or without a new KB4IT install. This fixes F4 |
| TV-06 | `kb4it themes` also prints the path each theme is loaded from (source, user, built-in, `theme_path`), so a user copy in `~/.kb4it/opt/resources/themes/` that hides the built-in theme is visible |
| TV-07 | `scripts/devel/check_themes.py` fails a release when a bundled theme's files changed since the previous release tag and its `version` did not. It prints the theme, the changed files and the old version. Fingerprints of the previous tag are computed from `git archive`, nothing new is stored |
| TV-08 | `help/source/howto-create-theme.md` and the theme reference pages document `version` and the fingerprint; the sample custom theme in `tests/fixtures/themes/mini/` gets a `version` |

## SI: source installer

`install_kb4it_from_source.sh` builds the same wheel as a release, checks it, installs it with the method the machine supports, and proves that the `kb4it` on `PATH` is the one just built.

### Usage

```bash
scripts/install/local/install_kb4it_from_source.sh [--method auto|uv|pipx|venv] [--python PATH] [--allow-dirty] [--extras]
```

### Requirements

| ID | Requirement |
|---|---|
| SI-01 | Python discovery checks `--python`, then `python3.14` down to `python3.11` on `PATH` (not only `/usr/bin`), then `python3`. A Python older than 3.11 is never used. When none is found, the error names the fix for the platform, for example `sudo dnf install python3.11` on RHEL 8 and 9 |
| SI-02 | Before building, the script lists untracked files under `kb4it/` and uncommitted changes (F9). It stops unless `--allow-dirty` is given; with it, the build is stamped `dirty` (BI-10) |
| SI-03 | It builds with `scripts/distribution/build/build_python.sh` (offline help and stamp included, F1), then runs `scripts/devel/check_wheel_themes.py`. It installs the wheel file, never the directory (S1) |
| SI-04 | `--method auto` picks uv, then pipx, then venv. `uv`: `uv tool install <wheel> --force --reinstall --python <python>`. `pipx`: `pipx install <wheel> --force --python <python>`; no reuse of an existing venv at a guessed path (F7, S2). `venv`: see SI-05 |
| SI-05 | The venv method (F8) creates `${KB4IT_VENV:-~/.local/share/kb4it/venv}` from the chosen Python, upgrades pip inside it, installs the wheel with `--force-reinstall`, and links `~/.local/bin/kb4it` to its `bin/kb4it`. It recreates the venv when its Python is not the chosen one. With `--extras`, every method installs `KB4IT[extras]` |
| SI-06 | Verification (F6) runs the installed binary by its absolute path: `kb4it --version` must print the build version of the wheel just built. Then `type -a kb4it` (POSIX `command -v` on other shells): when the first `kb4it` on `PATH` is another one, the script prints every match and how to remove or reorder it, and exits 2 |
| SI-07 | Verification also runs a new `kb4it doctor`, which lists the build version, Python, the installation path, the offline help, the editor bundle, every theme with its version, fingerprint and path, and exits 1 when something bundled is missing. It can be run any time, and its output is what a bug report should include |
| SI-08 | `scripts/uninstall/local/uninstall.sh` removes the venv method too (the venv folder and the `~/.local/bin/kb4it` link, only when the link points into that venv) |
| SI-09 | Tests in `tests/packaging/test_install_scripts.py`, with fake `uv`, `pipx` and Python executables as today: method selection, Python 3.6 refused, dirty tree refused, wheel installed instead of the directory, shadowed `kb4it` exits 2, venv method recreated on a different Python |
| SI-10 | `help/source/howto-install.md`: the "Run the latest code" section uses the script, documents `--method venv` for RHEL 8, and shows how to read the commit with `kb4it --version` and `kb4it doctor` |

## Order of work

1. **BI**: SI-06 and SI-07 need the build version to prove what was installed.
2. **TV**: TV-05 relies on the same signature code as BI-09; doing both together leaves one full rebuild after upgrading.
3. **SI**.
4. Help pages, `AGENTS.md` (module table, `kb4it doctor` in the commands, `BUILD.json`, `theme.json` `version`), `CHANGELOG.md` under `## [Unreleased]`.

## Compatibility

- Sites built by an earlier 0.10.0 compile everything once, because `kb4it_build` is missing from their `kbdict.json` (BI-09).
- Custom themes keep working without `version` (TV-02).
- Code reading `ENV["APP"]["version"]` sees the same `X.Y.Z` as before (BI-06). Theme code that read `theme["version"]` as the KB4IT version gets the theme version; no bundled theme reads it.
- PyPI, the wheel name and the release process (`scripts/release.sh`, `RELEASING.md`) keep `X.Y.Z`; only the stamp is added.

## Open decisions

| # | Question | Recommendation |
|---|---|---|
| D1 | First `version` of the bundled themes | `1.0.0` for all four in 0.10.0, then semantic versions of their own. The alternative, copying the KB4IT version, brings back F5 |
| D2 | Build version format | `X.Y.Z-dev+<n>.g<sha7>` as above. The PEP 440 form `X.Y.Z.devN+g<sha7>` would also be valid as wheel metadata, but would put a different version on every wheel and break the `VERSION` equals `pyproject.toml` rule |
| D3 | A dirty tree in the installer | Refuse unless `--allow-dirty` (SI-02) |
| D4 | `kb4it doctor` as a new CLI action | Yes: three touches (subparser, `KB4IT.run()`, `Workflow.doctor()`), plus a TUI entry later |

## Verification

- `./scripts/devel/test.sh` and `./scripts/devel/typecheck.sh` pass.
- `scripts/release.sh --dry-run` passes, and `check_themes.sh` fails with a changed theme whose `version` was not raised (TV-07).
- On a RHEL 8.10 VM with Python 3.11 and no uv: `install_kb4it_from_source.sh --method venv` installs, `kb4it --version` shows the commit of the checkout, `kb4it doctor` exits 0, and `kb4it help` opens the offline help.
- Install `6892218~1`, build a techdoc site, install `0a71990`, build again without `-f`: the summary shows every document compiled and all 42 pages have the Search link (BI-09).
- Edit a techdoc template in a checkout and build without `-f`: `CORE_SIGNATURE_CHANGED` is logged and every page is rebuilt (TV-05).
