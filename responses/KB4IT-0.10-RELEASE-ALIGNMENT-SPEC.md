---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-26
DocType: Reference
OS: Linux
Product: KB4IT, GitHub Actions, PyPI
Scope: Development
Status: Draft
Tag: specification, release, versioning, packaging, fingerprint
Topic: Upgrade, Documentation
---

# KB4IT 0.10 specification: align the release process with build identity and theme versions

## Overview

The versioning work (`responses/KB4IT-0.10-VERSIONING-SPEC.md`, commits `252d92d` and `c714487`) changed what a version means, what the build cache compares and what a theme carries. The release process (`RELEASING.md`, `scripts/release.sh`, `.github/workflows/publish.yml`, `.github/workflows/kb4it.yml`, the manual PyPI scripts and `help/source/dev-release.md`) was only partly updated.

The changes are compatible with the release mechanics: tag `vX.Y.Z` on the merge commit, the publish workflow, PyPI, the image and the packages all still work. Twelve gaps remain: two documents now state the opposite of what the code does, one new check can be skipped without anyone noticing, one release path can publish a wheel with a development stamp, and the 0.10.0 notes lack the changes users will notice.

Each requirement has an ID (`RA-01`, `RA-02`, ...). The plan and the commits refer to them. Base: branch `0.10.0` at `3781ac0`.

## Findings

| # | Where | Problem | Effect |
|---|---|---|---|
| F1 | `RELEASING.md`, "What the version means" | Shows `KB4IT 0.8.0 (v0.7.10-12-g3a96611)` and says "The build cache compares only the plain version, so installing a development build does not force every site to recompile" | Both are false since BI-07 and BI-09: the output is `KB4IT X.Y.Z-dev+<n>.g<sha7>` plus a commit line, and another build rebuilds every site once. The release guide teaches the old behaviour |
| F2 | `help/source/dev-release.md` line 20 | "A build from a clone adds `git describe` to `kb4it --version`" | Same as F1, in the published developer help |
| F3 | `scripts/devel/check_themes.py` `previous_release()` | With no `vX.Y.Z` tag in the clone, it prints `previous release: none` and skips the theme version check (TV-07) | CI (`kb4it.yml`, shallow checkout, no tags) never runs the check. `release.sh --commit` runs it only when the maintainer has fetched tags. Confirmed: this clone is shallow with 0 tags and the check passed |
| F4 | `.github/workflows/publish.yml` | Is the only place where the theme version check surely runs (`fetch-depth: 0`) | A forgotten theme version is found after the tag is pushed. `RELEASING.md` forbids moving a tag, so the only way out is the next patch release |
| F5 | `RELEASING.md`, "The steps" | No step raises theme versions. Step 4 refuses to commit when files other than the release files are modified | The maintainer learns about TV-07 from a failing `--commit`, then has to commit the `theme.json` files apart, as in step 2b, with no instructions |
| F6 | `scripts/release.sh --commit`, wheel guard | Runs `uv build --wheel` without `stamp_build.py` | The wheel it checks has no `BUILD.json`. A missing stamp in the real release would go unnoticed until users report `+unknown` |
| F7 | `publish.yml`, `check_wheel_themes.py` | Nothing checks that the wheel's `BUILD.json` exists, says `source: release` and names the tag's version | `stamp_build.py --require-release` stops a wrong commit, but a packaging slip (the `include` entry removed, the stamp run after the build) would ship unstamped wheels to PyPI, the image and the packages |
| F8 | `scripts/distribution/pypi/publish_pypi.sh`, `publish_testpypi.sh`; `RELEASING.md` "One-time setup" | The manual fallback stamps without `--require-release`, and `RELEASING.md` says to build "from a clean export of the tag" | An export has no `.git`, so the stamp is `X.Y.Z+unknown`; a build from a working tree uploads a `-dev+` stamp to PyPI. Either way `kb4it --version` of the published package does not say `X.Y.Z` |
| F9 | `scripts/distribution/docker/smoke.sh`, `RELEASING.md` step 7 | The image smoke test accepts any output that contains the version (`*"${KB4IT_VERSION}"*`); step 7 checks `kb4it themes` only | `KB4IT 0.10.0-dev+3.g1234567` passes the release smoke test. The new `kb4it doctor` is not part of the post-release check |
| F10 | `CHANGELOG.md` `[Unreleased]` | User-visible changes are listed under Added and Fixed only. Missing from Changed: `kb4it --version` prints two lines; the theme listing says `scope=user`, `scope=builtin` instead of `scope=local`, `scope=global`; a custom theme's `version` key is now read and checked; every site rebuilds once after the upgrade and after installing another commit | `releases/0.10.0.md` is drafted from the changelog, so the notes would miss what can break scripts and custom themes. `RELEASING.md` step 3 asks to "mention anything that breaks existing sites or themes" |
| F11 | `kb4it/services/frontend.py` `_identify()` | A custom theme whose `theme.json` holds a `version` that is not `X.Y.Z` (`"1.0"`, `"2.1-beta"`) now stops the build (`THEME_VERSION_INVALID`). Before 0.10 the key was ignored and overwritten | A minor release breaks a custom theme that built fine with 0.9. `RELEASING.md` says a change that breaks themes moves the minor number: 0.10.0 does, but the notes must say so (F10), or the check must start as a warning (D2) |
| F12 | `RELEASING.md`, "Keeping this document current" | Lists `release.sh`, `changelog.py`, `check_themes.py` and the publish workflow | `stamp_build.py` and `check_wheel_themes.py` now shape a release and are not listed |

## Requirements

### Documents

| ID | Requirement |
|---|---|
| RA-01 | `RELEASING.md` "What the version means" describes the build version: `X.Y.Z` for the clean commit of tag `vX.Y.Z`, `X.Y.Z-dev+<n>.g<sha7>[.dirty]` otherwise, `X.Y.Z+unknown` without git facts. It says where the stamp comes from (`stamp_build.py`, `BUILD.json`) and that another build rebuilds every site once (`KBDICT_BUILD_MISMATCH`). The sentence about the cache comparing only the plain version is removed (F1) |
| RA-02 | `RELEASING.md` gets a section "Theme versions". A theme version is independent of KB4IT's. Bump on the first change in a cycle: patch for fixes, minor for new features, major for changes that break overrides or custom templates. `kb4it` (requirement) and `version` (identity) are different fields (F5) |
| RA-03 | `RELEASING.md` gets step 2c, "Raise theme versions", with the command that lists the themes to raise (RA-05) and the commit to make (`chore(themes): raise theme versions`), as step 2b does for requirements (F5) |
| RA-04 | `help/source/dev-release.md` follows RA-01 to RA-03 (F2). `RELEASING.md` "Keeping this document current" adds `stamp_build.py` and `check_wheel_themes.py` (F12) |

### Theme version check

| ID | Requirement |
|---|---|
| RA-05 | `check_themes.py --changed` prints, for each bundled theme whose files (`apps/` aside) changed since the previous release tag while its `version` did not, the theme, its version and the changed files, and nothing else. `release.sh --dry-run` shows it as a guard, so step 1 already names the themes to raise (F4, F5) |
| RA-06 | `check_themes.py --release` fails closed: when `CHANGELOG.md` has a dated release section but no `vX.Y.Z` tag is reachable, it stops with `no release tag found: run git fetch --tags`. `release.sh --commit` and `publish.yml` pass `--release` (F3) |
| RA-07 | The CI theme job (`kb4it.yml`) checks out with `fetch-depth: 0` and runs the version check as a warning (`::warning::` per theme), so a forgotten bump shows in every pull request without turning it red (F3, F4; see D1) |

### Release build stamp

| ID | Requirement |
|---|---|
| RA-08 | `check_wheel_themes.py --stamp X.Y.Z` fails unless the wheel has `kb4it/BUILD.json`, its `version` is `X.Y.Z` and its `build_version` starts with `X.Y.Z`. `--release X.Y.Z` also requires `source: release`, `dirty: false` and `build_version` equal to `X.Y.Z` (F7) |
| RA-09 | `release.sh --commit` builds the wheel with `stamp_build.py` before `uv build` and checks it with `--stamp $VERSION` (F6) |
| RA-10 | `publish.yml` checks the wheel with `--release ${TAG#v}` before `twine check`, so PyPI, the image and the packages only ever get a release stamp (F7) |
| RA-11 | `publish_pypi.sh` and `publish_testpypi.sh` refuse to run outside a git checkout, run `stamp_build.py --require-release` (PyPI) or `stamp_build.py` (TestPyPI) and check the wheel as in RA-08. `RELEASING.md` says to build from a clean clone of the tag (`git clone --branch vX.Y.Z`), not from an export, because the stamp needs git (F8) |
| RA-12 | `docker/smoke.sh` compares the first line of `--version` with `KB4IT ${KB4IT_VERSION}` exactly when `KB4IT_RELEASE=1`, which `publish.yml` sets; CI keeps the prefix check for development images (F9) |
| RA-13 | `RELEASING.md` step 7 checks `kb4it --version` (first line exactly `KB4IT X.Y.Z`, second line the tagged commit) and `kb4it doctor` (exit 0) for the PyPI package and the image (F9) |

### Release notes and compatibility

| ID | Requirement |
|---|---|
| RA-14 | `CHANGELOG.md` `[Unreleased]` gets `### Changed` entries for: the two-line `kb4it --version`; `scope=builtin`, `scope=user`, `scope=source`, `scope=theme_path` in `kb4it themes`; the `version` key of custom themes now read and checked; one full rebuild after the upgrade and after installing another commit (F10) |
| RA-15 | `releases/0.10.0.md`, when drafted, keeps those four points under a "Before you upgrade" heading (F10, F11) |
| RA-16 | Depending on D2: either `THEME_VERSION_INVALID` stays an error and RA-15 says so, or in 0.10.x it is a warning, the theme loads as `unversioned`, and it becomes an error in 0.11.0 (F11) |

## Order of work

1. RA-14 and RA-01 to RA-04: documents only, no risk.
2. RA-08 to RA-12: the stamp checks, with tests in `tests/packaging/`.
3. RA-05 to RA-07: the theme version check modes, with tests next to `tests/core/test_theme_identity.py`.
4. RA-16 after D2; RA-13 and RA-15 are done at release time.

## Open decisions

| # | Question | Recommendation |
|---|---|---|
| D1 | Should a forgotten theme version bump fail CI, or only warn there and fail at release? | Warn in CI (RA-07), fail in `release.sh --commit` and `publish.yml` (RA-06). Failing every pull request after the first theme edit of a cycle punishes ordinary work |
| D2 | A custom theme with a `version` that is not `X.Y.Z`: error now, or warning in 0.10.x? | Warning in 0.10.x (`THEME_VERSION_INVALID` at warning level, theme shown as `unversioned`), error in 0.11.0. It costs one line and keeps 0.9 themes building |
| D3 | Should `release.sh` raise theme versions itself (for example `--bump-themes patch`)? | No: which part to raise is a judgement per theme. `--dry-run` lists them (RA-05), the maintainer edits `theme.json` |

## Verification

- `scripts/release.sh --dry-run` in a clone with tags lists a theme whose template changed since the last tag; in a clone without tags `--commit` stops with `run git fetch --tags`.
- `check_wheel_themes.py --release 0.10.0` fails on a wheel built from a development commit and passes on one built from the tagged commit.
- `publish_pypi.sh` run from `git archive` output stops before building.
- The rendered `RELEASING.md` and `dev-release.md` contain no `git describe` example and no claim that the cache ignores development builds.
