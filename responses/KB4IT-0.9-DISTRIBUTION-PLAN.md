---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-12
DocType: How-to guide
OS: Linux, macOS, Windows
Product: KB4IT, Docker, Podman, GitHub Actions
Scope: Development
Status: Draft
Tag: implementation-plan, distribution, packaging, container
Topic: Installation, Development
---

# KB4IT 0.9 distribution implementation plan

## Problem

`responses/KB4IT-0.9-DISTRIBUTION-SPEC.md` (approved 2026-10-12, recommended answer for D-1 to D-8) defines 18 requirements in three parts: packaging scripts (DS), container image on GHCR (GI) and GitHub Action (GA). This plan turns them into an ordered series of commits, delivered the same way as 0.9: a zipped `git am` series on top of the 46 patches already delivered.

## Prerequisites

- Base: the 0.9 series (patches 0001 to 0046, last commit `f398dc1`), then patch 0047 (the specification).
- Working branch here: `ccr-271d5ff1-h0hh01`. It now also holds the specification and its approval (patches 0047 and 0048).
- Tools in this environment, checked on 2026-10-12:
    - Python, `uv`, `git`, `dpkg-deb`.
    - Docker 29 with Buildx; containers run, and `--network none` works, so the offline installs can be tested here.
    - Images pulled successfully: `debian:bookworm-slim`, `fedora:latest`, `rockylinux:9`.
    - Not installed: `rpmbuild` (used inside a Fedora container instead), `shellcheck` (run through the `shellcheck-py` package with `uvx`), QEMU (no arm64 test runs here).
- Your side: the same as for 0.9 (a clone, `git am`, a pushed branch for CI). For the release itself: the one-time GHCR step of GI-05.

### Action versions

Latest releases on 2026-10-12, read with `git ls-remote --tags`. The new workflow steps pin them; the existing pins stay as they are.

| Action | Version |
|---|---|
| `docker/setup-qemu-action` | `v4.4.0` |
| `docker/setup-buildx-action` | `v4.4.1` |
| `docker/login-action` | `v4.6.0` |
| `docker/metadata-action` | `v6.2.0` |
| `docker/build-push-action` | `v7.4.0` |
| `actions/attest-build-provenance` | `v4.2.2` |
| `astral-sh/setup-uv` | `v10.2.0` (as in the existing workflows; `v10.3.0` exists, upgrading is a separate change) |

## Procedure

### Working rules for every commit

Same as the 0.9 plan:

1. One commit per requirement or clean part of one. One-line Conventional Commits message, no trailers; requirement ID in the CHANGELOG entry.
2. Each commit holds its scripts, tests, help pages and `CHANGELOG.md` entry under `## [Unreleased]`.
3. Before each commit:
    - `./scripts/devel/test.sh` passes.
    - `bash -n` and `shellcheck` pass on every script the commit touches.
    - `kb4it verify help/config/repo.json` passes when a help page changed.
    - For package and image commits, the matching container test below passes here.
4. No change to `kb4it/` itself (spec: Compatibility). If one becomes necessary, I stop and ask.
5. No em dashes.

### Design choices inside the spec

These follow the spec but fix details it leaves open.

| Topic | Choice |
|---|---|
| Shared shell code | New `scripts/distribution/lib/common.sh`, sourced by every script. It holds the repository root, the version, `ensure_wheel` (calls DS-01 only when `dist/` has no wheel for the current version), the package description of DS-02 and the Python version list. One place for the text and the logic the spec asks to keep in step. |
| Dependency wheels (DS-05) | New `scripts/distribution/wheels/download_wheels.sh ARCH`. It runs `pip download --only-binary=:all:` for Python 3.11, 3.12 and 3.13 and the manylinux platform tags of ARCH, from `requirements.txt` (kept equal to `pyproject.toml` by the 0.9 test FX-03). Output: `dist/wheels/<arch>/`. Tried here: about 8.5 MB per Python version, all dependencies have binary wheels for both architectures. |
| Building both architectures on one machine | Nothing is compiled; a package only carries wheel files. `dpkg-deb` takes the architecture from the control file, and `rpmbuild --target aarch64` packages the aarch64 wheels. No QEMU needed to build. |
| `postinst` and `%post` | Remove an earlier `/opt/kb4it/venv`, create it with the chosen Python, then `pip install --no-index --find-links /opt/kb4it/wheels kb4it`. The `pip install --upgrade pip` line goes, since it needs the network. The `.rpm` keeps the name of the Python it chose in `/opt/kb4it/python`, so an upgrade logs a change of interpreter. |
| Container build context (GI-01) | `build.sh` and `publish.yml` copy the release wheel into `dist/image/` and use that folder as the build context. The context then holds one file, which meets the intent of the `.dockerignore` in GI-01 without a `.dockerignore` at the repository root that would affect every other `docker build`. |
| Container tests | New `scripts/distribution/docker/smoke.sh IMAGE`: `--version`, create and build the techdoc sample with `--user "$(id -u):$(id -g)"` and check file ownership, `serve` with one HTTP request. Used here, in `kb4it.yml` and in `publish.yml` before the push. |
| Package tests | New `scripts/distribution/test/test_packages.sh`: builds the `.deb` and installs it in `debian:bookworm` and `ubuntu:24.04`; builds the `.rpm` inside `fedora:latest` and installs it in `fedora:latest` and `rockylinux:9`. Each target image first gets its Python (`python3-venv`; `python3.11` on Rocky) in a prepared layer; the install itself and the smoke build run with `--network none`. The same script runs here and in CI. |
| Action summary (GA-01) | The action reads the `[WORKFLOW] SUMMARY docs_total=... compiled=... skipped=... invalid=...` line that `kb4it build` already prints, and the `--version` output. The `target` output is resolved with a short Python step, the same rule as `resolve_repo_path`. No change to KB4IT. |
| Action name for the Marketplace (D-5) | `name: "KB4IT site build"`, with `branding` (icon `book-open`, colour `blue`). The Marketplace requires an `action.yml` at the root and a unique `name`; it does not forbid other workflows in the repository. The name is checked for uniqueness when you publish; `RELEASING.md` says what to do if it is taken. |

### Commit series

The numbers continue the 0.9 series. Counts are estimates.

#### Phase A: documents

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 47 | `docs: add specification for distribution scripts, container image and github action` | | `responses/KB4IT-0.9-DISTRIBUTION-SPEC.md` | (already delivered) |
| 48 | `docs: approve the distribution specification` | | same | (done) |
| 49 | `docs: add implementation plan for distribution` | | `responses/KB4IT-0.9-DISTRIBUTION-PLAN.md` | |

#### Phase B: packaging scripts

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 50 | `build(dist): add the python build script and shared helpers` | DS-01 | new `build/build_python.sh`, new `lib/common.sh`; `build_all.sh`, `pypi/publish_*.sh`, `pipx/install_pipx.sh` use them | new `tests/dist/test_scripts.py`: `bash -n` on every script; every script a script calls exists (catches F1 again); `build_python.sh` leaves exactly the wheel and the sdist, and `check_wheel_themes.py` passes |
| 51 | `fix(dist): use CHANGELOG.md and one package description` | DS-02 (F2, F3, F7) | `deb/build_deb.sh`, `rpm/kb4it.spec`, `docker/Dockerfile` | no script names `Changelog`; every description equals the one in `common.sh` |
| 52 | `fix(install): list the real requirements of the source installer` | DS-02 (F8) | `scripts/install/local/install_kb4it_from_source.sh` | runs with uv and no `/usr/bin/python3.*` (fake `PATH`) |
| 53 | `build(dist): download dependency wheels for offline installs` | DS-05 | new `wheels/download_wheels.sh` | every requirement has a wheel for 3.11, 3.12 and 3.13 on both architectures |
| 54 | `fix(deb): build per architecture and install offline` | DS-04 | `deb/build_deb.sh` | `test_packages.sh deb`: Debian 12 and Ubuntu 24.04, `--network none`, `kb4it --version` and a smoke build; remove and purge leave no `/opt/kb4it/venv` |
| 55 | `fix(rpm): package the release wheel and support rhel 9` | DS-03, D-8 | `rpm/build_rpm.sh`, `rpm/kb4it.spec` | `test_packages.sh rpm`: Fedora and Rocky Linux 9, offline; `%post` log names the Python it chose; `rpm -e` removes the venv |
| 56 | `fix(uninstall): remove uv, pipx and pip installs` | DS-06 (F9) | `scripts/uninstall/local/uninstall.sh` | fake `uv`, `pipx`, `pip` on `PATH`: the right one is called; `~/.kb4it` kept without `--purge` |
| 57 | `build(docker): install the release wheel in a non-root image` | GI-01, DS-07, D-4 | `docker/Dockerfile`, `docker/build.sh`, new `docker/smoke.sh` | `smoke.sh kb4it:latest` here: version, `--user` ownership, `serve` answers; Podman command checked in CI only |
| 58 | `ci: build and test the packages and the container image` | DS-08 | `.github/workflows/kb4it.yml`, new `test/test_packages.sh` | the new `packages` job; artifacts kept 7 days |
| 59 | `docs(dist): describe the distribution scripts` | DS-09 | `scripts/distribution/README.md`, `help/source/howto-install.md` ("Linux packages") | help verify |

#### Phase C: container image on GHCR

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 60 | `ci(publish): publish the container image to ghcr` | GI-02, GI-03, D-3 | `.github/workflows/publish.yml` (`image` job; `release` waits for it; release notes get the image digest) | `actionlint` here; real run on your release or a fork dry run |
| 61 | `ci(publish): attach deb and rpm packages to the github release` | GI-04 | `publish.yml` (`packages` job reusing `test_packages.sh`) | `actionlint`; the `release` job lists the four package files |
| 62 | `docs: document the container image and the release steps` | GI-05 | `RELEASING.md`, `help/source/dev-release.md`, `help/source/howto-install.md` ("Run in a container"), `README.md` ("Container") | help verify; `tests/core/test_readme.py` still passes |

#### Phase D: GitHub Action

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 63 | `feat(action): add a github action that builds a kb4it site` | GA-01 | new `action.yml` | new `tests/dist/test_action.py`: inputs and outputs as in the spec, every `run` step uses `shell: bash`, pinned versions; the action's shell steps run here against a sample site |
| 64 | `ci: test the github action on linux, macos and windows` | GA-02 | new `.github/workflows/action.yml` | the workflow itself (sample builds; failing `verify` makes the step fail) |
| 65 | `ci(help): build the help site with the kb4it action` | GA-03, D-6 | `.github/workflows/help.yml` | same pages produced as before (`verify`, then `build --force`, Python 3.11) |
| 66 | `docs: document the github action` | GA-04, D-5, D-7 | new `help/source/reference-github-action.md`, `howto-publish-github-pages.md`, `README.md`, `RELEASING.md` (Marketplace, no moving `v0` tag) | help verify; README test |
| 67 | `docs: record implementation notes in the distribution plan` | | this plan | |

D-1 (part of 0.9.0) needs no commit: the work lands before the 0.9.0 release commit, which you make with `scripts/release.sh`.

### Delivery package

`kb4it-0.9-distribution-series.zip`, built the same way as the 0.9 zip:

- `0047-*.patch` to `0067-*.patch`, from `git format-patch f398dc1..HEAD --start-number 47`.
- `README-APPLY.md` and `SERIES.sha256`.

How you apply it, on the branch where the 0.9 series is applied:

```bash
unzip kb4it-0.9-distribution-series.zip -d /tmp/kb4it-dist
git am --3way /tmp/kb4it-dist/*.patch
./scripts/devel/test.sh
git push
```

If you already applied patch 0047 from the spec zip, skip it: `git am --3way /tmp/kb4it-dist/00{48..67}-*.patch`.

### Progress reporting

A short status after each phase. No interim zip unless you ask for one: the parts that only CI can check (Phase C and the action on macOS and Windows) come at the end anyway.

## Verification

| Check | Where | When |
|---|---|---|
| Test suite, `bash -n`, `shellcheck` | Here | Every commit |
| `.deb` offline install, Debian 12 and Ubuntu 24.04, amd64 | Here (Docker) and CI | Commits 54, 58 |
| `.rpm` offline install, Fedora and Rocky Linux 9, x86_64 | Here (Docker) and CI | Commits 55, 58 |
| arm64 `.deb` and aarch64 `.rpm` | Contents checked here (wheels for aarch64 only); install tested only on a real arm64 machine or by you | Commits 54, 55 |
| Container image, amd64 | Here and CI | Commits 57, 58 |
| Workflow syntax | `actionlint` here (through `uvx` or its release binary) | Commits 58, 60, 61, 64, 65 |
| Multi-arch build, GHCR push, attestation, release assets | Your first release, or a dry run with a test tag on a fork | After applying |
| Action on macOS and Windows | CI, `action.yml` workflow | After you push |
| `git am` of the whole series on a clean `d026df3` checkout | Here | Before building the zip |

## Troubleshooting

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `python3.11` on Rocky Linux 9 lacks `ensurepip` or the bundled pip wheel | `%post` cannot create the venv | Test in `rockylinux:9` first (commit 55). If needed, add `Requires: python3.11-pip` through the same boolean dependency, and say so in the implementation notes |
| `rpmbuild --target aarch64` on x86_64 refuses or mislabels the package | No aarch64 `.rpm` | Build inside the Fedora container with `--target aarch64`; if it fails, build the aarch64 package in an arm64 Fedora container under QEMU in CI only |
| Packages grow from about 0.5 MB to about 25 MB (three Python versions of the compiled wheels) | Larger downloads | Accepted with D-2; size reported in the job summary |
| A distribution ships a Python newer than 3.13 | Offline install finds no compiled wheels for it | `%post`/`postinst` stop with a clear message naming the Python versions the package supports; adding a version is one line in `common.sh` |
| The arm64 image build under QEMU is slow | Longer release | Only on release tags (D-3); the cache of Buildx in GitHub Actions (`type=gha`) is used |
| The GHCR package stays private after the first push | `docker pull` fails for users | One-time step documented (GI-05); the release notes link shows the problem at once |
| PyPI upload succeeds and the image job fails | PyPI release without a GitHub release | Order is the spec's; `RELEASING.md` explains re-running the failed job |
| The action name is already taken on the Marketplace | Cannot list it | `RELEASING.md` gives a fallback name; the action still works with `uses:` |

## Open questions

None. The spec decisions cover the choices this plan needed. If one of the risks above forces a change to a requirement, I will ask before making it.
