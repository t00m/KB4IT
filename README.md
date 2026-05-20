# KB4IT - Turn your Markdown files into a browsable knowledge base

[![PyPI](https://img.shields.io/pypi/v/KB4IT)](https://pypi.org/project/KB4IT/)
[![Python versions](https://img.shields.io/pypi/pyversions/KB4IT)](https://pypi.org/project/KB4IT/)
![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)
![Platform](https://img.shields.io/badge/platform-GNU%2FLinux-lightgrey)

**KB4IT** turns a folder of Markdown (`.md`) files with YAML frontmatter into a fast, static, property-indexed website. No database, no JavaScript framework, no runtime. Write in plain text, commit to git, generate the site, serve the static files anywhere.

- **Markdown native** - sources are plain `.md` files with a YAML frontmatter block; rendered with `python-markdown` plus the `extra`, `admonition`, `toc`, and `sane_lists` extensions.
- **Serverless output** - plain HTML/CSS, host on GitHub Pages, S3, nginx, or just open `index.html`.
- **Smart incremental builds** - only changed documents and their key/value index pages are recompiled, driven by per-document body and metadata hashes (blake2b).
- **Property-driven navigation** - every frontmatter property becomes a filterable index page automatically.
- **Two themes out of the box** - `techdoc`, `blog` - plus a custom-theme directory under `~/.kb4it/opt/resources/themes/`.

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

# 4. Build the website
kb4it build ~/mykb/config/repo.json

# 5. Open it
xdg-open ~/mykb/target/index.html
```

## Why KB4IT?

- "I just want to drop `.md` files in a folder"
- "I want my metadata (Author, Category, Status…) to become navigation automatically"
- "I want the *output* to be static HTML

## Installation

**uv** - recommended, fastest:

```bash
uv tool install KB4IT
```

Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh` if you don't have it yet.

**pipx** - classic isolated install:

```bash
pipx install KB4IT
```

**pip**:

```bash
pip install --user KB4IT
```

**From source**:

```bash
git clone https://github.com/t00m/KB4IT && cd KB4IT
uv tool install . --force
```

## Requirements

- GNU/Linux (tested on Debian, Ubuntu, Fedora)
- Python ≥ 3.11
- `Mako` (templating), `Markdown` (Markdown → HTML), `PyYAML` (frontmatter), `lxml` (post-processing) - all installed automatically


## Usage

```bash
kb4it create <theme> <repo_path>        # scaffold a new repo
kb4it build <config.json>               # build the site (incremental)
kb4it build <config.json> --force       # force recompile everything
kb4it info <config.json>                # show repo stats
kb4it themes                            # list available themes
kb4it apps <theme>                      # list theme apps
kb4it --version                         # show version
```

A KB4IT repository is just three directories and a config file:

```
mykb/
├── config/
│   └── repo.json       # title, theme, source, target, …
├── source/             # your .md files
└── target/             # generated static website (output)
```

## Configuration

A minimal `repo.json` only needs four required keys:

```json
{
  "title":  "My Knowledge Base",
  "theme":  "techdoc",
  "source": "/home/me/mykb/source",
  "target": "/home/me/mykb/target"
}
```

Required (validated at load time with a clear per-key error):

- `title`  - site title shown in the navbar and `<title>`
- `theme`  - `techdoc` / `blog` or a custom theme name
- `source` - absolute path to the directory holding `.md` files
- `target` - absolute path where the static site will be written

Common optional keys honoured by the bundled themes:

- `tagline`       - short subtitle
- `force`         - force full rebuild on every run (overridden by `--force`)
- `workers`       - parallel compiler workers (default: `CPU_COUNT / 2`)
- `ignored_keys`  - frontmatter keys excluded from navigation
- `events`        - frontmatter categories treated as calendar events
- `logo`, `logo_alt` - paths to navbar logo assets

## Themes

- **techdoc** - Technical documentation, runbooks, knowledge bases. Dense, searchable, property-heavy navigation.
- **blog**    - Chronological posts with tags / categories.

Custom themes live in `~/.kb4it/opt/resources/themes/<your-theme>/`.

## Contributing

Contributions are very welcome - especially bug reports with a minimal reproducing repo, new themes, documentation improvements, and performance work on the compiler / builder.

```bash
git clone https://github.com/t00m/KB4IT
cd KB4IT
uv tool install . --force
kb4it --version
```

Open an issue before starting a large change so we can align on the approach.

## Roadmap / known limitations

- No online editor
- Pseudo-dynamic search - KB4IT aims to stay small and serverless.
- API is still evolving; minor releases may change internals.

## Credits

- [Python](http://www.python.org/) - the language KB4IT is written in.
- [python-markdown](https://python-markdown.github.io/) - Markdown to HTML conversion.
- [Mako](https://www.makotemplates.org/) - server-side templating.
- [UIKit](https://getuikit.com) - the front-end framework used by the bundled themes.
- [Geany](https://www.geany.org/) - the editor used to build KB4IT.

## License

KB4IT is released under the [GNU GPL v3 or later](LICENSE).

## Contact

Tomás Vírseda (aka **t00m**) - tomasvirseda@gmail.com

If KB4IT is useful to you, star the repo - it genuinely helps me decide where to spend time. Issues, ideas, and PRs are all welcome.
