---
DocType: How-to guide
Feature: Development
HelpId: dev-setup
Keyword: clone, test, pytest, coverage, check_themes, contribute, pull request, performance, --trace, profile, cProfile, py-spy
Level: advanced
Order: 720
Section: Reference
Summary: Get the source, run KB4IT from it, run the tests and the theme check, find what makes a build slow, and send a change.
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
kb4it --version          # KB4IT X.Y.Z (vX.Y.Z-12-gd925c10)
```

Run the same command again after each change. `scripts/install/local/install_kb4it_from_source.sh` does the same and falls back to pipx when uv is missing.

## Run the tests {#tests}

```bash
./scripts/devel/test.sh                       # everything
./scripts/devel/test.sh -q tests/core/test_cli.py
./scripts/devel/test.sh --python 3.13         # another Python version
python3 scripts/devel/smoke_build.py --from-source   # create and build every theme's sample app
```

The script runs pytest under Python 3.11 (or the version after `--python`) with the exact dependencies, through uv, so nothing is installed in your system. Any pytest option works after it. On Windows, run it from Git Bash.

CI runs the tests and the smoke build on Linux, macOS and Windows, with Python 3.11, 3.13 and 3.14.

The tests run KB4IT on throwaway knowledge bases with their own home folder, so they never touch your `~/.kb4it`.

| Folder | Covers |
|---|---|
| `tests/core/` | The command line, settings, documents, builds, helpers, versions |
| `tests/themes/` | techdoc, blog and bookshelf |
| `tests/apphelp/` | The apphelp theme in detail |
| `tests/tui/` | Every screen of the terminal interface |
| `tests/serve/` | `kb4it serve`, the local web server and the file watcher |

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

## Find what makes a build slow {#performance}

Start with the trace. It shows which stage or step takes the time:

```bash
kb4it build --trace CONFIG
```

See [Build timings](reference-command-line.md#trace). To see which functions inside a slow step take the time, run a profiler. KB4IT also runs as `python -m kb4it`, which is how both profilers below start it. From the source folder, `uv run` gives them KB4IT and its dependencies:

```bash
RUN="uv run --no-project --with-requirements requirements.txt --with-editable ."
```

cProfile ships with Python. It counts every call, so the build takes about twice as long, and it sees only the main thread, not the threads that compile documents:

```bash
$RUN python -m cProfile -o profile.pstats -m kb4it build CONFIG
$RUN python -c "import pstats; pstats.Stats('profile.pstats').sort_stats('cumulative').print_stats(30)"
```

Sort by `tottime` instead of `cumulative` to see the functions that spend the time themselves, not in what they call.

py-spy samples the running program a few hundred times a second. It slows the build down little, sees every thread and draws a flame graph you open in a browser:

```bash
$RUN --with py-spy py-spy record -o flame.svg -- python -m kb4it build CONFIG
```

On macOS, py-spy needs `sudo`. Profile a build without changes and one after `--force`: they spend their time in different places.

## Send a change {#contribute}

1. Open an issue first for anything large, so the approach can be agreed.
2. Keep each commit to one change, with a [Conventional Commits](https://www.conventionalcommits.org/) message such as `fix: keep whole sentences in drafted release notes`.
3. Add a line to the `[Unreleased]` section of `CHANGELOG.md`.
4. Make sure the tests and the theme check pass, then open a pull request against `master`.
