---
DocType: How-to guide
Feature: Installation
HelpId: install
Keyword: pip, pipx, uv, deb, rpm, apt, dnf, docker, podman, container, upgrade, uninstall, requirements, windows, macos, linux, wsl, powershell
Level: basic
Order: 130
Section: Get started
Summary: Install KB4IT on Linux, macOS or Windows with uv, pipx, pip, a Linux package or a container, upgrade it, remove it, or run it from a clone.
---

# Install KB4IT

## Before you start {#requirements}

- GNU/Linux, macOS 13 or newer, or Windows 10 or 11.
- Python 3.11 or newer: check with `python3 --version` (on Windows: `py --version`). uv can install Python for you.

Everything else KB4IT needs (Mako, Markdown, PyYAML, lxml, Rich and Textual) is installed with it.

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
sudo dnf install ./kb4it-0.9.0-1.x86_64.rpm
```

The package uses a Python from 3.11 to 3.14. On RHEL 9, whose `python3` is 3.9, dnf installs `python3.11` or `python3.12` next to it. Remove the package with `sudo apt remove kb4it` or `sudo dnf remove kb4it`.

## Run in a container {#container}

The image `ghcr.io/t00m/kb4it` has KB4IT with its extras, for `amd64` and `arm64`, and needs no Python on your machine. Run it from the folder of your knowledge base, which it sees as `/work`:

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" ghcr.io/t00m/kb4it:0.9.0 build config/repo.json
```

`--user` makes the files it writes yours. To preview the site while you write, publish the port and listen on every address inside the container:

```bash
docker run --rm -p 8642:8642 -v "$PWD:/work" ghcr.io/t00m/kb4it:0.9.0 serve config/repo.json --host 0.0.0.0
```

Then open `http://127.0.0.1:8642/`. With Podman, on hosts with SELinux such as Fedora and RHEL, add `:Z` to the folder so the container may read it:

```bash
podman run --rm -v "$PWD:/work:Z" ghcr.io/t00m/kb4it:0.9.0 build config/repo.json
```

Use a fixed version such as `0.9.0`, or `0.9` for its latest fixes; `latest` follows every release.

## Check the installation {#check}

```bash
kb4it --version
kb4it themes
```

`kb4it themes` lists the themes you can use: apphelp, blog, bookshelf and techdoc.

## Upgrade {#upgrade}

```bash
uv tool upgrade KB4IT      # or: pipx upgrade KB4IT, or: pip install --user -U KB4IT
```

After an upgrade the next build of each site compiles everything once, because the pages carry the version that made them.

## Remove {#remove}

```bash
uv tool uninstall KB4IT    # or: pipx uninstall KB4IT, or: pip uninstall KB4IT
```

Your knowledge bases are not touched. KB4IT's own data (the list of projects, your custom themes and logs) is in `~/.kb4it/` (`%USERPROFILE%\.kb4it` on Windows); delete that folder too if you want nothing left.

## Windows Subsystem for Linux {#wsl}

KB4IT runs natively on Windows, so WSL is not needed. If you already work inside WSL, install it there as on Linux; the sites it builds open in any Windows browser.

## Run the latest code {#source}

To try changes that are not released yet:

```bash
git clone https://github.com/t00m/KB4IT
cd KB4IT
uv tool install . --force
```

`kb4it --version` then adds the git commit, for example `KB4IT 0.8.0 (v0.7.10-12-gd925c10)`.
