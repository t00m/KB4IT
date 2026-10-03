# Releasing KB4IT

How to cut a release, and why the steps are what they are.

`scripts/release.sh` prepares a release and the publish workflow ships it. This document covers what neither can do for you: deciding the version and writing the release notes.

## What the version means

`kb4it/VERSION` owns the version. `pyproject.toml` carries a copy, and `tests/core/test_version.py` fails when the two differ.

The number names a **release**, not a change. Between releases it names the release being built: `0.8.0` in `kb4it/VERSION` while `CHANGELOG.md` has an `[Unreleased]` section means 0.8.0 is the target. It changes only through `scripts/release.sh`.

Development builds need no counter. In a source checkout, `kb4it --version` adds `git describe`:

```
$ kb4it --version
KB4IT 0.8.0 (v0.7.10-12-g3a96611)
```

That is the last tag, the commits since it and the commit itself, with nothing to edit and nothing to forget. The build cache compares only the plain version, so installing a development build does not force every site to recompile.

KB4IT follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). While the major version is 0, a change that breaks existing sites or themes moves the minor number.

## Themes declare what they need

Every theme's `theme.json` has a `kb4it` requirement, for example `">=0.7.9"` or `">=0.7.9, <0.8"`. KB4IT refuses to load a theme whose requirement it does not meet (`THEME_REQUIREMENT_UNMET`). Raise a theme's requirement when it starts using something new from the core, such as a builder method or a `BuildPlan` field.

`scripts/devel/check_themes.sh` checks every theme tracked in git:

- `theme.json` has `id`, `name`, `version` and `kb4it`, and the `id` matches the folder
- the requirement is met by the version being released
- the required templates and the `deploy_dirs` folders exist
- every sample app under `apps/` is created and built with no error and no warning

It builds from what git tracks, so a file that exists only in your working tree cannot make a theme look fine. The release script and CI both run it.

## Before you start

- Every change for this release is committed and merged into your branch.
- `CHANGELOG.md` has an `[Unreleased]` section holding everything since the last release, in `Added`, `Changed`, `Fixed` and `Removed`.
- `./scripts/devel/test.sh` and `./scripts/devel/check_themes.sh` pass.

## The steps

### 1. Look at what would happen

```bash
scripts/release.sh --dry-run            # release the version in kb4it/VERSION
scripts/release.sh --dry-run 0.8.0      # or a given version, or major / minor / patch
```

This reports the version, whether the tag already exists (locally or on GitHub) and whether there is anything to release. It writes nothing.

### 2. Prepare

```bash
scripts/release.sh                      # or: scripts/release.sh 0.8.0
```

This sets the version in `kb4it/VERSION` and `pyproject.toml`, turns `[Unreleased]` into `[X.Y.Z] - <today>` with a fresh empty `[Unreleased]` above it, and drafts `releases/X.Y.Z.md` from the changelog. Running it twice is safe: the second run finds the section already dated and leaves it alone.

### 3. Write the release notes

`releases/X.Y.Z.md` becomes the body of the GitHub release. Write it for someone deciding whether to update, not for someone reading a diff: one sentence, then the few changes a user would notice. Mention anything that breaks existing sites or themes.

The draft has one line per changelog entry, which is usually too many. Cut it down, then delete the `TODO` line. The script and the workflow both refuse to go on while it is there.

### 4. Check and commit

```bash
scripts/release.sh --commit
```

This refuses to commit when:

- tracked files other than the release files are modified
- the release notes still have their `TODO` line
- the changelog has no dated section for the version
- `kb4it/VERSION` and `pyproject.toml` disagree
- the tests fail
- a tracked theme is not compliant
- the wheel does not hold every tracked theme

When everything passes it commits `chore(release): X.Y.Z`. It never tags and never pushes.

### 5. Merge and tag (yours)

`master` only accepts pull requests, so the tag goes on the merge commit:

```bash
git push -u origin <branch>             # open a pull request to master, let CI pass, merge
git checkout master && git pull --ff-only
git tag vX.Y.Z
git push origin vX.Y.Z
```

### 6. The workflow publishes

Pushing the tag runs `.github/workflows/publish.yml`:

1. **Check:** it confirms the tag equals `kb4it/VERSION` and `pyproject.toml`, the changelog has the dated section, and the notes exist without `TODO`. Then it runs the tests and the theme check, builds, confirms the wheel holds every tracked theme, and runs `twine check`.
2. **Publish:** it uploads to PyPI with trusted publishing (no stored token).
3. **Release:** it creates the GitHub release `vX.Y.Z` with `releases/X.Y.Z.md` as the body and the wheel and sdist attached.

Only plain `vX.Y.Z` tags trigger it. A tag such as `v0.7.39-fix1` is not a PyPI version and is ignored.

### 7. Check it and open the next cycle

```bash
pip install --no-cache-dir KB4IT==X.Y.Z && kb4it themes
scripts/release.sh --open 0.8.0         # commits "chore: target version 0.8.0"
```

## One-time setup

The workflow needs two things it cannot set up itself:

- On pypi.org: KB4IT, Settings, Publishing, add a GitHub Actions publisher with owner `t00m`, repository `KB4IT`, workflow `publish.yml` and environment `pypi`.
- On GitHub: Settings, Environments, an environment named `pypi`; then enable the workflow with `gh workflow enable publish.yml`.

If the workflow cannot be used, `scripts/distribution/pypi/publish_pypi.sh` uploads by hand. Build from a clean export of the tag, never from a working tree, because a working tree may hold themes that are not tracked.

## Keeping this document current

This describes real scripts. When `release.sh`, `changelog.py`, `check_themes.py` or the publish workflow change, change this file in the same commit. A release document that is wrong is worse than none: it gets followed.
