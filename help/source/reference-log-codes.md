---
DocType: Reference
Feature: Building, Themes, Configuration
HelpId: log-codes
Keyword: log, error, warning, code, message, kb4it.log, build log, CONFIG_ERROR, THEME_ERROR, DOC_INVALID, PAGES_FAILED, META_INVALID
Level: advanced
Order: 640
Related: troubleshooting.md
Section: Reference
Summary: Every error and warning code KB4IT writes to its log, what it means and what to do.
---

# Log codes

Each warning or error line in the log has a component in brackets, a code, and details as `key=value` pairs:

```
[BACKEND] CONFIG_KEY_MISSING key=title
```

The code tells you what happened. The details name the file, key or page. KB4IT prints these lines in the terminal and keeps them in `var/log/kb4it.log` inside the knowledge base. Run with `-L DEBUG` to see every step around them.

The tables list each code once. **Stops** means the command ends with exit status `1`. The common problems have a longer answer in [Troubleshooting](troubleshooting.md).

## Command result {#result}

KB4IT writes one of these lines last, when a command fails. The line before it names the cause.

| Code | Level | Meaning |
|---|---|---|
| `CONFIG_ERROR` | error | The settings are missing or wrong. Stops |
| `THEME_ERROR` | error | The theme cannot load, or its own checks failed. Stops |
| `COMPILE_ERROR` | error | Pages could not be made, a hook failed, or documents cannot be read with `"fail_on_invalid": true`. Stops |
| `KB4IT_ERROR` | error | Any other failure. Stops |

## Settings {#settings}

| Code | Level | Meaning | What to do |
|---|---|---|---|
| `CONFIG_MISSING` | error | The `repo.json` path given to the command does not exist. Stops | Check the path; it is `config/repo.json` inside the knowledge base |
| `CONFIG_PARSE_FAIL` | error | `repo.json` cannot be read. Stops | Fix the JSON |
| `CONFIG_KEY_MISSING` | error | A required key is missing. Stops | See [CONFIG_KEY_MISSING](troubleshooting.md#config-key) |
| `VERIFY_ERROR` | error | `kb4it verify` cannot read `repo.json`. Stops | Fix the JSON or the path |
| `PATH_CWD_RELATIVE` | warning | `source` was found relative to the current folder, not to the knowledge base folder. Older settings worked that way. The build goes on | Make `source` and `target` relative to the folder that holds `config/` |
| `SOURCE_MISSING` | error | The `source` folder does not exist. Stops | See [SOURCE_MISSING](troubleshooting.md#source-missing) |
| `LOAD_FAIL` | error | The `hooks` file raised an error while loading. Stops | Fix the Python file; the message has the error |
| `MD_EXTENSION_MISSING` | error | A Markdown extension, nh3 or Pygments is not installed. Stops | See [MD_EXTENSION_MISSING](troubleshooting.md#md-extension) |
| `MD_EXTENSION_INVALID` | error | A Markdown extension is installed but fails to load with the given settings. Stops | Check its entry in `markdown.extension_configs` |
| `CONFIG_FAIL`, `CONFIG_WARN` | error, warning | Written by an old settings check of the blog theme. Current versions do not run it | Nothing; the line comes from an older KB4IT |

## Documents {#documents}

| Code | Level | Meaning | What to do |
|---|---|---|---|
| `DOC_INVALID` | error | A document cannot be read. It is left out of the site; with `"fail_on_invalid": true` the build stops | See [why a document is rejected](reference-document-format.md#invalid) |
| `DOC_WARN` | warning | The document sets `title` in its front matter. KB4IT ignores it and uses the first `#` heading | Remove `title` from the front matter |
| `DOC_NAME_CLASH` | warning | Two documents differ only by letter case or extension | See [file names](troubleshooting.md#names) |
| `DOC_NAME_RESERVED` | error | The file name is reserved: a Windows device name, or a page the theme writes (`404.md` in techdoc, blog and bookshelf; `add.md` while the editor is on in a theme that supports the Add page). The document is left out | See [file names](troubleshooting.md#names) |
| `DATE_INVALID` | warning, error | A date value cannot be read as a date. The document is sorted with the undated ones | Use a [date form KB4IT reads](reference-document-format.md#dates) |
| `DOC_UNDATED` | warning | The blog theme found a post without a `Date` | Add a `Date` property |
| `LINK_BROKEN` | warning | A link points to a `.md` file that is not in `source/` | See [LINK_BROKEN](troubleshooting.md#link-broken) |
| `ANCHOR_MISSING` | warning | A link points to a section that does not exist | Fix the `#anchor` part of the link |
| `SCAN_FAIL` | warning | The links of a document cannot be checked. The build goes on | Run `kb4it verify` and look at the document the line names |
| `MD_FENCE_IN_BLOCK` | warning | A fenced code block sits inside a list or a quote, where plain Markdown does not see it | See [code inside a note or a list](reference-document-format.md#code-in-blocks) |

## Build {#build}

| Code | Level | Meaning | What to do |
|---|---|---|---|
| `MD_COMPILE_FAIL` | error | The Markdown of a document cannot be converted. Its page is not made | Check the document; the line has the error |
| `COMPILE_FAILED` | error | A page was not made. The other pages are still published | Look for the error above it in the log |
| `PAGES_FAILED` | error | The list of pages that could not be made. The build ends with `1` | Fix each page in the list; see [exit status](reference-command-line.md#exit) |
| `MEMORY_EXHAUSTED` | error | The computer ran out of memory while making a page | Lower `workers` in `repo.json`, or add memory |
| `WRITE_FAIL` | error | A page made by the theme cannot be written to the build folder | Check free disk space and permissions of `var/` |
| `PAGE_MISSING` | error | A page that should be copied to `target` was not made | Look for the error of that page above it in the log |
| `HTML_MISSING` | error | The theme cannot find the converted text of a document | Look for `MD_COMPILE_FAIL` for the same document |
| `METADATA_FAIL`, `KEY_FAIL` | error | The theme cannot build the list of properties of a document | Check the properties of the document the line names |
| `DATATABLE_FAIL` | error | The theme cannot add a document to a table | Check the properties of the document the line names |
| `INDEX_SKIP` | warning | The blog theme left a post out of its home page | Check the post the line names; the line has the error |
| `INDEX_LARGE` | warning | The search index is larger than 5 MB, or 2 MB for apphelp sites | See [search](reference-repo-json.md#search). The build goes on |
| `ADD_PAGE` | info | Written as `[BUILDER] ADD_PAGE enabled=<True or False> skeletons=<overrides, theme or common> categories=<n>`: whether this build makes the Add page, and the skeleton set and number of cards it uses (the last two only when enabled). See the `editor` key in [repo.json](reference-repo-json.md) | Nothing |
| `SKELETON_UNLISTED` | warning | Written as `[BUILDER] SKELETON_UNLISTED file=<name>`: a `*-SKELETON.md` file is not listed in `skeletons.json`, so the Add page ignores it | List the file in `skeletons.json`, or delete it |
| `DEPLOY_DIR_MISSING` | warning | A folder listed in `deploy_dirs` of `theme.json` does not exist in the theme | Create the folder, or remove it from the list |
| `FORCE_SKIP` | warning | With `--force`, a build folder in `var/` was kept because it holds `source` or `target` | Move `source` and `target` out of `var/` |
| `KBDICT_VERSION_MISMATCH` | warning | The build cache was made by another KB4IT version. Every page is rebuilt | Nothing |
| `KBDICT_PYYAML_MISMATCH` | warning | The build cache was made with another PyYAML version. Every page is rebuilt | Nothing |
| `KBDICT_CORRUPT` | warning | The build cache cannot be read. Every page is rebuilt and the cache is replaced | Nothing |
| `KBDICT_LOAD_FAIL` | error | The build cache cannot be opened at all. Stops | Delete `var/` in the knowledge base and build again |

## Themes {#themes}

| Code | Level | Meaning | What to do |
|---|---|---|---|
| `THEME_NOT_FOUND` | error | No theme has the name in `theme`. Stops | See [THEME_NOT_FOUND](troubleshooting.md#theme-not-found) |
| `THEME_MISSING` | error | No theme name was given. Stops | Set `theme` in `repo.json` |
| `THEME_LOAD_FAIL` | error | The theme in `theme_path` cannot load. Stops | Check the folder and its `theme.json` |
| `THEME_PATH_INVALID` | error | `theme_path` is not a folder, or has no `theme.json`. Stops | Correct `theme_path` |
| `THEME_CONF_MISSING` | warning | The theme folder has no `theme.json` | Add one; see [Make your own theme](howto-create-theme.md) |
| `THEME_CONF_INVALID` | error | The theme's `theme.json` cannot be read | Fix the JSON |
| `THEME_INVALID` | error | `kb4it themes` found a theme folder that cannot load. The other themes are listed | Fix or remove that folder |
| `THEME_REQUIREMENT_UNMET` | error | The theme needs a newer KB4IT. Stops | See [THEME_REQUIREMENT_UNMET](troubleshooting.md#requirement) |
| `THEME_REQUIREMENT_MISSING` | warning | The theme does not say which KB4IT it needs | Add a `kb4it` field to its `theme.json` |
| `THEME_REQUIREMENT_INVALID` | error | The `kb4it` field of `theme.json` is not a valid version rule. Stops | Write it like `">=0.9"` |
| `THEME_NOT_LOADED` | error | The site was about to be written without a loaded theme. Stops | Report it as a bug |
| `THEME_AUTOESCAPE_OFF` | warning | Your own theme prints values without escaping them | Add `"autoescape": true` to `theme.json`; see [Escaping](howto-create-theme.md#escaping) |
| `THEME_VERIFY_ERROR` | error | The theme's own check crashed during `kb4it verify`. Stops | Fix the theme's `verify.py` |
| `TEMPLATE_MISSING` | error | The theme lacks a template every theme needs. Stops | Add the template the line names |
| `TEMPLATE_NOT_FOUND` | error | A template the theme asks for does not exist. Stops | Add it to the theme or to `overrides/templates/` |
| `TEMPLATE_COMPILE_FAIL` | error | A template has a syntax error. Stops | See [TEMPLATE_COMPILE_FAIL](troubleshooting.md#template-compile) |

## Help sites {#apphelp}

The apphelp theme checks the properties of each page. With `"strict": true`, the default, any of these problems stops the build and the message lists them all. With `"strict": false` they are warnings. See [apphelp](reference-theme-apphelp.md).

| Code | Meaning | What to do |
|---|---|---|
| `META_MISSING` | A page lacks `Section`, `Order`, `Summary` or `Feature` | Add the property the line names |
| `META_INVALID` | A property has a wrong value: a reserved file name, the old `Kind` property (now `DocType` and `Layout`), an unknown `Layout`, an `Order` that is not a whole number, a `Summary` over 160 characters, a `Related` page that does not exist, or a malformed `HelpId` | Fix the value the line names |
| `META_UNKNOWN` | A `Feature`, `Level` or `Platform` value is not in the vocabulary | Use a listed value, or add it to `vocabulary` |
| `META_CONFIG` | The `vocabulary` in `repo.json` has no `Feature` list | Add one |
| `DOCTYPE_MISSING` | A page has no `DocType`. It is left out | Add `DocType` |
| `DOCTYPE_INVALID` | `DocType` is not `Tutorial`, `How-to guide`, `Reference` or `Explanation`. It is left out | Use one of the four |
| `DOC_LEFT_OUT` | A page without a valid `DocType` was left out of the site | See `DOCTYPE_MISSING` and `DOCTYPE_INVALID` |
| `HELPID_DUPLICATE` | Two pages use the same help id | Give each page its own |
| `HELPID_TARGET_MISSING` | A help id points to a page or section that does not exist. Stops in strict mode | Fix the `HelpId` or the heading it points to |
| `CONTRACT_MISSING` | An entry of the contract file has no page. Stops | Add the page or help id, or remove the entry |
| `CONTRACT_FILE_MISSING` | The `contract` file named in `repo.json` does not exist | Create it, or remove `contract` |
| `INDEX_PAGE_MISSING` | A page is missing from the search index because its file was not written | Look for its error above in the log |

## Terminal interface and projects {#projects}

| Code | Level | Meaning | What to do |
|---|---|---|---|
| `PROJECTS_CORRUPT` | warning | `projects.json` cannot be read. KB4IT renames it to `projects.json.corrupt-<date>` and starts an empty list | Add your knowledge bases again, or repair the kept copy |
| `PROJECTS_LOAD_ERROR` | error | `kb4it projects` cannot read the list | Check `~/.kb4it/projects.json` |
| `PROJECT_SAVE_ERROR` | error | A new knowledge base could not be added to the list | Check permissions of `~/.kb4it` |
| `REPO_PATH_MISSING`, `REPO_PATH_CREATED` | warning | `kb4it create` was given a folder that did not exist, and created it | Nothing |
| `WARNING_PUBLIC` | warning | `kb4it serve` listens on an address other computers can reach | Use the default `--host 127.0.0.1` unless you need it |

## Internal errors {#internal}

These point to a bug in KB4IT or in a theme, not to your documents. Please [report them](https://github.com/t00m/KB4IT/issues) with the log.

| Code | Level | Meaning |
|---|---|---|
| `SERVICE_NOT_REGISTERED` | error | A part of KB4IT asked for a service that does not exist. Stops |
| `DOMAIN_UNKNOWN` | error | A theme wrote a value into an unknown place |
| `DOC_NOT_IN_DB` | warning | A theme asked for a document that is not in the build |
