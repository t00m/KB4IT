---
DocType: How-to guide
Feature: Building
HelpId: hooks
Keyword: hooks, python, on_config, on_document, on_page, on_build_end, plugin, automation
Level: advanced
Order: 330
Related: reference-repo-json.md, howto-customize-templates.md
Section: Guides
Summary: Run your own Python code at fixed points of a build, without writing a theme.
---

# Run your own code during a build

Hooks are Python functions in a file of your knowledge base. KB4IT calls them at fixed points of every build. Use them to fill in text, change pages or run a task after the build.

!!! warning "Hooks run with your rights"
    A hook can do anything your user account can do. Only turn on hooks in knowledge bases you trust.

## Turn hooks on {#enable}

Create `hooks/hooks.py` next to `config/` and name it in `repo.json`:

```json
"hooks": "hooks/hooks.py"
```

KB4IT never loads a hooks file that `repo.json` does not name. The build log shows `[HOOKS] LOADED` with the hooks it found. Editing the file rebuilds every page.

## The hooks {#hooks}

Define only the functions you need.

| Function | Called | Receives | Returns |
|---|---|---|---|
| `on_config(repo)` | Once, after `repo.json` is read | A copy of the settings | The settings to use |
| `on_document(doc_id, meta, text)` | Before each document is converted | File name, its properties (`{key: [values]}`), the Markdown after the title | The Markdown to convert |
| `on_page(page, html)` | After the theme built each page | Page file name, full HTML | The HTML to publish |
| `on_build_end(target, summary)` | After the build | Website folder, build counters | Nothing |

An error in a hook stops the build with `[HOOKS] FAIL hook=<name> doc=<file> error=<message>` and exit status 1.

`on_document` and `on_page` run while several documents are converted at once. Keep them free of shared state, or protect it with a lock.

## Examples {#examples}

Replace a placeholder with a value that changes:

```python
import datetime

def on_document(doc_id, meta, text):
    return text.replace("{{year}}", str(datetime.date.today().year))
```

Add a notice to every page:

```python
def on_page(page, html):
    return html.replace("<body>", '<body><div class="notice">Internal use only</div>', 1)
```

Copy the site somewhere after each build:

```python
import shutil

def on_build_end(target, summary):
    if summary["compiled"]:
        shutil.copytree(target, "/srv/www/kb", dirs_exist_ok=True)
```
