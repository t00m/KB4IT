# Changelog

All notable changes to KB4IT are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- `KB4IT_HOME` environment variable: puts the per-user files (`projects.json`, user themes, logs) in another folder instead of `~/.kb4it`. The test suite uses it so that it never writes to the real profile, also on Windows (CP-03).
- Terminal interface: **Copy Log** uses `pbcopy` on macOS and `clip.exe` on Windows, before falling back to the terminal's OSC 52 (CP-05).
- Documents named like a Windows device (`con.md`, `nul.md`, `com1.md`, ...) are left out of the site on every system with `DOC_NAME_RESERVED`, so a site builds the same everywhere. Two documents whose pages differ only by letter case or extension (`Note.md`, `note.md`, `note.markdown`) log `DOC_NAME_CLASH`; `kb4it verify` reports both problems, and `fail_on_invalid` makes them stop the build (CP-06).
- CI runs the tests and a create-and-build of every bundled theme on Linux, macOS and Windows, with Python 3.11 and 3.13. `scripts/devel/test.sh --python X.Y` picks the Python version, and `scripts/devel/smoke_build.py` runs the same smoke build locally (CP-09).
- `kb4it serve CONFIG`: builds the site, serves it at `http://127.0.0.1:8642/` and rebuilds it when a document, `repo.json`, your own theme, overrides or hooks change. Open pages reload after each rebuild, and a failed build shows its first error in a bar at the top of the page; the files in `target/` never contain the reload script. Options: `--host`, `--port`, `--open`, `--no-watch`, `--no-reload`, `--interval`, `--force` (SV-01).
- Terminal interface: **Browse via Web Server** rebuilds the site when you save a document, reloads open pages and shows a notification after each rebuild (SV-02).
- `markdown` block in `repo.json`: `extensions` and `extension_configs` add python-markdown extensions to the built-in ones. A missing extension stops the build with `MD_EXTENSION_MISSING` and an install hint, and `kb4it verify` reports it; changing the block rebuilds every page. `KB4IT[extras]` installs PyMdown Extensions (MD-01).
- `markdown.highlight`: `pygments` colours code blocks at build time with Pygments, writes `resources/pygments.css` (a light and a dark style, `pygments_style` and `pygments_style_dark`) and drops highlight.js from the pages, in all four themes; `none` turns colouring off. The default, `client`, keeps highlight.js. Pygments is a new dependency (MD-02).
- Full-text search in techdoc, blog and bookshelf: a search box that shows the best matches as you type, and a `search.html` page with all results and filters by Category and Tag. The index (`search-index.js`) holds the text of every document by section, works from `file://`, and is updated incrementally: documents that did not change are not parsed again. `"search": false` in `repo.json` turns it off. The search engine is now shared with apphelp (SR-01, SR-02, SR-03).
- `site_url` in `repo.json`: the public address of the site, used by the sitemap, the feed and the canonical and Open Graph tags. A value that is not an `http://` or `https://` address stops the build (PB-01).
- With `site_url` set, every build writes `sitemap.xml` (with the document `Date` as last change) and `robots.txt`; a `robots.txt` in `source/` is published instead of the generated one. `"sitemap": false` turns both off (PB-02).
- Atom feed `feed.xml` with the newest dated documents: on by default in the blog theme when `site_url` is set, and available in techdoc and bookshelf with `"feed": {"enabled": true}`. Options: `limit`, `categories`, `full_content` (PB-03).
- Every page carries a description (the `Summary` property, or the first lines of the document) and Open Graph tags; with `site_url` also a canonical link, and `og_image` adds a preview image for shared links. The fixed "KB4IT document" description and author tags of techdoc, blog and bookshelf are gone. A theme can replace the tags with its own `HTML_HEAD_META.tpl` (PB-04).
- Per-repository overrides: a template in `overrides/templates/` replaces the theme's template of the same name, and files in `overrides/static/` are copied into the website. Changing them rebuilds every page; `overrides` in `repo.json` picks another folder. `kb4it serve` watches the folder (CU-01).
- Build hooks: `"hooks": "hooks/hooks.py"` in `repo.json` loads Python functions that KB4IT calls during the build: `on_config`, `on_document`, `on_page` and `on_build_end`. An error in a hook stops the build; editing the file rebuilds every page (CU-02).
- "Linked from": every document ends with the list of documents that link to it, in all four themes. Links are kept in `kbdict.json`, so only changed documents are scanned, and a page is rebuilt when its list changes. `"backlinks": false` hides the list (KG-01).
- apphelp versions: with `"versions": {"enabled": true}` each build goes to `target/<version>/` and keeps the other versions, `latest/` copies the newest one, and `index.html`, `versions.json` and `helpids.js` at the top point to it. A version selector in the header opens the same page in another version (VH-01, VH-02). The GitHub Pages guide shows how to publish all versions (VH-03).
- `scripts/distribution/wheels/download_wheels.sh ARCH` downloads the binary wheels of every KB4IT dependency for Python 3.11, 3.12 and 3.13 on `x86_64` or `aarch64` into `dist/wheels/`, about 20 MB per architecture. The `.deb` and `.rpm` ship them so they install without network access (DS-05).
- Python 3.14 is supported: the full test suite passes on it, CI runs it on Linux, macOS and Windows next to 3.11 and 3.13, and the `.deb` and `.rpm` carry wheels for it. Fedora 44 ships Python 3.14 as `python3`.
- CI job `packages`: checks every distribution script with shellcheck, builds the sdist, wheel, source tarball, `.deb` and `.rpm` for both architectures, installs the packages offline in Debian 12, Ubuntu 24.04, Fedora and Rocky Linux 9 containers, builds the container image and smoke-tests it with Docker and Podman. The packages and tarballs are kept as workflow artifacts for 7 days (DS-08).
- Each release publishes the container image `ghcr.io/t00m/kb4it` for amd64 and arm64, tagged `X.Y.Z`, `X.Y` and `latest`, from the same wheel as PyPI. The image is smoke-tested before the push, carries an SBOM and a build provenance attestation, and the GitHub release waits for it and names its digest. The workflow pushes with its own token; no secret is stored (GI-02, GI-03).
- Each GitHub release carries the `.deb` (amd64, arm64) and `.rpm` (x86_64, aarch64), built from the released wheel and installed offline in containers before the release is created (GI-04).
- GitHub Action: `uses: t00m/KB4IT@vX.Y.Z` installs KB4IT with uv, runs `kb4it verify` (any problem fails the step) and `kb4it build`, and writes a job summary with the version and the build counters. Inputs: `config`, `version` (empty: the KB4IT of the action itself), `python-version`, `extras`, `verify`, `force`; outputs: `target`, the absolute path of the built site, and `version`. It runs on Linux, macOS and Windows runners and never deploys (GA-01).
- CI workflow `action`: runs the GitHub Action of the same commit with `uses: ./` on Linux, macOS and Windows, checks its outputs, and checks that a broken link makes it fail (GA-02).
- Help page "GitHub Action" lists the action inputs and outputs and how to pin its version; "Publish on GitHub Pages" uses the action, and keeps the plain commands as an alternative. `README.md` mentions the action, `RELEASING.md` says how to list a release on the GitHub Marketplace and that there is no moving `v0` tag, and `AGENTS.md` describes the distribution scripts and the action (GA-04).
- `scripts/devel/theme_snapshot.py --content DIR` also saves every page of each sample site, normalised (build dates, times and the version replaced), with the documents of `tests/fixtures/audit/` added, so `diff -r` of two runs shows every change in the HTML a theme or template change makes.
- `kb4it verify` warns with `MD_FENCE_IN_BLOCK doc=... lines=...` about a fenced code block inside an admonition or a list item, which the default extensions render as inline code; the warning does not fail the check, and it is silent when `pymdownx.superfences` is enabled. The document format help explains both ways to write such code (OC-05, MD-01).
- Themes can escape template output: with `"autoescape": true` in `theme.json`, every `${...}` is HTML-escaped unless it is marked `| n`. KB4IT's common templates are always escaped. A custom theme without the key prints values as before and gets one `[BUILDER] THEME_AUTOESCAPE_OFF` warning per build. `scripts/devel/escape_audit.py` lists the expressions of a theme for review, and the theme how-to explains the flag (SC-01, SEC-01).
- `"markdown": {"sanitize": true}` cleans the HTML of each document with [nh3](https://nh3.readthedocs.io/): what Markdown and the bundled extensions make stays, while scripts, styles, event handlers, `javascript:` links and `data:` URLs other than images go. Off by default; nh3 joins the `extras` (also in the GitHub Action and the container image). With it off, `kb4it verify` lists documents holding a script or an `on...=` handler outside code (`DOC_RAW_SCRIPT`, information only), and the help explains the trust model (SC-02, SEC-02).
- `scripts/devel/validate_html.py` builds the sample site of every bundled theme (with the audit documents) and checks every page with the Nu HTML Checker, ignoring only the UIkit `uk-*` attributes; CI runs it in the `package` job, so the markup fixed in this release stays valid (TS-02, TST-02).
- Tests for the failure branches of the compiler: a document that cannot compile, a page that runs out of memory and a progress callback that fails; the next build makes the failed pages. Test coverage, with the builds the tests start in their own process, rose from 85% at the audit to 91% (TS-01, TST-01).

### Changed

- KB4IT no longer stops with "KB4IT only runs in GNU/Linux systems" when the system has no `/etc/os-release`, and no longer reads `/proc` at start-up; on macOS and Windows the platform is described with Python's `platform.platform()`. The debug log names the platform family (CP-01).
- The lock moved from `~/.kb4it/var/kb4it.lock` to each knowledge base (`var/kb4it.lock`), and it uses `flock` on Linux and macOS and `msvcrt` on Windows. Two knowledge bases can now build at the same time, and listing themes, apps or projects, `info` and `verify` never wait for a build. A second build of the same knowledge base still stops with exit status 1 and names the PID that holds it. `projects.json` is written under a short lock, so two `kb4it create` runs cannot lose an entry (CP-02).
- `kb4it create` writes `bin/compile.cmd` on Windows instead of `bin/compile.sh`. Both scripts quote the path of `repo.json`, so a knowledge base in a folder with spaces builds with them; `compile.sh` starts with `#!/bin/sh` (CP-04).
- KB4IT is declared OS independent on PyPI, and the install page explains how to install it on Windows (PowerShell) and macOS (CP-08).
- `kb4it verify` also checks the links between documents: a link to a missing document (`LINK_BROKEN`) or to a missing section (`ANCHOR_MISSING`) is reported and makes it exit with status 1. A build still only warns (KG-02).
- The `.deb` package is built per architecture (`build_deb.sh amd64` or `arm64`) and carries the wheels of every dependency, so it installs without network access; it no longer runs `pip install --upgrade pip` during installation. It refuses, with a clear message, a `python3` it has no wheels for. `scripts/distribution/test/test_packages.sh` builds it and tests install, a smoke build and removal in Debian 12 and Ubuntu 24.04 containers with networking off (DS-04).
- The `.rpm` package is built per architecture (`build_rpm.sh x86_64` or `aarch64`, in `dist/rpm_build/`) from the release wheel and the dependency wheels, so `rpmbuild` and the installation need no network; it no longer builds a second wheel with `pip install --user build`. It requires any Python from 3.11 to 3.14 as `python3` or as `python3.11` to `python3.14`, so it installs on RHEL 9, Rocky Linux 9 and AlmaLinux 9 next to their Python 3.9. `%post` uses the newest supported Python it finds and logs which one; `test_packages.sh rpm` tests it in Fedora and Rocky Linux 9 containers (DS-03).
- The container image installs the release wheel with its extras on `python:3.13-slim`, instead of building its own wheel on 3.12. It runs as the non-root user `kb4it` (UID 1000), works in `/work`, exposes port 8642 for `kb4it serve`, keeps its per-user files in `/tmp/kb4it` so it also runs with `--user "$(id -u):$(id -g)"`, and carries the OCI labels (version, revision, source, licence, documentation). `scripts/distribution/docker/smoke.sh IMAGE` checks the version, a build owned by the calling user and `serve` (GI-01, DS-07).
- `scripts/distribution/README.md` describes what each distribution script builds and needs, and the help page "Install KB4IT" has a section on the `.deb` and `.rpm` packages (DS-09).
- `README.md` and the help page "Install KB4IT" show how to run KB4IT from the container image with Docker or Podman (with `:Z` on SELinux hosts), and where to find the Linux packages. `RELEASING.md` and the help page "Release a version" describe the image and package jobs, what to do when one fails after the PyPI upload, and the one-time step that makes the image public on GitHub (GI-05).
- The help site is built and checked with the KB4IT GitHub Action of the same commit (`uses: ./`), so every change to the help also tests the action (GA-03).
- The help pages "Command line" and "GitHub Action" list every case in which `kb4it build` ends with status 1, including a page that could not be made (BO-03).

### Fixed

- A second build in the same process, as the TUI does, reused the templates loaded by the first build: an edited template was ignored, and a second project whose theme shares a template name with the first rendered the first theme's template. Template caches now belong to each build (FX-01).
- Pages, logs and theme files are always read and written as UTF-8. On Windows, or on Linux with a non-UTF-8 locale, documents with accents failed to build or were written in the wrong encoding, and log lines with accents could stop the build. A test fails when any text file is opened without naming its encoding (FX-02).
- `requirements.txt` was missing `Markdown` and `PyYAML`; a test now keeps it equal to the dependencies in `pyproject.toml`. `pixi.toml` lists macOS and Windows platforms (FX-03).
- Documents and `repo.json` saved with a UTF-8 byte order mark, as some Windows editors do, were rejected (`missing_frontmatter`, or a JSON error). They now load like any other file. CRLF line endings give the same metadata and body hash as LF, so a checkout with `core.autocrlf` does not rebuild every page (CP-07).
- A document whose closing `---` line ends with spaces showed its title twice: the compiler now skips the whole closing line, as the frontmatter reader already did (MD-03).
- `scripts/distribution/build/build_python.sh` exists again: the `.deb` script, `build_all.sh`, the manual PyPI scripts and `install_pipx.sh wheel` called it but it was missing. It removes earlier KB4IT wheels from `dist/` before building, so no script picks a stale one. The distribution scripts share their settings in `scripts/distribution/lib/common.sh`, and a test checks that every script they call exists (DS-01).
- `scripts/distribution/build/build_python.sh` is in the repository: the `build/` line of `.gitignore` had kept it out, so the `.deb` script, `build_all.sh`, the manual PyPI scripts and `install_pipx.sh wheel` called a missing file. It removes earlier KB4IT wheels from `dist/` before building, so no script picks a stale one. The distribution scripts share their settings in `scripts/distribution/lib/common.sh`; tests check that every script they call exists and that no script is ignored by git (DS-01).
- The `.rpm` spec and the container `Dockerfile` name `CHANGELOG.md` instead of the old `Changelog`, so `rpmbuild` and `docker build` no longer stop on a missing file; the `.deb` no longer skips its documents silently. The `.deb`, the `.rpm` and the container image share one description, which lists the four bundled themes (DS-02).
- `scripts/install/local/install_kb4it_from_source.sh` lists its real requirements (uv, or pipx with Python 3.11 or newer) instead of asciidoctor. With uv it needs no Python in `/usr/bin`, so it also works on macOS; with pipx it passes the newest Python 3.11+ it finds in `/usr/bin` or on `PATH`. It works from any folder and no longer deletes `dist/` (DS-02).
- `scripts/uninstall/local/uninstall.sh` removes KB4IT installed with uv, pipx or `pip --user`, whichever has it, instead of only pip. `--purge` also deletes `~/.kb4it` (or `KB4IT_HOME`) after asking. The unused install routine with `pip --trusted-host`, which turned off certificate checks, is gone (DS-06).
- A page that cannot be made now fails the build: `kb4it build` exits 1, logs `[WORKFLOW] PAGES_FAILED` with the page names, and the summary (also in the GitHub Action job summary and the `on_build_end` hook) has a `failed=` count. Before, a page whose Markdown or template failed was only logged and the build reported success. Every other page is still deployed, and the deployer no longer stops at the first page missing from its cache (COR-01, COR-09).
- `var/db/kbdict.json` is written only after a build succeeds. Before, it was written during the analysis, so after a failed or interrupted build the next incremental build treated the changed documents as done and kept serving their old pages until `--force` (COR-02).
- The build refuses a `target` folder that is, or holds, the repository root, `source`, `config/`, `var/`, the home folder or a filesystem root, or that lies inside `source`; before, `"target": "."` let the deployer delete files of the repository (FS-01, COR-03).
- The deployer removes from `target` only the pages that an earlier build recorded as its own (`deployed` in `var/db/kbdict.json`). Other `.html` files you keep in `target` are no longer deleted, and the first build after an upgrade deletes nothing. The unused step that emptied the whole target is gone (FS-01, COR-03).
- JSON files (`projects.json`, `var/db/kbdict.json`) are written to a temporary file and then moved into place, so a crash or a full disk leaves the old file whole. An unreadable `projects.json` is kept as `projects.json.corrupt-<timestamp>` with a `PROJECTS_CORRUPT` warning instead of being replaced by a list holding only the new project; an unreadable `kbdict.json` logs `KBDICT_CORRUPT` and the build runs as a full rebuild instead of failing (FS-02, COR-04).
- Changing a `repo.json` setting that a theme can print, such as `title`, `tagline` or a theme option, rebuilds every page. Before, unchanged documents kept the old header until `--force`. `workers`, `force`, `fail_on_invalid`, `source` and `target` do not trigger a rebuild (OC-01, COR-05).
- A template that exists but does not compile (an override, a custom theme) fails the build with `[BUILDER] TEMPLATE_COMPILE_FAIL`, the file and the line, logged once. Before, it was skipped in silence and the theme's own template was used, or the build said the template was not found (OC-02, COR-06).
- The document title is the first `# ` heading outside fenced and indented code blocks. Before, a `# comment` in a shell or Python block above the title became the title. The same rule finds the line that the page body leaves out and that the change detection ignores (OC-03, COR-07).
- A blog post without `Date` no longer stops the blog: it is listed after the dated posts, has no calendar line, and is logged once with `[THEME] DOC_UNDATED`. An unexpected error now prints its type and the log file, as in `Error: KeyError: 'Date' (see <repo>/var/log/kb4it.log)`, instead of the bare message (OC-04, COR-08).
- With `pymdownx.superfences` and the default `"highlight": "client"`, code blocks get plain `language-*` classes for highlight.js instead of Pygments markup without its stylesheet; `pygments` mode still gives Pygments markup and `pygments.css`. `scripts/devel/test.sh` installs `pymdown-extensions`, so these paths run in CI (OC-05, MD-03).
- Help pages "Customize templates", "Create a theme" and "Release" showed the commands of their numbered steps as inline code; the new `verify` warning found them, and they are now code blocks (MD-01).
- Page names made from property names and values never start with a dot. A property such as `.note` used to make a hidden key page that was never built, and with it no page reached the target; it now makes `note.html`. A property name or value that cleans to nothing, such as `...`, makes the document invalid (`bad_property_name` or `bad_property_value`, so `fail_on_invalid` applies) instead of breaking the site (SC-03, SEC-03).
- Links in documents are no longer rewritten: the `HTML_TAG_A` transformation added an empty `target=""` and `class=""` (techdoc, blog) or a second `class` to links that had one (bookshelf, where it also overrode the tag cloud style). bookshelf colours document links with CSS instead, and the blog key modal title no longer gets a second `class` (HT-01, HTML-01).
- blog marks document sections with the classes `kb-sect1` to `kb-sect4` and `kb-section-body` instead of the same `id` on every section, which repeated ids on any page with more than one section (HT-01, HTML-01).
- Valid markup in techdoc and blog pages: the blog footer no longer closes two `div`s it never opened; the blog home page gives the metadata and source dialogs of each post their own ids; the datatable tooltips are a `span`, not a `div` inside a `span`; the techdoc contents menu no longer puts a list inside a list; the techdoc logo has `width="24"` instead of `24px`; and the styles of the techdoc "Add" page moved from a `<style>` element in the body to `screen.css`. The Nu HTML Checker reports no errors on the techdoc sample site other than UIkit attributes (HT-01, HTML-01).
- Accessible defaults for new sites: the sample `repo.json` files of techdoc and blog no longer carry `{placeholder}` values (`logo_alt` is empty, the `git_*` keys are gone), the logo falls back to the site title as its `alt`, and the "Built with KB4IT" badge has an `alt`. Edit and "Create new post" links appear only when `"git": true` and the git server, user, repository and branch are set; before, every blog post linked to `{https://{server.fqdn}/...}`. Every page of techdoc and blog has one `h1` and a `<main>` landmark (blog posts use their title, other blog pages a heading for screen readers), and bookshelf pages without a heading get the page title (HT-02, HTML-02).

### Removed

- The unused `exec_cmd` helper, which ran commands through a shell (`shell=True`). A test now checks that no module of the package uses a shell (FS-03, BASE-01).

### Security

- apphelp escapes template output (`"autoescape": true`); only the page body, the `aria-current` attribute and the labels for the scripts are printed raw. Its explicit `| h` filters are gone (SC-01, SEC-01).
- techdoc escapes template output. Titles, property names and values, dates and the document source shown under "Source" print as text; before, a value such as `<img src=x onerror=...>` ran in every page that listed it. The tables, the date cells and the tooltips that techdoc builds in Python escape the values they hold, and the JSON of the "Add" page cannot close its `<script>` (SC-01, SEC-01).
- blog escapes template output. Post titles, property names and values and the source shown under "Source" print as text; the tables and tooltips it builds in Python escape the values they hold (SC-01, SEC-01).
- bookshelf escapes template output. Book, part and chapter titles, authors, tags and other property values print as text; the separators next to them stay as they were, and the tables it builds in Python escape the values they hold. All four bundled themes now escape (SC-01, SEC-01).

---

## [0.8.0] - 2026-10-03

### Fixed

- A second build in the same process, as the TUI does when you compile another project, ran the first theme's logic. Each theme load now imports its own `logic/theme.py`.
- `kb4it themes` no longer logs `'Backend' object has no attribute 'repo'` while listing apphelp.
- `kb4it create` with an unknown theme exits 1 instead of 0.
- blog: posts without an `Author` were left out of the index page (`INDEX_SKIP`) and rendered without the post layout.
- TUI: a failed build showed "Done" instead of "FAILED". After a build, the project screen now refreshes, so Explore, View Build Log and Browse are enabled without leaving the project.
- apphelp: table columns no longer break words in the middle; a wide table scrolls instead.

### Added

- User help at https://t00m.github.io/KB4IT/, built with the apphelp theme from `help/`: getting started, installing, writing documents, building, the terminal interface, publishing, the four themes, creating a theme, a command and settings reference, troubleshooting, and development notes. `.github/workflows/help.yml` builds it on every push that touches the help or the code and publishes it from `master` (#68).

- Tests for the command line (`themes`, `apps`, `projects`, `info`, `create`, configuration and theme errors, `--force`, the process lock), the `kb4it.core.util` helpers, the techdoc, blog and bookshelf themes, and every TUI screen. Line coverage of `kb4it` goes from 60% to 90%.

### Changed

- CI and the publish workflow use the current major versions of their GitHub Actions (`checkout` v7, `upload-artifact` v7, `download-artifact` v8, `setup-uv` v10.2.0), which run on Node 24 instead of the deprecated Node 20. A downloaded build that does not match its recorded hash now fails the publish workflow. `setup-uv` is pinned to a full version because it publishes no `v10` tag.

### Removed

- `docs/`, which held an empty page and an example of an API that no longer exists. The help in `help/` replaces it.

---

## [0.7.10] - 2026-10-03

### Fixed

- A source document with unreadable frontmatter (for example an unquoted value containing `: `) no longer vanishes silently. It is recorded in `BuildPlan.invalid_docs` and counted as `invalid=N` in the build summary, and the log gives the YAML line, column and problem.
- apphelp: with `strict` on, an invalid document fails the build as `DOC_INVALID`, together with the other metadata problems.
- `kb4it verify` exits 1 when it finds a non-conformant file or a theme problem, so it can gate CI.
- `kb4it create` makes the `source/` and `target/` folders when the theme's sample app has none. Git cannot store empty folders, so `kb4it create bookshelf` from a git checkout or a PyPI install produced a repository that did not build.

### Added

- `repo.json` switch `fail_on_invalid` (default `false`) makes any theme fail the build on invalid documents.
- apphelp: theme documentation in `kb4it/resources/themes/apphelp/README.md`.
- The `kb4it` requirement in a theme's `theme.json` (for example `">=0.7.9"`, or `">=0.7.9, <0.8"`) is enforced: a theme that needs a newer KB4IT is refused with `THEME_REQUIREMENT_UNMET`, and an unreadable requirement with `THEME_REQUIREMENT_INVALID`. A theme without one loads with a warning.
- `kb4it --version` run from a git checkout adds `git describe`, so a development build is identifiable without changing any file.
- Release process (`RELEASING.md`): `scripts/release.sh` prepares a release (version, dated changelog, release notes) and commits it only after the tests, the theme check and the wheel check pass. It never tags or pushes.
- `scripts/devel/check_themes.sh` checks every tracked theme before a release: complete `theme.json`, a `kb4it` requirement met by the release, required templates, and sample apps that build with no error or warning. CI runs it too.
- The publish workflow runs on plain `vX.Y.Z` tags only. It checks that the tag matches the committed version, the changelog and the release notes, runs the tests and the theme check, publishes to PyPI with trusted publishing and creates the GitHub release.

### Changed

- apphelp: every page is classified by type of document with `DocType`, the same key and values as `techdoc`: `Tutorial`, `How-to guide`, `Reference` or `Explanation`. A page without a valid `DocType` is left out of the site, the navigation, the search and the help ids, and fails the build when `strict` is on. The landing page groups pages by type of document, and search filters by it.
- apphelp: the `Kind` key is replaced. Use `DocType` for the type of document and the optional `Layout` key (`faq`, `tips`, `troubleshooting`) for the special renderings. A page that still has `Kind` is reported as `META_INVALID`.
- apphelp: the labels `kind_*` and `facet_Kind` are now `doctype_*` and `facet_DocType`.

### Removed

- `setup.py`, unused since the build moved to `pyproject.toml`.
- `scripts/devel/genbuild.py` and the `+build.N` counter it wrote into `kb4it/VERSION` and `pyproject.toml` on every local install. PyPI rejects such versions, and the changing version forced every site to recompile after each install.
- The legacy upload scripts in `scripts/distribution/pip/` and `scripts/distribution/deb/create_deb.sh`, which used `setup.py`.

---

## [0.7.9] - 2026-10-01

### Added

- New theme `apphelp`: help sites for applications, with strict metadata, offline search, help ids and `go.html`.
- `theme.json` `metadata_pages` turns the metadata pages off.
- `theme.json` `deploy_dirs` deploys only the listed theme folders.
- `repo.json` `publish_sources` controls copying the sources to the target.
- Optional `logic/verify.py` theme hook, run by `kb4it verify`.
- `Builder.site_signature()` rebuilds every page when the site shape changes.
- Tests run with `./scripts/devel/test.sh`; CI runs them and checks the wheel for every tracked theme.

### Changed

- Markdown links to `.md` files are rewritten to `.html`, keeping the fragment; unknown targets log `LINK_BROKEN`.
- `source` and `target` are relative to the repository root (`PATH_CWD_RELATIVE` fallback); `kb4it create` writes them that way.
- The backend no longer writes into `source/`; `Builder.create_page_about_app()` builds the about page.
- `Date` is optional; undated documents come after dated ones and show an empty date cell.
- YAML null frontmatter values become `[]`.
- Custom themes: the about pages are no longer added for every theme. A custom theme must call `create_page_about_kb4it()` and `create_page_about_app()` in its `build()` to get them. An untouched generated `source/about_kb4it.md` from older versions is removed.

---

## [0.7.38]

### Theme: Techdoc: Document view

- **Collapsible TOC**: a `<details>` panel appears at the top of every document; open by default, collapses on click. Renders correctly in print (forced open, no max-height).
- **Redesigned headings**: `h2`/`h3`/`h4` now carry a coloured left-accent bar (blue gradient by depth) instead of the generic UIKit card title style.
- **Collapsible sections**: clicking any `h2` heading toggles the section body open/closed. The indicator arrow (`▾`/`▸`) is rendered via CSS `::after` to avoid HTML-entity display bugs in `textContent`.
- **Document Properties section**: document metadata moved from a hidden top block to a collapsible `kb-sect1` section at the end of the document. Collapsed by default on screen; forced open and link-free in print. Keys are bold; values are comma-separated inline links.
- **Print CSS overhaul**:
  - Page margins reduced from `1.5cm 2cm` to `1cm 1.5cm`.
  - Line height reduced from `1.6` to `1.35`; paragraph spacing from `6pt` to `4pt`.
  - Document title block shown in print (hidden on screen).
  - TOC included in print output.
  - Metadata values displayed as a bullet list (sans-serif, black, no URL suffixes).
  - Section card padding zeroed; `uk-card-body` padding suppressed.
  - All collapsed section bodies forced visible in print.
- **Print button**: added to the document actions bar.
- **Add document page**: new page with per-category AsciiDoc skeletons loaded from `.adoc` files; copy-to-clipboard button restored and modernised.
- **Add document: metadata form**: clicking *Create* now opens a two-step modal. Step 1 is a form with one field per AsciiDoc attribute in the skeleton; step 2 shows the filled skeleton ready to copy. `Date` auto-fills to today; `Category` is read-only; all other fields support free-text entry.
- **Add document: multi-select tag chips**: keys with known values in the live metadata database render as clickable chip selectors (multiple values selectable). Keys with more than 8 known values open a popup picker with a live filter, custom-value entry, and a *Clear all* button, avoiding cluttered chip clouds in the form.
- **Copy-to-clipboard**: migrated to `navigator.clipboard` API with `execCommand` fallback.

### Theme: Techdoc: Landing page

- **Hero stats bar**: document counts per Diataxis category link to their respective listing pages. Diataxis count corrected; avoids 404 when a category has no documents.
- **Changes/Incidents alert bar**: two-column panel showing recent changes and open incidents.
- **Upcoming events**: panel now shows only future events; month headers and alert bar headers are clickable links.
- **Color-coded category labels**: event tables show labels with uniform fixed width and per-category colour.
- **Landing page layout reorganised**.

### Theme: Techdoc: Events

- Events page replaced year-card layout with a year-selector, 12-month calendar grid, and a DataTable.
- Unchanged event pages are skipped during recompilation.

### Theme: Techdoc: Other pages

- Key-value, key, and stats pages redesigned with modern CSS (word cloud, bar charts, breadcrumbs).
- Help page is auto-generated when the repository has no `help.adoc`.

### Theme: Blog

- "Read more…" link appended after each post excerpt on the index page.
- New index page renders posts by excerpt instead of full content.
- Visual and style improvements to datatables and post layout.

### Core: Performance

- **Incremental deployment**: deployer now copies only new or changed files and deletes stale ones, skipping unchanged assets.
- **Incremental compilation**: split body/metadata hashes ensure key pages are recompiled whenever any document's metadata changes.
- **BLAKE2b hashing**: replaced MD5 with BLAKE2b for content and file hashing.
- **Compiler**: removed random sleep from `compilation_finished` callback.

### Core: Features

- `Date` is now the hardcoded sort key for all themes; the configurable `sort` property is removed.
- `About KB4IT` source page is auto-created in the repository if missing.
- Mako templating library updated from 1.3.6 to 1.3.11.
- `Date` key is blocked from appearing in the stats page and word cloud.
- Keys listed in `ignored_keys` are excluded from stats and word cloud.

### Core: Bug fixes

- **Template cache race condition**: `builder.template()` previously cached `Template("")` between fallback attempts, causing concurrent compiler workers to read a half-built entry and render empty content. Downstream `content.replace("", …)` then exhausted memory. The cache is now locked and only populated on success.
- `kb4it themes` command restored after a regression caused by repo-dict loading during theme listing.
- `ignored_keys` now loaded correctly from repo config.
- Backend and deployer fail early with a clear error when runtime theme data is missing.
- `reason` variable in `get_asciidoctor_attributes` initialised to prevent `UnboundLocalError`.
- Removed stale references to the `Updated` document property.
- Theme pages are registered as build targets even when not recompiled in the current run.
- Invalid (non-AsciiDoc) documents are excluded from the compilation pipeline.
- Successful compilations no longer emit a spurious error-level debug message.

### Refactoring / Chores

- Dead code removed and missing docstrings added across core and service modules.
- Debug log format unified across all modules for diff-friendly output.
- Core modules (`env`, `log`, `service`, `util`) and service modules (`backend`, `builder`, `compiler`, `deployer`, `frontend`, `processor`) reformatted and cleaned up.
- README revised for clarity and updated information.

---

## [0.7.26] and earlier

See git history.

---

## [0.7] - 2019-11-15

### Added

- Asciidoctor 2.0.
- Layout based on UIkit.
- Smart compiling.

## [0.6] - 2019-09-10

- Released.
