---
DocType: Reference
Feature: Building, Configuration
HelpId: command-line
Keyword: cli, kb4it, create, build, serve, verify, info, themes, apps, projects, --force, --log-level, exit status, KB4IT_HOME
Level: basic
Order: 610
Section: Reference
Summary: Every kb4it command and option, and what the exit status means.
---

# Command line

`kb4it` with no command, in a terminal, opens the [terminal interface](howto-use-tui.md). With a command it works like any other command-line tool.

| Command | Does |
|---|---|
| `kb4it create THEME [APP] PATH` | Creates a knowledge base in `PATH` from a theme and one of its apps (`default` if you leave it out) |
| `kb4it build CONFIG` | Builds the website of the knowledge base whose settings are in `CONFIG` |
| `kb4it build --force CONFIG` | Rebuilds everything |
| `kb4it serve CONFIG` | Builds, serves the site at `http://127.0.0.1:8642/` and rebuilds it when you save; see [Preview while you write](howto-preview.md) |
| `kb4it verify CONFIG` | Checks every document and the theme's own rules without building |
| `kb4it info CONFIG` | Shows the main settings |
| `kb4it themes` | Lists the installed themes |
| `kb4it apps THEME` | Lists the sample apps of a theme |
| `kb4it projects` | Lists the knowledge bases you created or imported |

`CONFIG` is the path of `config/repo.json`, for example `~/mykb/config/repo.json`.

## Options {#options}

Put them before the command.

| Option | Does |
|---|---|
| `-L LEVEL`, `--log-level LEVEL` | How much to print: `DEBUG`, `INFO` (default), `WARNING` or `ERROR` |
| `-v`, `--version` | Prints the version and exits |
| `-h`, `--help` | Prints help; `kb4it build --help` prints help for one command |

`-f` is short for `--force`.

## Exit status {#exit}

| Status | Meaning |
|---|---|
| `0` | Done |
| `1` | Something failed: missing or broken settings, a theme that cannot load, a failed build, problems found by `verify`, or another KB4IT already building the same knowledge base |

A build with unreadable documents still ends with `0` and reports them as `invalid=`; set `"fail_on_invalid": true` to make it fail.

## Files KB4IT keeps {#files}

| Path | Holds |
|---|---|
| `~/.kb4it/projects.json` | The list behind `kb4it projects` and the terminal interface |
| `~/.kb4it/opt/resources/themes/` | Your own themes |
| `~/.kb4it/var/projects.lock` | Held for a moment while `projects.json` is written |
| `<knowledge base>/var/` | Build cache and logs; safe to delete |
| `<knowledge base>/var/kb4it.lock` | Stops two builds of the same knowledge base at once |

`~` is your home folder: `/home/<you>` on Linux, `/Users/<you>` on macOS, `C:\Users\<you>` on Windows.

## Environment variables {#environment}

| Variable | Effect |
|---|---|
| `KB4IT_HOME` | Folder for the files above instead of `~/.kb4it`. Useful for a portable install or to keep test runs apart |
