# KB4IT distribution scripts

This directory builds KB4IT for the channels other than PyPI. All scripts:

- are safe to re-run
- write their outputs to `<repo>/dist/` (or `KB4IT_DIST_OUT`)
- read the version from `kb4it/VERSION`
- can be run from anywhere (they locate the repo root themselves)
- share their settings in `lib/common.sh`: the package description, the Python
  versions the Linux packages support (3.11 to 3.14), and the helpers that build
  the wheel only when `dist/` has none for the current version

The `.deb`, `.rpm` and container image are Linux-only; the scripts run on any
GNU/Linux host with the tools listed below.

## Layout

| Directory | Produces | Script | Needs |
|---|---|---|---|
| `build/` | sdist + wheel | `build_python.sh` | uv (or `python3 -m build`) |
| `wheels/` | dependency wheels for one architecture | `download_wheels.sh ARCH` | uv or pip, network |
| `deb/` | `kb4it_<v>_<arch>.deb` (amd64, arm64) | `build_deb.sh [ARCH]` | `dpkg-deb` |
| `rpm/` | `kb4it-<v>-<r>.<arch>.rpm` (x86_64, aarch64) | `build_rpm.sh [ARCH]` + `kb4it.spec` | `rpmbuild` (`rpm-build` on Fedora/RHEL, `rpm` on Debian/Ubuntu) |
| `docker/` | OCI image `kb4it:<v>` and `kb4it:latest` | `build.sh` + `Dockerfile`; `smoke.sh IMAGE` tests it | docker or podman |
| `tarball/` | source `.tar.gz` + `.zip` + SHA-256 | `build_tarball.sh` | git or tar |
| `pypi/` | upload to PyPI / TestPyPI | `publish_pypi.sh`, `publish_testpypi.sh` | twine, an API token |
| `pipx/` | pipx install from source, wheel or PyPI | `install_pipx.sh` | pipx |
| `test/` | offline install tests of the `.deb` and `.rpm` | `test_packages.sh [deb, rpm or all]` | docker or podman |
| _(root)_ | every format the host supports | `build_all.sh` | |

`ARCH` defaults to the architecture of the machine; both architectures build on
either machine, because the packages carry wheels and compile nothing.

## Releases

Releases are not made from here. `scripts/release.sh` prepares a release, and the
publish workflow (`.github/workflows/publish.yml`) builds and uploads it from a
`vX.Y.Z` tag: the wheel to PyPI, the container image to GHCR, and the `.deb`,
`.rpm` and wheel to the GitHub release. See `RELEASING.md`. `pypi/publish_*.sh`
remain as a manual fallback for the PyPI step.

The CI job `packages` in `.github/workflows/kb4it.yml` runs these scripts on every
push and pull request, so they cannot break silently.

## Per-channel notes

### .deb / .rpm

Both packages carry the KB4IT wheel and the wheels of its dependencies for Python
3.11 to 3.14 (lxml, PyYAML and MarkupSafe have compiled code, so the packages are
per architecture). The post-install script creates `/opt/kb4it/venv` from those
wheels without network access and links `/usr/bin/kb4it`. Removing the package
removes `/opt/kb4it` completely.

- `.deb`: needs `python3 (>= 3.11)` and `python3-venv` (Debian 12, Ubuntu 24.04 and newer).
- `.rpm`: needs a Python from 3.11 to 3.14 as `python3` or as `python3.11` to
  `python3.14`, so it installs on RHEL 9 and its rebuilds next to their Python 3.9.
  `%post` uses the newest supported one and logs which.

Test both offline in containers with `test/test_packages.sh`;
`KB4IT_PKGTEST_DEB_IMAGES` and `KB4IT_PKGTEST_RPM_IMAGES` change the images.

### Container image

`python:3.13-slim` with the release wheel and its extras (PyMdown Extensions),
running as the non-root user `kb4it` (UID 1000) in `/work`:

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" kb4it:latest build config/repo.json
docker run --rm -p 8642:8642 -v "$PWD:/work" kb4it:latest serve config/repo.json --host 0.0.0.0
podman run --rm -v "$PWD:/work:Z" kb4it:latest build config/repo.json
```

The build context is `dist/image/`, which holds only the wheel. Released images are
published as `ghcr.io/t00m/kb4it`.

### Source tarball

`tarball/build_tarball.sh` runs `git archive HEAD` so it only includes tracked
files. A `.zip` and SHA-256 sums are produced alongside the `.tar.gz`.
