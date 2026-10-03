---
DocType: How-to guide
Feature: Development
HelpId: dev-setup
Keyword: clone, test, pytest, coverage, check_themes, contribute, pull request
Level: advanced
Order: 720
Section: Development
Summary: Get the source, run KB4IT from it, run the tests and the theme check, and send a change.
---

# Run and test from source

## Get the code {#clone}

```bash
git clone https://github.com/t00m/KB4IT
cd KB4IT
```

You need Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

## Run your working copy {#run}

Install it as your `kb4it` command:

```bash
uv tool install . --force
kb4it --version          # KB4IT 0.8.0 (v0.7.10-12-gd925c10)
```

Run the same command again after each change. `scripts/install/local/install_kb4it_from_source.sh` does the same and falls back to pipx when uv is missing.

## Run the tests {#tests}

```bash
./scripts/devel/test.sh             # everything
./scripts/devel/test.sh -q tests/core/test_cli.py
```

The script runs pytest under Python 3.11 with the exact dependencies, through uv, so nothing is installed in your system. Any pytest option works after it.

The tests run KB4IT on throwaway knowledge bases with their own home folder, so they never touch your `~/.kb4it`.

| Folder | Covers |
|---|---|
| `tests/core/` | The command line, settings, documents, builds, helpers, versions |
| `tests/themes/` | techdoc, blog and bookshelf |
| `tests/apphelp/` | The apphelp theme in detail |
| `tests/tui/` | Every screen of the terminal interface |

## Check the themes {#themes}

```bash
./scripts/devel/check_themes.sh
```

It builds every sample app of every theme tracked in git and fails on any error or warning. CI runs it on every push, and a release cannot be made without it.

## Build this help {#help}

```bash
kb4it build help/config/repo.json
xdg-open help/target/index.html
```

See [Write these pages](dev-help.md).

## Send a change {#contribute}

1. Open an issue first for anything large, so the approach can be agreed.
2. Keep each commit to one change, with a [Conventional Commits](https://www.conventionalcommits.org/) message such as `fix: keep whole sentences in drafted release notes`.
3. Add a line to the `[Unreleased]` section of `CHANGELOG.md`.
4. Make sure the tests and the theme check pass, then open a pull request against `master`.
