---
DocType: How-to guide
Feature: Building
HelpId: terminal
Keyword: terminal, shell, tmux, screen, ssh, id, project id, import, delete, keys, search, grep, vim, quickfix, completion
Level: basic
Order: 325
Related: reference-command-line.md, howto-use-tui.md
Section: Guides
Summary: Build, search and explore your knowledge bases from the shell, with short project ids.
---

# Work with your knowledge bases from the terminal

Everything here is one command, so it fits a tmux or screen pane, works over SSH and works in a pipe. For the menus, see the [terminal interface](howto-use-tui.md).

## Give each knowledge base an id {#ids}

An id replaces the path of `repo.json` in every command. Choose it when you create the knowledge base:

```bash
kb4it create --id sapblog techdoc ~/kb/sap
```

For a knowledge base you already have, import it with an id. Run the same command on a listed one to add or change its id:

```bash
kb4it import ~/kb/ops/config/repo.json --id ops
```

`kb4it projects` lists the ids. From now on:

```bash
kb4it build sapblog
kb4it serve ops --open
kb4it verify sapblog
```

Turn on [shell completion](reference-command-line.md#completion) and <kbd>Tab</kbd> completes the ids too.

## Find text in the documents {#search}

```bash
kb4it search restore
```

It searches the Markdown sources of every listed knowledge base and prints one line per match: `path:line: text`. No build is needed. Narrow it down:

```bash
kb4it search restore -p sapblog                          # one knowledge base
kb4it search 'ORA-\d+' -r -p ops                         # a regular expression
kb4it search restore --where Status=Open --where Tag=backup
kb4it search restore -l                                  # only the file names
```

Open the matches in vim and jump between them with `:cnext` and `:cprevious`:

```bash
vim -q <(kb4it search restore -p sapblog)
```

The status works in scripts as in `grep`: `0` found, `1` not found, `2` error.

## Explore properties and values {#keys}

`kb4it keys` drills down from the properties to the documents:

```bash
kb4it keys sapblog                 # every property, with its number of documents
kb4it keys sapblog Tag             # every value of Tag
kb4it keys sapblog Tag backup      # the documents with Tag: backup
```

The last form prints paths, so you can open them or pass them on:

```bash
vim $(kb4it keys sapblog Status Open)
```

## Remove a knowledge base {#delete}

```bash
kb4it delete ops            # removes it from the list; the files stay
kb4it delete ops --files    # also deletes the folder, after you type "ops" to confirm
```

In a script, `--files` needs `--yes`. KB4IT never deletes your home folder, a folder without `config/repo.json`, or a knowledge base that is being built. See [Import and delete](reference-command-line.md#import).
