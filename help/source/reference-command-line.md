---
DocType: Reference
Feature: Building, Configuration
HelpId: command-line
Keyword: cli, kb4it, create, build, serve, verify, info, themes, apps, projects, help, --url, --dismiss, notice, --force, --trace, --log-level, exit status, KB4IT_HOME
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
| `kb4it build --trace CONFIG` | Builds and shows how long each part of the build took; see [Build timings](#trace) |
| `kb4it serve CONFIG` | Builds, serves the site at `http://127.0.0.1:8642/` and rebuilds it when you save; see [Preview while you write](howto-preview.md) |
| `kb4it verify CONFIG` | Checks every document, the links between documents (`LINK_BROKEN`, `LINK_NO_EXTENSION`, `ANCHOR_MISSING`) and the theme's own rules without building |
| `kb4it info CONFIG` | Shows the main settings |
| `kb4it themes` | Lists the installed themes with their version, fingerprint and folder |
| `kb4it apps THEME` | Lists the sample apps of a theme |
| `kb4it projects` | Lists the knowledge bases you created or imported |
| `kb4it help` | Opens the offline copy of this help in your browser; see [Help center](#help) |
| `kb4it help --url` | Prints the address of the online help |
| `kb4it help --dismiss` | Hides the help notice |
| `kb4it --version` | Prints the KB4IT build, then the commit it was built from and when |

`CONFIG` is the path of `config/repo.json`, for example `~/mykb/config/repo.json`.

## Help center {#help}

`kb4it help` opens the copy of this help that ships inside the installed package. It needs no network. When the package has no copy, the command prints the online address and ends with `1`. When no browser starts, it prints the path of the file to open by hand.

`kb4it help --url` prints the online address and does nothing else.

Until you dismiss it, every command that runs, except `kb4it help`, prints a two-line notice on standard error. The notice gives the path of the offline copy and the online address. `kb4it help --dismiss` hides it for good: it writes the file `help-notice-dismissed` in `~/.kb4it` (or in `KB4IT_HOME`). Delete that file to see the notice again. The terminal interface shows the first line of the notice as a banner, until you press `d` there or run this command. The notice never shows when the variable `CI` has a non-empty value.

## Options {#options}

Put them before the command.

| Option | Does |
|---|---|
| `-L LEVEL`, `--log-level LEVEL` | How much to print: `DEBUG`, `INFO` (default), `WARNING` or `ERROR` |
| `-v`, `--version` | Prints the version and exits |
| `-h`, `--help` | Prints help; `kb4it build --help` prints help for one command |

`-f` is short for `--force`.

## Build timings {#trace}

`kb4it build --trace CONFIG` (also `kb4it serve --trace CONFIG`) times each stage and step of the build and the compilation of each document. It works with any `-L` level and adds nothing to the log.

At the end of the build it prints a table: time in milliseconds, share of the build, and the step, indented under its stage. Steps under 1% are left out. Documents compiled in parallel are summed in one line.

It also writes `<knowledge base>/var/log/trace.json`, replaced at each build. Open it in https://ui.perfetto.dev or `chrome://tracing` to see the build as a timeline, with one row per worker thread.

## Exit status {#exit}

| Status | Meaning |
|---|---|
| `0` | Done |
| `1` | Something failed (see below) |

`kb4it build` ends with `1` when:

- the settings are missing or broken, or the theme cannot load;
- a page could not be made: its Markdown, its template or a hook failed. The other pages are still published, the log lists the failed ones after `PAGES_FAILED`, and the summary shows `failed=`;
- documents cannot be read and `"fail_on_invalid": true` is set (without it, they are only reported as `invalid=`);
- another KB4IT is already building the same knowledge base.

After a failed build the next build compiles again every document that changed since the last successful one, so there is no need for `--force`.

`kb4it verify` ends with `1` when it finds a problem in a document, a theme or a link.

## Files KB4IT keeps {#files}

| Path | Holds |
|---|---|
| `~/.kb4it/projects.json` | The list behind `kb4it projects` and the terminal interface |
| `~/.kb4it/opt/resources/themes/` | Your own themes |
| `~/.kb4it/var/projects.lock` | Held for a moment while `projects.json` is written |
| `~/.kb4it/help-notice-dismissed` | Written by `kb4it help --dismiss`; hides the help notice |
| `<knowledge base>/var/` | Build cache and logs; safe to delete |
| `<knowledge base>/var/kb4it.lock` | Stops two builds of the same knowledge base at once |

`~` is your home folder: `/home/<you>` on Linux, `/Users/<you>` on macOS, `C:\Users\<you>` on Windows.

## Environment variables {#environment}

| Variable | Effect |
|---|---|
| `KB4IT_HOME` | Folder for the files above instead of `~/.kb4it`. Useful for a portable install or to keep test runs apart |
| `KB4IT_HELP_INDEX` | Path of the `index.html` that `kb4it help` opens, instead of the copy in the package |
| `CI` | Any non-empty value hides the help notice |
