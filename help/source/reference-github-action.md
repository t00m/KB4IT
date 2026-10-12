---
DocType: Reference
Feature: Publishing
HelpId: github-action
Keyword: github actions, action, ci, workflow, uses, inputs, outputs, verify, pages
Level: advanced
Order: 630
Related: howto-publish-github-pages.md
Section: Reference
Summary: The inputs and outputs of the KB4IT GitHub Action, which builds a site in a GitHub workflow.
---

# GitHub Action

The KB4IT repository is also a GitHub Action. One step in a workflow installs KB4IT, checks the documents and builds the site:

```yaml
- id: kb4it
  uses: t00m/KB4IT@v0.9.0
  with:
    config: config/repo.json
```

It runs on Linux, macOS and Windows runners and needs no Python on the runner: it installs KB4IT with uv. It never publishes anything; pass its `target` output to the step that does, such as `actions/upload-pages-artifact`. [Publish on GitHub Pages](howto-publish-github-pages.md) has a complete workflow.

## Inputs {#inputs}

| Input | Default | Meaning |
|---|---|---|
| `config` | (required) | Path of `repo.json`, relative to the workspace |
| `version` | empty | KB4IT version to install from PyPI. Empty installs the KB4IT of the action itself, so `@v0.9.0` builds with KB4IT 0.9.0 |
| `python-version` | `3.13` | Python that runs KB4IT, from 3.11 to 3.14 |
| `extras` | `false` | `true` also installs the extras ([PyMdown Extensions](reference-repo-json.md#markdown)) |
| `verify` | `true` | Run `kb4it verify` first; a document that cannot be read, a broken link or a theme problem fails the step before anything is built |
| `force` | `false` | `true` builds with `--force`, compiling every page |

## Outputs {#outputs}

| Output | Meaning |
|---|---|
| `target` | Absolute path of the built site: the `target` of `repo.json`, resolved like KB4IT does |
| `version` | KB4IT version that built it |

The step also writes a summary on the workflow run page: the KB4IT version, the number of documents, how many were compiled, skipped and invalid, and the target folder.

## Choose the version {#version}

Refer to the action by a release tag, such as `t00m/KB4IT@v0.9.0`, or by a full commit hash. Then the site is built the same way until you change it. There is no moving tag such as `@v0`: a new KB4IT can change how pages look, so upgrade on purpose, after a local build.

To keep the action of one release but build with another KB4IT, set `version`:

```yaml
- uses: t00m/KB4IT@v0.9.0
  with:
    config: config/repo.json
    version: 0.9.1
```
