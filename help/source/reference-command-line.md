---
DocType: Reference
Feature: Building, Configuration
HelpId: command-line
Keyword: cli, kb4it, create, --index, --id, id, project id, import, delete, --files, --yes, keys, search, --where, -p, grep, vim, quickfix, build, doctor, serve, --host, --port, --open, --no-watch, --no-reload, --interval, verify, info, themes, apps, projects, help, --url, --dismiss, notice, --force, --trace, --log-level, exit status, KB4IT_HOME, completion, autocomplete, bash, zsh, fish
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
| `kb4it create --index yes THEME [APP] PATH` | Also decides whether search engines may index the site: `--index yes` writes `"seo": {"index": true}` into `repo.json`, `--index no` writes `false`. Without it nothing is written and the build reminds you; see [Search engines](reference-repo-json.md#indexing) |
| `kb4it create --id ID THEME [APP] PATH` | Also gives the new knowledge base the id `ID`; see [Project ids](#ids) |
| `kb4it build CONFIG` | Builds the website of the knowledge base whose settings are in `CONFIG` |
| `kb4it build --force CONFIG` | Rebuilds everything |
| `kb4it build --trace CONFIG` | Builds and shows how long each part of the build took; see [Build timings](#trace) |
| `kb4it serve CONFIG` | Builds, serves the site at `http://127.0.0.1:8642/` and rebuilds it when you save; see [its options](#serve) and [Preview while you write](howto-preview.md) |
| `kb4it verify CONFIG` | Checks every document, the links between documents (`LINK_BROKEN`, `LINK_NO_EXTENSION`, `ANCHOR_MISSING`) and the theme's own rules without building. It also shows `INDEX_UNSET` while `seo.index` is not set, as information, and checks the [profiles](reference-log-codes.md#people): an error such as `PROFILE_INVALID` fails it, `PROFILE_NO_CONTACT` and `AUTHOR_NO_PROFILE` do not |
| `kb4it info CONFIG` | Shows the main settings |
| `kb4it themes` | Lists the installed themes with their version, fingerprint and folder |
| `kb4it doctor` | Shows the KB4IT build and commit, Python, the folders it uses and every theme; ends with `1` when a bundled file or theme is missing. See [Check the installation](howto-install.md#check) |
| `kb4it apps THEME` | Lists the sample apps of a theme |
| `kb4it projects` | Lists the knowledge bases you created or imported, with their ids. Piped, it prints `id`, name and config separated by tabs, with no header |
| `kb4it import CONFIG [--id ID] [--name NAME]` | Adds an existing knowledge base to the list; on a listed one, sets its id or name. See [Import and delete](#import) |
| `kb4it delete PROJECT [--files] [--yes]` | Removes a knowledge base from the list; `--files` also deletes its folder. See [Import and delete](#import) |
| `kb4it keys PROJECT [KEY [VALUE]]` | Lists the properties of the documents, the values of one, or the documents with one value. See [Properties and values](#keys) |
| `kb4it search PATTERN [-p PROJECT]...` | Finds text in the Markdown sources and prints `path:line: text`. See [Search the sources](#search) |
| `kb4it help` | Opens the offline copy of this help in your browser; see [Help center](#help) |
| `kb4it help --url` | Prints the address of the online help |
| `kb4it help --dismiss` | Hides the help notice |
| `kb4it --version` | Prints the KB4IT build, then the commit it was built from and when |

`CONFIG` is the path of `config/repo.json`, for example `~/mykb/config/repo.json`, or the id of a listed project. `PROJECT` is the same: an id or a config path.

## Project ids {#ids}

An id is a short name you choose for a knowledge base, so you type `kb4it build sapblog` instead of the whole path. It has 1 to 32 characters: lowercase letters, digits and dashes, starting with a letter. Each id is used by one project only.

Give an id when you create or import a knowledge base: `kb4it create --id sapblog techdoc ~/kb/sap` or `kb4it import ~/kb/sap/config/repo.json --id sapblog`. To give an id to a knowledge base that is already listed, run `kb4it import` on it again with `--id`. The terminal interface has an **Edit id** button on the project screen.

Every command that takes `CONFIG` (`build`, `serve`, `info`, `verify`, `keys`, `delete`, `search -p`) also takes an id. KB4IT reads the word this way:

1. When a file with that name exists, it is the config file. So `kb4it build config/repo.json` works as always.
2. Otherwise, when a listed project has that id, KB4IT uses its config file.
3. Otherwise the command ends with `1` and says that there is no such id or file.

## Import and delete {#import}

`kb4it import CONFIG` adds a knowledge base you already have, for example one cloned from git. The display name is the `title` in `repo.json`, or the folder name; `--name` sets another one. Running it on a listed knowledge base adds nothing twice: it sets the `--id` and `--name` you give, or says it is already listed.

`kb4it delete PROJECT` removes the knowledge base from the list. Its files stay on disk.

`kb4it delete PROJECT --files` also deletes the knowledge base folder, the one that holds `config/`. In a terminal it shows the folder and the number of files, and asks you to type the id (or the folder name, when the project has no id). In a script, add `--yes`; without a terminal and without `--yes` it deletes nothing and ends with `1`. It refuses, and deletes nothing, when:

- the folder has no `config/` holding the project's `repo.json`;
- the folder is `/`, your home folder or `~/.kb4it`, or contains one of them;
- a build or `kb4it serve` is using the knowledge base.

When `target` in `repo.json` points outside the knowledge base folder, the website there is kept, and the command prints its path.

## Properties and values {#keys}

`kb4it keys` reads the front matter of the documents in `source/` directly. It needs no build.

| Command | Prints |
|---|---|
| `kb4it keys sapblog` | Each property with the number of documents that use it. `Title` is left out |
| `kb4it keys sapblog Tag` | Each value of `Tag` with its number of documents |
| `kb4it keys sapblog Tag backup` | The path of each document with `Tag: backup`, one per line |

Property names and values match in any case: `kb4it keys sapblog tag BACKUP` works. Documents KB4IT cannot read are left out, and one line on standard error gives how many; `kb4it verify` tells why. An unknown property or value ends with `1`.

## Search the sources {#search}

`kb4it search PATTERN` finds `PATTERN` in the Markdown documents of every listed knowledge base, front matter included. Each match prints as `path:line: text`, with the full path, the way `grep -n` does:

```bash
kb4it search restore                         # every knowledge base
kb4it search restore -p sapblog -p ops       # only these two
kb4it search restore --where Status=Open     # only documents with Status: Open
vim -q <(kb4it search restore -p sapblog)    # open the matches in vim's quickfix list
```

| Option | Does |
|---|---|
| `-p PROJECT`, `--project PROJECT` | Searches this knowledge base only; repeat it for several. Without `-p`, every listed one |
| `--where KEY=VALUE` | Keeps the documents with that property value, in any case. Different keys must all match; the same key repeated matches any of its values: `--where Status=Open --where Status=Planned --where Tag=backup` means (Open or Planned) and backup |
| `-r`, `--regex` | `PATTERN` is a Python regular expression. Without it, it is plain text |
| `-s`, `--case-sensitive` | Matches upper and lower case exactly. Without it, case does not matter |
| `-l`, `--files-with-matches` | Prints only the path of each matching document |

In a terminal the path, the line number and the match are colored; piped, or with `NO_COLOR` set, the output is plain. A listed knowledge base whose `repo.json` is gone is skipped with a warning.

`kb4it search` ends like `grep`: `0` when something matched, `1` when nothing did, `2` on an error such as a wrong regular expression, an unknown `-p` or an empty project list.

## Help center {#help}

`kb4it help` opens the copy of this help that ships inside the installed package. It needs no network. When the package has no copy, the command prints the online address and ends with `1`. When no browser starts, it prints the path of the file to open by hand.

`kb4it help --url` prints the online address and does nothing else.

Until you dismiss it, every command that runs, except `kb4it help`, prints a two-line notice on standard error. The notice gives the path of the offline copy and the online address. `kb4it help --dismiss` hides it for good: it writes the file `help-notice-dismissed` in `~/.kb4it` (or in `KB4IT_HOME`). Delete that file to see the notice again. The terminal interface shows the first line of the notice as a banner, until you press `d` there or run this command. The notice never shows when the variable `CI` has a non-empty value.

## Options {#options}

Put them before the command.

| Option | Does |
|---|---|
| `-L LEVEL`, `--log-level LEVEL` | How much to print: `DEBUG`, `INFO` (default), `WARNING` or `ERROR`. The log file gets every line at any level |
| `-v`, `--version` | Prints the version and exits |
| `-h`, `--help` | Prints help; `kb4it build --help` prints help for one command |

`-f` is short for `--force`.

## Options of serve {#serve}

Put them after `serve`, before or after `CONFIG`.

| Option | Does |
|---|---|
| `--host ADDRESS` | Address to listen on. Default `127.0.0.1`, this computer only; `0.0.0.0` lets other computers see the preview (`WARNING_PUBLIC`) |
| `--port PORT` | First port to try. Default `8642`; when it is busy, the next free one is used |
| `--open` | Opens the site in your browser |
| `--no-watch` | Serves only; does not rebuild when a file changes |
| `--no-reload` | Rebuilds, but does not reload pages in the browser |
| `--interval SECONDS` | Seconds between checks for changes. Default `1.0` |
| `-f`, `--force` | Rebuilds everything in the first build |
| `--trace` | Writes `var/log/trace.json` with the timings of each build; see [Build timings](#trace) |

## Shell completion {#completion}

KB4IT completes commands, options, the installed themes, the apps of a theme and file paths with <kbd>Tab</kbd>. It uses [argcomplete](https://kislyuk.github.io/argcomplete/), which is installed with KB4IT. Register the command once per shell:

```bash
# bash
eval "$(register-python-argcomplete kb4it)"
# zsh, after compinit
eval "$(register-python-argcomplete kb4it)"
# fish
register-python-argcomplete --shell fish kb4it | source
```

Put the line in `~/.bashrc`, `~/.zshrc` or `~/.config/fish/config.fish` to keep it. `activate-global-python-argcomplete` enables completion for `kb4it` and every other argcomplete-aware command at once.

The `CONFIG` and `PROJECT` arguments complete the project ids and file paths; `search -p` completes the ids only. `kb4it keys sapblog <Tab>` lists the properties and, after one, its values; `kb4it search x --where <Tab>` completes `KEY=` and then `KEY=VALUE`.

`kb4it create <Tab>` and `kb4it apps <Tab>` list the installed themes; after a theme, the next word lists its sample apps and folders. Once the app is typed, only folders are offered for the path. The `config` argument of `build`, `serve`, `info` and `verify` completes file paths, so `config/repo.json` is a few keystrokes away. Completion reads the theme folders directly, so a theme installed under `~/.kb4it/opt/resources/themes/` appears without regenerating anything.

Without argcomplete the command line works as before; only <kbd>Tab</kbd> completion is missing.

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

`kb4it search` uses its own statuses, like `grep`; see [Search the sources](#search).

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
