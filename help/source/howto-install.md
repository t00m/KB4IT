---
DocType: How-to guide
Feature: Installation
HelpId: install
Keyword: pip, pipx, uv, upgrade, uninstall, requirements
Level: basic
Order: 130
Section: Get started
Summary: Install KB4IT with uv, pipx or pip, upgrade it, remove it, or run it from a clone.
---

# Install KB4IT

## Before you start {#requirements}

- GNU/Linux (tested on Debian, Ubuntu and Fedora).
- Python 3.11 or newer: check with `python3 --version`.

Everything else KB4IT needs (Mako, Markdown, PyYAML, lxml, Rich and Textual) is installed with it.

## Install with uv {#uv}

[uv](https://docs.astral.sh/uv/) installs KB4IT in its own environment and puts the `kb4it` command on your path.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # only if you do not have uv yet
uv tool install KB4IT
```

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

Your knowledge bases are not touched. KB4IT's own data (the list of projects, your custom themes and logs) is in `~/.kb4it/`; delete that folder too if you want nothing left.

## Run the latest code {#source}

To try changes that are not released yet:

```bash
git clone https://github.com/t00m/KB4IT
cd KB4IT
uv tool install . --force
```

`kb4it --version` then adds the git commit, for example `KB4IT 0.8.0 (v0.7.10-12-gd925c10)`.
