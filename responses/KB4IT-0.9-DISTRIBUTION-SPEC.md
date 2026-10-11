---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-11
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT, Docker, Podman, GitHub Actions
Scope: Development
Status: Draft
Tag: specification, distribution, packaging, container
Topic: Installation, Documentation
---

# KB4IT 0.9 distribution specification: packaging scripts, container image and GitHub Action

## Overview

KB4IT is published to PyPI by `.github/workflows/publish.yml` on every `vX.Y.Z` tag. The other channels in `scripts/distribution/` (`.deb`, `.rpm`, Docker, tarball, pipx helper) exist but cannot run as committed, and nothing in CI builds them.

This specification covers three pieces of work:

1. **DS**: repair the packaging scripts and keep them working with a CI job.
2. **GI**: publish a multi-architecture container image to the GitHub Container Registry (GHCR) on every release.
3. **GA**: ship a GitHub Action, so a site can be built on GitHub with one `uses:` line.

The base is the 0.9 series (`kb4it-0.9-series.zip`, 46 patches on `d026df3`). This document is delivered as patch 0047; the implementation will follow the same review cycle as 0.9 (spec, plan, patch series).

### Findings this specification fixes

| # | Where | Problem | Effect |
|---|---|---|---|
| F1 | `build_all.sh`, `deb/build_deb.sh`, `pypi/publish_*.sh`, `pipx/install_pipx.sh` | Call `scripts/distribution/build/build_python.sh`, which does not exist | The `.deb`, the manual PyPI fallback and `install_pipx.sh wheel` fail |
| F2 | `docker/Dockerfile` | `COPY ... Changelog ...`; the file is `CHANGELOG.md` | `docker build` fails |
| F3 | `rpm/kb4it.spec` | `%doc ... Changelog ...` | `rpmbuild` fails on the missing file |
| F4 | `rpm/kb4it.spec` `%install` | Runs `pip install --user build` and builds the wheel inside `rpmbuild` | Needs network at build time, writes to the builder's home, builds a second, different wheel |
| F5 | `rpm/kb4it.spec` | `Requires: python3 >= 3.11` | Cannot install on RHEL 9 / Rocky / Alma 9, whose `python3` is 3.9 although `python3.11` and `python3.12` are available |
| F6 | `.deb` and `.rpm` post-install scripts | `pip install` of the wheel downloads every dependency from PyPI during installation | Installation fails without internet or behind a proxy; versions are not fixed |
| F7 | Package descriptions | List a "book" theme that no longer exists; miss bookshelf and apphelp | Wrong package metadata |
| F8 | `install/local/install_kb4it_from_source.sh` | Header lists asciidoctor/coderay; requires `/usr/bin/python3.*` | Misleading; fails on macOS and where Python is not in `/usr/bin`, although uv needs no system Python |
| F9 | `uninstall/local/uninstall.sh` | Holds an unused install routine with `pip --trusted-host` (turns off certificate checks for PyPI) and `--break-system-packages`; uninstalls with `pip` only | Dead code that teaches an unsafe pattern; KB4IT installed with uv or pipx is not removed |
| F10 | `docker/Dockerfile` | Builds its own wheel; base `python:3.12-slim`; image never published | The image is not the artifact on PyPI; 3.12 is not in the CI matrix; nobody can pull it |
| F11 | CI | No job builds any of these | They broke silently and will again |

## Conventions

Same as the 0.9 specification: one-line Conventional Commits without trailers, tests and docs and CHANGELOG entry in the same commit, `[<COMPONENT>] EVENT key=value` logging, no em dashes. Shell scripts start with `set -euo pipefail`, locate the repository root themselves, read the version from `kb4it/VERSION`, and write only to `<repo>/dist/`. GitHub Actions are pinned to a full version, as the existing workflows do (`setup-uv@v10.2.0`); the versions are checked against the current releases when the plan is written.

## Part 1: packaging scripts (DS)

### DS-01 Python build script

**Requirement.** New `scripts/distribution/build/build_python.sh`:

- Removes earlier `dist/*.whl` and `dist/*.tar.gz` of KB4IT, so later steps never pick a stale wheel.
- Builds the sdist and wheel with `uv build` when uv is installed, otherwise `python3 -m build`.
- Prints the paths of the two files it made.

Every script that needs a wheel calls it only when `dist/` holds no wheel for the current version.

**Acceptance.** `build_python.sh` leaves exactly `dist/kb4it-<version>-py3-none-any.whl` and `dist/kb4it-<version>.tar.gz`; `check_wheel_themes.py` passes on it.

### DS-02 File names and descriptions

**Requirement.**

- `Changelog` becomes `CHANGELOG.md` in the `.deb` docs, the `.rpm` `%doc` line and anything the container image copies (F2, F3).
- Package descriptions (`.deb` control file, `.rpm` `%description`, container labels) use one text: "KB4IT turns a folder of Markdown files with YAML frontmatter into a static website you can browse by any property. Themes: techdoc, blog, bookshelf, apphelp." (F7)
- `install_kb4it_from_source.sh`: the header lists the real requirements (uv or pipx; Python 3.11+ only when pipx is used). The `/usr/bin/python3.*` lookup is used only on the pipx path, and falls back to `python3` on `PATH` (F8).

### DS-03 RPM package

**Requirement.**

- The spec no longer builds the wheel. `build_rpm.sh` calls DS-01 and passes the wheel to `rpmbuild` as `Source1`; `%install` copies it. `%install` does not touch the network (F4).
- Python requirement as a boolean dependency, supported by RPM 4.13 and later (RHEL 8+, Fedora):
  `Requires: (python3 >= 3.11 or python3.11 or python3.12 or python3.13)` (F5).
- `%post` picks the first of `python3.13`, `python3.12`, `python3.11`, `python3` that exists and is at least 3.11, and creates the virtual environment with it. It logs which one it used.
- The package installs the dependency wheels too (DS-05), so `%post` needs no network.

**Acceptance.** The `.rpm` builds in a `fedora:latest` container and in a `rockylinux:9` container (with `python3.11` installed), installs with `dnf`, and `kb4it --version` and a smoke build of the techdoc sample run in both, with networking turned off for the install step.

### DS-04 Debian package

**Requirement.**

- `build_deb.sh` calls DS-01 when no wheel exists (F1) and ships the dependency wheels (DS-05).
- `Depends: python3 (>= 3.11), python3-venv` stays; Debian 12 and Ubuntu 24.04 meet it.
- `postinst` installs from the shipped wheels only (`pip install --no-index --find-links`), so it needs no network.

**Acceptance.** The `.deb` builds on `ubuntu-latest`, installs with `apt install ./kb4it_<v>_all.deb` in `debian:bookworm` and `ubuntu:24.04` containers, and `kb4it --version` and a smoke build run, with networking off for the install step.

### DS-05 Offline installation for .deb and .rpm

**Requirement.** At package build time, `pip download` fetches the wheels of KB4IT's dependencies for the target platform into `/opt/kb4it/wheels/`. `lxml` has compiled wheels, so the packages become architecture-specific:

| Package | Architectures built |
|---|---|
| `.deb` | `amd64`, `arm64` |
| `.rpm` | `x86_64`, `aarch64` |

The Python versions covered are the ones the target distributions ship: 3.11, 3.12, 3.13 (one wheel per version where a dependency has compiled wheels).

**Alternative** (see Decision D-2): keep `Architecture: all` / `noarch` and the online install, and document that installation needs access to PyPI.

### DS-06 Uninstall script

**Requirement.** `uninstall/local/uninstall.sh` is rewritten:

- The unused `detect_distro` function, with `--trusted-host` and `--break-system-packages`, is removed (F9).
- It removes KB4IT installed by `uv tool`, by `pipx`, or by `pip --user`, whichever it finds, and says which.
- It never deletes `~/.kb4it` unless called with `--purge`, and then asks first.

### DS-07 Container build script

**Requirement.** `docker/build.sh` keeps its interface (`IMAGE_NAME`, `IMAGE_REGISTRY`, docker or podman) and builds with the Dockerfile of GI-01, calling DS-01 first when needed. `PYTHON_VERSION` defaults to `3.13`.

### DS-08 CI job for packages

**Requirement.** New job `packages` in `.github/workflows/kb4it.yml`, on `ubuntu-latest`, on every push and pull request:

1. `build_python.sh`, `tarball/build_tarball.sh`.
2. `.deb`: build, then install and smoke test in `debian:bookworm` (networking off for the install).
3. `.rpm`: build and smoke test inside `fedora:latest` and `rockylinux:9`.
4. Container: `docker/build.sh`, then `docker run kb4it:latest --version` and a create-and-build of the techdoc sample inside the container.

The job uploads the built `.deb`, `.rpm` and tarball as workflow artifacts, kept 7 days, so a reviewer can try them.

**Acceptance.** The job is green on the commit that adds it, and turns red if any script of F1 to F3 is broken again (checked by reverting DS-01 locally).

### DS-09 Documentation of the scripts

**Requirement.** `scripts/distribution/README.md` describes what each script produces, what it needs (dpkg-deb, rpmbuild, docker or podman), that the packages are Linux-only, and that releases go through `publish.yml`. The help page `howto-install.md` gets a section "Linux packages" pointing to the `.deb` and `.rpm` attached to each GitHub release (GI-04).

## Part 2: container image on GHCR (GI)

### GI-01 Dockerfile

**Requirement.** `scripts/distribution/docker/Dockerfile` is replaced:

- One stage on `python:${PYTHON_VERSION}-slim`, default `3.13`.
- Installs the wheel from `dist/` (the same file uploaded to PyPI), with the `extras` (PyMdown Extensions) (Decision D-4).
- Runs as a non-root user `kb4it` (UID 1000) by default.
- `ENV KB4IT_HOME=/tmp/kb4it`, so the image also works with `--user "$(id -u):$(id -g)"`, which keeps generated files owned by the person running it.
- `WORKDIR /work`, `EXPOSE 8642`, `ENTRYPOINT ["kb4it"]`, `CMD ["--help"]`.
- OCI labels: title, description (DS-02), version, revision (git commit), source `https://github.com/t00m/KB4IT`, licenses `GPL-3.0-or-later`, documentation URL.
- A `.dockerignore` limits the build context to `dist/` and the Dockerfile.

**Usage the image supports:**

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" ghcr.io/t00m/kb4it:0.9.0 build config/repo.json
docker run --rm -p 8642:8642 -v "$PWD:/work" ghcr.io/t00m/kb4it:0.9.0 serve config/repo.json --host 0.0.0.0
podman run --rm -v "$PWD:/work:Z" ghcr.io/t00m/kb4it:0.9.0 build config/repo.json
```

**Acceptance.** The three commands work in the CI smoke test (`serve` checked with one HTTP request); the image size is reported in the job summary; files written with `--user` belong to the runner user.

### GI-02 Publishing on release

**Requirement.** New job `image` in `.github/workflows/publish.yml`:

- Runs after `check`, using the same `dist` artifact; it does not rebuild the wheel.
- Permissions: `contents: read`, `packages: write`, `id-token: write` and `attestations: write` (for GI-03).
- Logs in to `ghcr.io` with the workflow's `GITHUB_TOKEN`; no stored secret.
- Builds for `linux/amd64` and `linux/arm64` with QEMU and Buildx.
- Before pushing, loads the `amd64` image and runs `kb4it --version`; the version printed must equal the tag.
- Tags: `X.Y.Z`, `X.Y` and `latest` (Decision D-3 for an `edge` tag from `master`).
- The `release` job waits for both `publish` and `image`, so a GitHub release never announces an image that failed.

**Acceptance.** A dry run on a fork with a test tag pushes `ghcr.io/<fork>/kb4it` with the three tags and both architectures (`docker buildx imagetools inspect`).

### GI-03 Supply chain

**Requirement.** The image gets a build provenance attestation (`actions/attest-build-provenance`) and an SBOM from Buildx. The GitHub release notes link to the image with the exact digest.

### GI-04 Packages on the GitHub release

**Requirement.** The `release` job also attaches the `.deb` and `.rpm` (both architectures, DS-05) built by a new `packages` job in `publish.yml`, which reuses the DS-08 steps.

### GI-05 One-time setup and documentation

**Requirement.**

- `RELEASING.md` and `dev-release.md` explain the one-time steps the first release needs: after the first push, set the package `kb4it` on GitHub to **Public** and link it to the repository (the `source` label usually links it).
- `howto-install.md` gets a section "Run in a container" with the commands of GI-01, including Podman with `:Z` for SELinux hosts (RHEL, Fedora).
- `README.md` Installation gets a short "Container" block.

## Part 3: GitHub Action (GA)

### GA-01 The action

**Requirement.** A composite action in `action.yml` at the repository root, usable as `uses: t00m/KB4IT@v0.9.0`.

| Input | Default | Meaning |
|---|---|---|
| `config` | (required) | Path of `repo.json` |
| `version` | (empty) | KB4IT version to install from PyPI. Empty: install the KB4IT of the action's own commit (`github.action_path`), so `@v0.9.0` means KB4IT 0.9.0 |
| `python-version` | `3.13` | Python for KB4IT |
| `extras` | `false` | Install `KB4IT[extras]` |
| `verify` | `true` | Run `kb4it verify` before building; problems fail the step |
| `force` | `false` | Build with `--force` |

| Output | Meaning |
|---|---|
| `target` | Absolute path of the built site, resolved like KB4IT does (relative to the repository root, the parent of `config/`) |
| `version` | KB4IT version that built it |

**Behaviour.** Steps run with `shell: bash` on every runner (Linux, macOS, Windows). It installs uv with the pinned `setup-uv`, installs KB4IT with `uv tool install`, runs `verify` and `build`, and writes a job summary: KB4IT version, documents, compiled, invalid, and the `SUMMARY` line of the build. It never deploys; publishing stays with `actions/upload-pages-artifact` and `actions/deploy-pages`.

**Example the docs show:**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - id: kb4it
        uses: t00m/KB4IT@v0.9.0
        with:
          config: config/repo.json
      - uses: actions/upload-pages-artifact@v5
        with:
          path: ${{ steps.kb4it.outputs.target }}
```

### GA-02 Tests

**Requirement.** New workflow `.github/workflows/action.yml`, on changes to `action.yml`, `kb4it/**` or itself, matrix Linux, macOS, Windows:

1. `kb4it create techdoc` a sample with the installed KB4IT of the commit.
2. `uses: ./` with `config` pointing at it.
3. Check that `outputs.target` points at a folder with `index.html`, and that `outputs.version` equals `kb4it/VERSION`.
4. A second job checks that a broken document fails the step when `verify` is `true`.

### GA-03 Dogfooding

**Requirement.** `.github/workflows/help.yml` builds the help site with `uses: ./` instead of its own install and build steps (Decision D-6).

### GA-04 Documentation

**Requirement.**

- `howto-publish-github-pages.md` uses the action in its workflow, and keeps the manual steps as an alternative.
- A new reference section in `reference-command-line.md` or a new page `reference-github-action.md` lists the inputs and outputs.
- `README.md` "Live demos" or "Installation" mentions the action in one line.
- Listing on the GitHub Marketplace is a manual choice when publishing a release; `RELEASING.md` says how (Decision D-5).

## Compatibility

- No change to KB4IT itself, to `repo.json` or to the output.
- The `.deb` and `.rpm` change architecture from `all`/`noarch` to per-architecture if D-2 keeps the recommendation.
- `publish.yml` gains jobs; a release fails if the image or the packages fail, before anything reaches the GitHub release. PyPI upload still happens first (the order is unchanged), so a failure in `image` after PyPI leaves a PyPI release without a GitHub release; `RELEASING.md` explains how to re-run the failed job.

## Decisions for review

| # | Decision | Recommendation | Alternative |
|---|---|---|---|
| D-1 | Release vehicle | Part of 0.9.0, before the first tag, so 0.9.0 is the first release with an image and an action | A 0.9.1 release afterwards |
| D-2 | `.deb`/`.rpm` dependencies | Ship dependency wheels, per architecture; installs offline | Keep `all`/`noarch` and online install, document the network need |
| D-3 | `edge` image from `master` | No; only release tags | Push `edge` on every merge to `master` |
| D-4 | Extras in the image | Yes, image includes PyMdown Extensions | Plain KB4IT; users build their own image for extras |
| D-5 | GitHub Marketplace | List the action from 0.9.0 | Do not list; usable by `uses:` anyway |
| D-6 | Help site builds with the action | Yes (`uses: ./`) | Keep the current steps |
| D-7 | Moving major tag (`v0`) for the action | No; users pin `vX.Y.Z` or a commit | Maintain a moving `v0` tag |
| D-8 | RHEL 9 support in the `.rpm` | Yes, through `python3.11`/`python3.12` | Fedora and RHEL 10 only |

## Testing summary

| Check | Where |
|---|---|
| Unit-style checks of the shell scripts (`bash -n`, `shellcheck`) | CI `packages` job |
| `.deb` install in Debian 12 and Ubuntu 24.04, offline | CI `packages` job (containers) |
| `.rpm` install in Fedora and Rocky Linux 9, offline | CI `packages` job (containers) |
| Container: version, build, serve, `--user` ownership, both architectures | CI `packages` job; `publish.yml` before push |
| Action on Linux, macOS and Windows; failing `verify` | `action.yml` workflow |
| Release dry run on a fork | Manual, once, documented in the plan |

What I can run here before delivering: the scripts, `shellcheck`, the `.deb` build and install in a container if the session allows containers, and the action steps as plain shell. The multi-architecture build, GHCR push, attestation and the action on macOS and Windows can only be verified by CI on GitHub.

## Related Topics

- `responses/KB4IT-0.9-SPEC.md`, `responses/KB4IT-0.9-PLAN.md`: the 0.9 work this builds on.
- `RELEASING.md`, `.github/workflows/publish.yml`: the release process this extends.
