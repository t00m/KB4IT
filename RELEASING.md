# Releasing KB4IT

How to cut a release, and why the steps are what they are.

`scripts/release.sh` prepares a release and the publish workflow ships it. This document covers what neither can do for you: deciding the version and writing the release notes.

## What the version means

`kb4it/VERSION` owns the version. `pyproject.toml` carries a copy, and `tests/core/test_version.py` fails when the two differ.

The number names a **release**, not a change. Between releases it names the release being built: `0.8.0` in `kb4it/VERSION` while `CHANGELOG.md` has an `[Unreleased]` section means 0.8.0 is the target. It changes only through `scripts/release.sh`.

Every build also has a **build version**, which says which commit it is:

| Build | `kb4it --version`, first line |
|---|---|
| The clean commit of tag `vX.Y.Z` | `KB4IT X.Y.Z` |
| Any other commit | `KB4IT X.Y.Z-dev+<n>.g<sha7>`: commits since the last tag, then the commit |
| Uncommitted changes under `kb4it/` | the same, ending in `.dirty` |
| No git facts at all | `KB4IT X.Y.Z+unknown` |

The second line names the full commit and the build date. Nothing is edited by hand. A source checkout reads it from git. A package carries it in `kb4it/BUILD.json`, written by `scripts/devel/stamp_build.py` before the build: `build_python.sh`, CI and the publish workflow run it, and the publish workflow runs it with `--require-release`, which fails unless the commit is the clean commit of the tag.

The build cache (`kbdict.json`) stores the build version. A site built by another build, even another commit of the same version, is rebuilt once on its next build (`KBDICT_BUILD_MISMATCH`). Theme requirements are checked against `X.Y.Z` only.

KB4IT follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). While the major version is 0, a change that breaks existing sites or themes moves the minor number.

## Themes declare what they need

Every theme's `theme.json` has a `kb4it` requirement, for example `">=0.7.9"` or `">=0.7.9, <0.8"`. KB4IT refuses to load a theme whose requirement it does not meet (`THEME_REQUIREMENT_UNMET`). Raise a theme's requirement when it starts using something new from the core, such as a builder method or a `BuildPlan` field.

`scripts/devel/check_themes.sh` checks every theme tracked in git:

- `theme.json` has `id`, `name`, `version` and `kb4it`, and the `id` matches the folder
- a theme whose files (`apps/` aside) changed since the previous release tag has a new `version`: raise it in the theme's `theme.json` (semantic versioning: patch for fixes, minor for new features, major for changes that break overrides or custom templates)
- the requirement is met by the version being released
- the required templates and the `deploy_dirs` folders exist
- every sample app under `apps/` is created and built with no error and no warning

It builds from what git tracks, so a file that exists only in your working tree cannot make a theme look fine. The release script and CI both run it.

The theme version check needs the release tags. CI fetches them and reports a forgotten version as a warning, so a pull request is not blocked. `release.sh --commit` and the publish workflow run the check with `--release`: there a forgotten version fails, and so does a clone without tags when `CHANGELOG.md` lists earlier releases. Run `git fetch --tags` before you start.

## Theme versions

A theme's `version` in `theme.json` is its own, independent of KB4IT's: the four bundled themes started at `1.0.0` in KB4IT 0.10.0. It is not the same field as `kb4it`, the KB4IT the theme needs.

Raise a theme's version once per release in which its files changed (`apps/` aside), following semantic versioning:

- patch (`1.0.1`): fixes that do not change what a site looks like on purpose;
- minor (`1.1.0`): new features, new templates, new `theme.json` keys;
- major (`2.0.0`): changes that break a site's overrides or a custom theme built on this one, such as a renamed template or a removed template variable.

Every build shows the theme as `<id> <version>+<fingerprint>`; the fingerprint changes with every file, so it tells two builds apart even when the version was not raised. The version is what users read.

## Before you start

- Every change for this release is committed and merged into your branch.
- `CHANGELOG.md` has an `[Unreleased]` section holding everything since the last release, in `Added`, `Changed`, `Fixed` and `Removed`.
- `./scripts/devel/test.sh` and `./scripts/devel/check_themes.sh` pass.
- Release tags are in your clone (`git fetch --tags`): the theme version check needs them.

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

### 2b. Raise the requirement of themes that use new core features

While `kb4it/VERSION` still names the previous release, a theme cannot require the new one: KB4IT would refuse to load it and the tests would fail. So a theme that starts using something new from the core keeps its old requirement until the release, and is raised here, after step 2 has set the new version.

For 0.9.0 all four bundled themes use new core features (search, feeds, page metadata, overrides, backlinks):

```bash
for theme in apphelp blog bookshelf techdoc; do
    python3 - "kb4it/resources/themes/$theme/theme.json" 0.9.0 <<'PY'
import json, sys
path, version = sys.argv[1], sys.argv[2]
conf = json.load(open(path, encoding="utf-8"))
conf["kb4it"] = f">={version}"
open(path, "w", encoding="utf-8").write(json.dumps(conf, indent=4, ensure_ascii=False) + "\n")
PY
done
./scripts/devel/check_themes.sh
git add kb4it/resources/themes/*/theme.json
git commit -m "chore(themes): require kb4it 0.9.0"
```

Commit only the `theme.json` files: the `--commit` step expects every other change except `kb4it/VERSION`, `pyproject.toml` and `CHANGELOG.md` to be committed.

### 2c. Raise theme versions

`--dry-run` in step 1 already listed the themes whose files changed since the last release while their version did not. List them again and raise each one in its `theme.json`, as described in [Theme versions](#theme-versions):

```bash
git fetch --tags
./scripts/devel/check_themes.sh --worktree --changed
# edit kb4it/resources/themes/<theme>/theme.json: "version": "X.Y.Z"
./scripts/devel/check_themes.sh --worktree --changed      # "No theme version to raise."
git add kb4it/resources/themes/*/theme.json
git commit -m "chore(themes): raise theme versions"
```

As in step 2b, commit only the `theme.json` files.

### 3. Write the release notes

`releases/X.Y.Z.md` becomes the body of the GitHub release. Write it for someone deciding whether to update, not for someone reading a diff: one sentence, then the few changes a user would notice. Mention anything that breaks existing sites or themes.

The draft has one line per changelog entry, which is usually too many. Cut it down, then delete the `TODO` line. Keep every `Changed` or `Removed` entry that can break a script, a site or a custom theme under a heading "Before you upgrade". The script and the workflow both refuse to go on while it is there.

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
- a tracked theme is not compliant, or changed since the last release without a new version
- the wheel does not hold every tracked theme, the offline help and a build stamp of the version

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

1. **Check:** it confirms the tag equals `kb4it/VERSION` and `pyproject.toml`, the changelog has the dated section, and the notes exist without `TODO`. Then it runs the tests and the theme check (`--release`), stamps the build (`stamp_build.py --require-release`), builds, confirms the wheel holds every tracked theme and the release stamp (`check_wheel_themes.py --release X.Y.Z`), and runs `twine check`.
2. **Publish:** it uploads to PyPI with trusted publishing (no stored token).
3. **Image:** from the same wheel it builds the container image, smoke-tests the amd64 build (the first line of `--version` must be exactly `KB4IT X.Y.Z`), then pushes `ghcr.io/t00m/kb4it` for amd64 and arm64 as `X.Y.Z`, `X.Y` and `latest`, with an SBOM and a build provenance attestation. It logs in with the workflow token; nothing is stored.
4. **Packages:** from the same wheel it builds the `.deb` (amd64, arm64) and `.rpm` (x86_64, aarch64) and installs them offline in Debian, Ubuntu, Fedora and Rocky Linux containers.
5. **Release:** once PyPI, the image and the packages succeeded, it creates the GitHub release `vX.Y.Z` with `releases/X.Y.Z.md` as the body, a line with the image and its digest, and the wheel, the sdist and the four packages attached.

Image and packages run next to the PyPI upload, so a failure in either can leave a version on PyPI without a GitHub release. When the failure is transient (a registry or mirror that did not answer), open the failed run and use **Re-run failed jobs**: the PyPI upload is not repeated, and the release job runs once everything is green. A re-run uses the tagged commit, so when the cause is in that code, fix it on `master` and release the next patch version. Never move or re-push a tag.

Only plain `vX.Y.Z` tags trigger it. A tag such as `v0.7.39-fix1` is not a PyPI version and is ignored.

### 7. Check it and open the next cycle

```bash
python3.11 -m venv /tmp/kb4it-check && /tmp/kb4it-check/bin/pip install --no-cache-dir KB4IT==X.Y.Z
/tmp/kb4it-check/bin/kb4it --version    # first line exactly "KB4IT X.Y.Z", second the tagged commit
PATH=/tmp/kb4it-check/bin:$PATH python3 scripts/devel/smoke_build.py --doctor --all-apps
docker run --rm ghcr.io/t00m/kb4it:X.Y.Z --version
docker run --rm ghcr.io/t00m/kb4it:X.Y.Z doctor
scripts/release.sh --open 0.8.0         # commits "chore: target version 0.8.0"
```

`smoke_build.py --doctor --all-apps` runs `kb4it doctor` and then creates and builds every sample app of every theme from the installed package, so a theme that does not load after installation shows here.

### 8. GitHub Marketplace (optional, each release)

The repository is also a GitHub Action (`action.yml`). To list a release on the Marketplace, open the release on GitHub, **Edit**, tick **Publish this Action to the GitHub Marketplace**, pick the categories (Continuous integration, Publishing) and save. The first time, GitHub asks you to accept the Marketplace developer agreement. The action's `name` must be unique on the Marketplace; if `KB4IT site build` is ever taken, change `name` in `action.yml`.

Users pin the action by its release tag (`t00m/KB4IT@vX.Y.Z`). There is no moving major tag such as `v0`: do not create one.

## One-time setup

The workflow needs a few things it cannot set up itself:

- On pypi.org: KB4IT, Settings, Publishing, add a GitHub Actions publisher with owner `t00m`, repository `KB4IT`, workflow `publish.yml` and environment `pypi`.
- On GitHub: Settings, Environments, an environment named `pypi`; then enable the workflow with `gh workflow enable publish.yml`.
- After the first release that pushes the image: on GitHub, your profile, **Packages**, `kb4it`, **Package settings**: under **Danger Zone** change the visibility to **Public**, so anyone can pull it. Check that the package is linked to the KB4IT repository (the image's `source` label normally links it; if not, use **Connect repository**). New packages start private, so until this is done `docker pull ghcr.io/t00m/kb4it` fails for everyone else.

If the workflow cannot be used, `scripts/distribution/pypi/publish_pypi.sh` uploads by hand. Run it in a clean clone of the tag (`git clone --branch vX.Y.Z https://github.com/t00m/KB4IT`): never in a working tree, which may hold themes that are not tracked, and never in an export, which has no git and so no build stamp. The script refuses to run outside a git clone and checks that the wheel carries the release stamp.

## Keeping this document current

This describes real scripts. When `release.sh`, `changelog.py`, `check_themes.py`, `check_wheel_themes.py`, `stamp_build.py`, `smoke_build.py` or the publish workflow change, change this file in the same commit. A release document that is wrong is worse than none: it gets followed.
