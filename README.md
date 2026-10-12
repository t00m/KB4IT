# KB4IT - Turn your Markdown files into a browsable knowledge base

[![PyPI](https://img.shields.io/pypi/v/KB4IT)](https://pypi.org/project/KB4IT/)
[![Python versions](https://img.shields.io/pypi/pyversions/KB4IT)](https://pypi.org/project/KB4IT/)
![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)
![Platform](https://img.shields.io/badge/platform-GNU%2FLinux%20%7C%20macOS%20%7C%20Windows-lightgrey)

**KB4IT** turns a folder of Markdown (`.md`) files with YAML frontmatter into a fast, static, property-indexed website. No database, no JavaScript framework, no runtime. Write in plain text, commit to git, generate the site, serve the static files anywhere.

- **Markdown native** - sources are plain `.md` files with a YAML frontmatter block; rendered with `python-markdown` plus the `extra`, `admonition`, `toc`, and `sane_lists` extensions, and any other extension you enable in `repo.json`.
- **Property-driven navigation** - every frontmatter property becomes a filterable index page automatically.
- **Live preview** - `kb4it serve` rebuilds the site when you save and reloads the page in the browser.
- **Full-text search** - runs in the browser, needs no server, and also works when you open the site from disk.
- **Smart incremental builds** - only changed documents and their key/value index pages are recompiled, driven by per-document body and metadata hashes (blake2b).
- **Ready to publish** - `sitemap.xml`, `robots.txt`, an Atom feed, Open Graph tags and canonical links once you set `site_url`.
- **Links you can trust** - every document lists the documents that link to it, and `kb4it verify` reports broken links and anchors.
- **Yours to adjust** - replace a single template per site, add your own CSS or scripts, or run Python hooks during the build.
- **Four themes out of the box** - `techdoc`, `blog`, `bookshelf` and `apphelp` - plus a custom-theme directory under `~/.kb4it/opt/resources/themes/`.
- **Runs everywhere** - GNU/Linux, macOS and Windows.

**Documentation: [t00m.github.io/KB4IT](https://t00m.github.io/KB4IT/)** - install, write, build, publish, themes and development notes.

## Live demos

See KB4IT in action with the bundled themes:

- **techdoc** - [t00mterías](https://t00m.github.io/techdoc/index.html)
- **blog** - [t00m's tech notes](https://t00m.github.io/blog/index.html)

## Source format

Every KB4IT document is a Markdown file beginning with a YAML frontmatter block. The closing `---` is the only header boundary; the title comes from the first `# H1` heading, not from the frontmatter.

```markdown
---
Author: Tomás Vírseda
Category: Procedure
Date: 2026-05-19
DocType: How-to guide
OS: Linux
Tag: backup, housekeeping
---

# Daily backup runbook

## Procedure

1. …
```

Frontmatter values are either scalars or comma-separated lists. Property names are case-sensitive and singular (`Tag`, `Product`, `OS`).

## Quick start

```bash
# 1. Install KB4IT (see Installation below)
uv tool install KB4IT

# 2. Create a new knowledge base
kb4it create techdoc ~/mykb

# 3. Drop your .md files into ~/mykb/source/

# 4. Build it, serve it and rebuild it each time you save
kb4it serve ~/mykb/config/repo.json

# 5. Open the address it prints, http://127.0.0.1:8642/, in your browser
```

When you are happy with it, `kb4it build ~/mykb/config/repo.json` writes the final site to `~/mykb/target/`, ready to copy to any web server. On GitHub, the [KB4IT action](https://t00m.github.io/KB4IT/reference-github-action.html) builds it in one step: `uses: t00m/KB4IT@v0.9.0`.

## Why KB4IT?

- "I just want to drop `.md` files in a folder"
- "I want my metadata (Author, Category, Status…) to become navigation automatically"
- "I want the *output* to be static HTML"
- "I want to see my changes while I write"
- "I want it on Linux, macOS and Windows"

## Installation

**uv** - recommended, fastest.

On GNU/Linux and macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # or, on macOS: brew install uv
uv tool install KB4IT
```

On Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv tool install KB4IT
```

**pipx** - classic isolated install:

```bash
pipx install KB4IT
```

**pip**:

```bash
pip install --user KB4IT
```

**Extras** - [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) for task lists, tabs, details and more:

```bash
uv tool install "KB4IT[extras]"
```

**Container** - Docker or Podman, nothing else to install:

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" ghcr.io/t00m/kb4it build config/repo.json
```

**Linux packages** - a `.deb` and an `.rpm` for each release on the [releases page](https://github.com/t00m/KB4IT/releases); they install without internet access.

**From source**:

```bash
git clone https://github.com/t00m/KB4IT && cd KB4IT
uv tool install . --force
```

On Windows, KB4IT runs natively; the Windows Subsystem for Linux works too but is not needed.

## Requirements

- GNU/Linux, macOS 13 or newer, or Windows 10 or 11
- Python 3.11 to 3.14
- `Mako` (templating), `Markdown` (Markdown → HTML), `PyYAML` (frontmatter), `Pygments` (code highlighting), `lxml` (post-processing), `rich` and `textual` (terminal interface) - all installed automatically

## Usage

```bash
kb4it create <theme> [<app>] <repo_path>  # scaffold a new repo
kb4it serve <config.json>                 # build, serve on 127.0.0.1:8642 and rebuild on change
kb4it build <config.json>                 # build the site (incremental)
kb4it build <config.json> --force         # force recompile everything
kb4it verify <config.json>                # check documents and links without building
kb4it info <config.json>                  # show repo stats
kb4it themes                              # list available themes
kb4it apps <theme>                        # list theme apps
kb4it projects                            # list your knowledge bases
kb4it --version                           # show version
```

Run `kb4it` with no arguments in a terminal to open the terminal interface: create, build, explore and preview your projects from one screen.

A KB4IT repository is a few directories and a config file:

```
mykb/
├── config/
│   └── repo.json       # title, theme, source, target, …
├── source/             # your .md files
├── target/             # generated static website (output)
├── overrides/          # optional: your own templates and static files
├── hooks/              # optional: Python build hooks
└── var/                # build cache and logs; safe to delete
```

## Configuration

A minimal `repo.json` only needs four required keys:

```json
{
  "title":  "My Knowledge Base",
  "theme":  "techdoc",
  "source": "source",
  "target": "target"
}
```

Required (validated at load time with a clear per-key error):

- `title`  - site title shown in the navbar and `<title>`
- `theme`  - `techdoc`, `blog`, `bookshelf`, `apphelp` or a custom theme name
- `source` - directory holding the `.md` files, relative to the repository root (absolute paths work too)
- `target` - directory where the static site will be written, relative to the repository root

Common optional keys:

- `tagline`       - short subtitle
- `force`         - force full rebuild on every run (overridden by `--force`)
- `workers`       - parallel compiler workers (default: `CPU_COUNT / 2`)
- `ignored_keys`  - frontmatter keys excluded from navigation
- `logo`, `logo_alt` - paths to navbar logo assets

New in 0.9, all optional:

- `site_url`   - public address of the site; enables `sitemap.xml`, the feed and canonical links
- `markdown`   - extra python-markdown extensions, and build-time code highlighting with Pygments
- `search`     - `false` turns off full-text search
- `feed`       - Atom feed settings (on by default in the blog theme)
- `sitemap`    - `false` turns off `sitemap.xml` and `robots.txt`
- `og_image`   - preview image for shared links
- `overrides`  - folder with your own templates and static files (default `overrides`)
- `hooks`      - Python file with build hooks
- `backlinks`  - `false` hides the "Linked from" list

Every key is described in the [repository settings reference](https://t00m.github.io/KB4IT/reference-repo-json.html).

## Themes

- **techdoc** - Technical documentation, runbooks, knowledge bases. Dense, property-heavy navigation, full-text search, event calendar.
- **blog** - Chronological posts with tags and categories, full-text search and an Atom feed.
- **bookshelf** - Study companion organised as books, parts and chapters, with reading progress and search.
- **apphelp** - Help site for an application. Works from `file://`, from a GitHub Pages subpath and embedded in the app; strict metadata, offline search, help ids and versioned help. Start with `kb4it create apphelp <path>`.

All themes show the documents that link to each page. Custom themes live in `~/.kb4it/opt/resources/themes/<your-theme>/`; to change only one template of a theme, use the `overrides/` folder.

## Contributing

Contributions are very welcome - especially bug reports with a minimal reproducing repo, new themes, documentation improvements, and performance work on the compiler / builder.

```bash
git clone https://github.com/t00m/KB4IT
cd KB4IT
uv tool install . --force
kb4it --version
./scripts/devel/test.sh          # the tests; on Windows, run it from Git Bash
```

CI runs the tests and a build of every theme on GNU/Linux, macOS and Windows with Python 3.11, 3.13 and 3.14.

Open an issue before starting a large change so we can align on the approach.

## Roadmap / known limitations

- No online editor
- No multilingual sites yet
- No built-in diagrams or math: add a browser library such as Mermaid or KaTeX with the `overrides/` folder
- No image processing (resizing, minification)
- API is still evolving; minor releases may change internals.

## Credits

- [Python](http://www.python.org/) - the language KB4IT is written in.
- [python-markdown](https://python-markdown.github.io/) - Markdown to HTML conversion.
- [Mako](https://www.makotemplates.org/) - server-side templating.
- [Pygments](https://pygments.org/) - code highlighting.
- [UIKit](https://getuikit.com) - the front-end framework used by the bundled themes.
- [Geany](https://www.geany.org/) - the editor used to build KB4IT.

## License

KB4IT is released under the [GNU GPL v3 or later](LICENSE).

## Contact

Tomás Vírseda (aka **t00m**) - tomasvirseda@gmail.com

If KB4IT is useful to you, star the repo - it genuinely helps me decide where to spend time. Issues, ideas, and PRs are all welcome.
