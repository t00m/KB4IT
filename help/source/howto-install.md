---
DocType: How-to guide
Feature: Installation
HelpId: install
Keyword: pip, pipx, uv, deb, rpm, apt, dnf, docker, podman, container, upgrade, uninstall, requirements, windows, macos, linux, wsl, powershell, doctor, venv, rhel, commit, build version
Level: basic
Order: 130
Section: Guides
Summary: Install KB4IT on Linux, macOS or Windows with uv, pipx, pip, a Linux package or a container, upgrade it, remove it, or run it from a clone.
---

# Install KB4IT

## Before you start {#requirements}

- GNU/Linux, macOS 13 or newer, or Windows 10 or 11.
- Python 3.11 or newer: check with `python3 --version` (on Windows: `py --version`). uv can install Python for you.

Everything else KB4IT needs (Mako, Markdown, PyYAML, lxml, Pillow, Rich and Textual) is installed with it.

## Install with uv {#uv}

[uv](https://docs.astral.sh/uv/) installs KB4IT in its own environment and puts the `kb4it` command on your path.

On Linux and macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # only if you do not have uv yet (or: brew install uv)
uv tool install KB4IT
```

On Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # only if you do not have uv yet
uv tool install KB4IT
```

Open a new terminal afterwards, so the `kb4it` command is found.

## Install with pipx {#pipx}

```bash
pipx install KB4IT
```

## Install with pip {#pip}

```bash
pip install --user KB4IT
```

!!! tip
    uv and pipx keep KB4IT apart from your other Python packages, so an upgrade of one never breaks the other. Prefer them to pip.

## Install a Linux package {#linux-packages}

Each [GitHub release](https://github.com/t00m/KB4IT/releases) has a `.deb` and an `.rpm` for `x86_64` (`amd64`) and `aarch64` (`arm64`). They install KB4IT in `/opt/kb4it` with everything it needs, so the installation works without internet access, and put `kb4it` in `/usr/bin`.

On Debian 12 or newer and Ubuntu 24.04 or newer:

```bash
sudo apt install ./kb4it_0.9.0_amd64.deb
```

On Fedora, and on RHEL, Rocky Linux and AlmaLinux 9 or newer:

```bash
sudo dnf install ./kb4it-X.Y.Z-1.x86_64.rpm
```

The package uses a Python from 3.11 to 3.14. On RHEL 9, whose `python3` is 3.9, dnf installs `python3.11` or `python3.12` next to it. Remove the package with `sudo apt remove kb4it` or `sudo dnf remove kb4it`.

## Run in a container {#container}

The image `ghcr.io/t00m/kb4it` has KB4IT with its extras, for `amd64` and `arm64`, and needs no Python on your machine. Run it from the folder of your knowledge base, which it sees as `/work`:

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" ghcr.io/t00m/kb4it:X.Y.Z build config/repo.json
```

`--user` makes the files it writes yours. To preview the site while you write, publish the port and listen on every address inside the container:

```bash
docker run --rm -p 8642:8642 -v "$PWD:/work" ghcr.io/t00m/kb4it:X.Y.Z serve config/repo.json --host 0.0.0.0
```

Then open `http://127.0.0.1:8642/`. With rootless Podman, `--userns=keep-id` keeps your user ID inside the container, so it can write to the folder and the files stay yours. On hosts with SELinux, such as Fedora and RHEL, also add `:Z` to the folder so the container may read it:

```bash
podman run --rm --userns=keep-id --user "$(id -u):$(id -g)" -v "$PWD:/work:Z" ghcr.io/t00m/kb4it:X.Y.Z build config/repo.json
```

Use a fixed version such as `X.Y.Z`, or `X.Y` for its latest fixes; `latest` follows every release.

## Check the installation {#check}

```bash
kb4it --version
kb4it doctor
```

`kb4it --version` prints the build and, on a second line, the commit it was built from:

```text
KB4IT X.Y.Z-dev+42.g0a71990
commit 0a71990c... built 2026-10-26T08:12:03Z
```

A release shows only `X.Y.Z`. Any other commit adds `-dev+`, the number of commits since the last release and the commit (`g` and its first 7 characters), plus `.dirty` when it was built with uncommitted changes. `+unknown` means the package carries no build stamp.

`kb4it doctor` adds Python, the folders KB4IT runs from, the offline help and every theme with its version, fingerprint and folder, so it shows when a copy of a theme in `~/.kb4it` hides the bundled one. It ends with `1` and a `PROBLEM` line when a bundled file or theme is missing. Add its output to any bug report.

## Upgrade {#upgrade}

```bash
uv tool upgrade KB4IT      # or: pipx upgrade KB4IT, or: pip install --user -U KB4IT
```

After an upgrade the next build of each site compiles everything once, because the pages carry the build that made them. This also happens when you install another commit of the same version (`KBDICT_BUILD_MISMATCH` in the log).

## Remove {#remove}

```bash
uv tool uninstall KB4IT    # or: pipx uninstall KB4IT, or: pip uninstall KB4IT
```

From a clone, `scripts/uninstall/local/uninstall.sh` removes KB4IT whichever way it was installed: uv, pipx, pip or the virtual environment of the source installer.

Your knowledge bases are not touched. KB4IT's own data (the list of projects, your custom themes and logs) is in `~/.kb4it/` (`%USERPROFILE%\.kb4it` on Windows); delete that folder too if you want nothing left.

## Windows Subsystem for Linux {#wsl}

KB4IT runs natively on Windows, so WSL is not needed. If you already work inside WSL, install it there as on Linux; the sites it builds open in any Windows browser.

## Run the latest code {#source}

To try changes that are not released yet, install from a clone with the source installer. It builds the same wheel as a release, with the offline help and the build stamp, installs that wheel and checks the result:

```bash
git clone https://github.com/t00m/KB4IT
cd KB4IT
scripts/install/local/install_kb4it_from_source.sh
```

It uses uv, else pipx, else a virtual environment. Choose with `--method uv`, `--method pipx` or `--method venv`. No root access is needed for any of them.

| Option | Does |
|---|---|
| `--method venv` | Needs only Python 3.11 or newer: creates `~/.local/share/kb4it/venv` (or `KB4IT_VENV`) and links `~/.local/bin/kb4it` to it |
| `--python PATH` | The Python to use. Without it the newest `python3.14` to `python3.11` on `PATH` is used, never an older `python3` |
| `--allow-dirty` | Builds even with uncommitted changes; the build is marked `.dirty`. Without it the installer stops and lists them |
| `--extras` | Also installs the optional extras (PyMdown Extensions, nh3) |
| `--wheel FILE` | Installs a wheel you already have, such as one from a release, instead of building one |

At the end it runs the new `kb4it --version` and `kb4it doctor`. It ends with `2` when another `kb4it` comes first on `PATH`, and lists them all; remove the old one or reorder `PATH`.

### RHEL 8 and 9 {#rhel}

Their `python3` is too old, but `python3.11` installs next to it:

```bash
sudo dnf install python3.11
scripts/install/local/install_kb4it_from_source.sh --method venv
```

Without uv, the installer needs network access to PyPI to build the wheel and install the dependencies.
