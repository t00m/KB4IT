---
DocType: How-to guide
Feature: Publishing
HelpId: github-pages
Keyword: github actions, ci, deploy, workflow, pages
Level: advanced
Order: 410
Related: howto-publish-web-server.md
Section: Publish
Summary: Keep the knowledge base in a GitHub repository and publish it on GitHub Pages on every push.
---

# Publish on GitHub Pages

GitHub can build your site and publish it each time you push a change. You keep only the documents and settings in git; the website is made by GitHub Actions.

## Prepare the repository {#prepare}

Put the knowledge base at the root of a GitHub repository, or in a folder of an existing one:

```text
config/repo.json
source/...
```

Do not commit the generated files. Add a `.gitignore` next to `config/`:

```text
var/
target/
```

Keep `"source": "source"` and `"target": "target"` in `repo.json`. They are relative to the knowledge base folder, so the build works on any computer. `kb4it create` writes them that way.

!!! warning "Sources are published by default"
    KB4IT copies your `.md` files to the website, so readers can see the source of each page. Set `"publish_sources": false` in `repo.json` if they should not.

## Add the workflow {#workflow}

Create `.github/workflows/site.yml`:

```yaml
name: site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'
      - run: pip install KB4IT
      - run: kb4it build config/repo.json
      - uses: actions/upload-pages-artifact@v5
        with:
          path: target

  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

If the knowledge base is in a folder, say `docs-site/`, use `docs-site/config/repo.json` and `path: docs-site/target`.

!!! tip "Pin the version"
    Install the version you tested, for example `pip install KB4IT==0.7.10`, so the site does not change when a new KB4IT is released. Upgrade on purpose, after a local build.

## Turn on GitHub Pages {#enable}

In the repository on GitHub, open **Settings**, then **Pages**, and under **Build and deployment** set **Source** to **GitHub Actions**. Or from a terminal with the GitHub CLI:

```bash
gh api -X POST repos/OWNER/REPO/pages -f build_type=workflow
```

Push a change. The site appears at `https://OWNER.github.io/REPO/`. The **Actions** tab shows each build and its log.

## Check broken documents in CI {#check}

Add `kb4it verify config/repo.json` before the build step to stop the publish when a document cannot be read, or set `"fail_on_invalid": true` in `repo.json`.

This help is published exactly this way; see `.github/workflows/help.yml` in the [KB4IT repository](https://github.com/t00m/KB4IT).
