# KB4IT distribution scripts

This directory contains build scripts that produce KB4IT artefacts for the
main Linux distribution channels. All scripts:

- are idempotent and safe to re-run
- write outputs to `<repo>/dist/`
- read the version from `kb4it/VERSION`
- can be run from anywhere (they locate the repo root themselves)

Make them executable once with `chmod +x scripts/distribution/**/*.sh`.

## Layout

| Directory | Produces | Script |
|---|---|---|
| `build/` | sdist + wheel (PEP 517) | `build_python.sh` |
| `pypi/`  | Upload to PyPI / TestPyPI | `publish_pypi.sh`, `publish_testpypi.sh` |
| `pipx/`  | pipx install from source/wheel/PyPI | `install_pipx.sh` |
| `docker/` | OCI image (docker or podman) | `build.sh` + `Dockerfile` |
| `deb/`   | Debian `.deb` package | `build_deb.sh` |
| `rpm/`   | RPM package | `build_rpm.sh` + `kb4it.spec` |
| `tarball/` | Source tarball + zip + SHA-256 | `build_tarball.sh` |
| _(root)_ | Build every supported format | `build_all.sh` |

## Releases

Releases are not made from here. `scripts/release.sh` prepares a release and
the publish workflow builds and uploads it from a `vX.Y.Z` tag; see
`RELEASING.md` in the repository root. The scripts in this directory build
packages for other channels (deb, rpm, Docker, tarball) from the version in
`kb4it/VERSION`, and `pypi/publish_*.sh` remain as a manual fallback for the
workflow.

## Per-channel notes

### PyPI / pipx
`pip install KB4IT` or `pipx install KB4IT` after the PyPI upload. The wheel
is pure-Python and works on any GNU/Linux with Python ≥ 3.11. No external
binary toolchain is required.

### Docker
Produces a small image based on `python:3.12-slim`. Mount the KB4IT repo
at `/work`:

```bash
docker run --rm -v "$(pwd)/myrepo:/work" kb4it:latest build /work/config/repo.json
```

### .deb / .rpm
Both packages install the wheel into `/opt/kb4it/venv` and expose
`/usr/bin/kb4it` as a symlink. This isolates KB4IT from the distro's
Python site-packages without requiring any system packaging of its
Python dependencies.

### Source tarball
`scripts/distribution/tarball/build_tarball.sh` runs `git archive HEAD` so
it only includes tracked files. A `.zip` and SHA-256 sums are produced
alongside the `.tar.gz` for release uploads.
