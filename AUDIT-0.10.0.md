# KB4IT 0.10.0 audit

Read-only audit of the checkout at `f87ac63` (`0.10.0`). The only repository file
created for this audit is this report. The worktree already had unrelated
untracked `claude/`, `skills/`, and `uv.lock` entries, and a modified `.gitignore`;
they were not changed.

## Executive summary

- Overall risk: **Moderate**. No confirmed critical or high severity issue was found.
- Confirmed medium issue: static asset symlinks can copy files outside the repository into the published site.
- Post-audit follow-up: COR-15 is fixed; the focused suite passes 29 tests and the full suite passes 1,549 tests (179 skipped).
- A minimal `KB4IT()` construction still raises `KeyError` when `log_level` is omitted.
- Strict CI typing and theme compliance pass; ordinary package-wide mypy reports 63 errors.
- Generated sample HTML is valid: 175 pages, zero Nu checker errors or warnings.
- Coverage is 74%. Browser tests were skipped because Chromium and Playwright were unavailable.
- The 2,000-document first build took 38.8 seconds; a one-document incremental build took 2.63 seconds.

## Phase 0: Inventory

### Scope and architecture

KB4IT is a Python static-site generator. `kb4it/core/main.py` exposes the CLI and
controller; `kb4it/__main__.py` supports `python -m kb4it`. CLI actions include
`create`, `build`, `serve`, `info`, `verify`, `themes`, `apps`, and `projects`.
With no arguments in an interactive terminal it launches the Textual TUI. The
GitHub Action is the composite action in `action.yml`, which calls
`scripts/action/run.sh`. Build hooks and custom theme Python code execute
in-process.

The normal build flow is `Workflow` -> `Backend` -> per-build `Pipeline`
(`Processor`, `Compiler`, `Deployer`) -> theme `Builder` -> target directory.
Markdown frontmatter and BLAKE2b hashes feed the incremental `BuildPlan`; Mako
templates and python-markdown produce HTML; static resources and pages are
deployed incrementally. `serve` holds a repository lock while its polling
watcher triggers builds and the standard-library server serves the target.
The editor uses the browser File System Access API or a download fallback; there
is no HTTP save endpoint.

Main packages are `kb4it/core`, `kb4it/services`, `kb4it/tui`, and the four
bundled theme trees under `kb4it/resources/themes/{techdoc,blog,bookshelf,apphelp}`.
Templates, offline help, editor resources, and Mermaid/KaTeX resources ship under
`kb4it/resources/`. Distribution and release scripts live under `scripts/`.

### Change since the previous audit

The referenced commit `b5330aa` is not present in this checkout's Git object
database, so a direct diff against it was not possible. I compared the available
release base `0.9.1` to `HEAD`: 241 files changed, 19,081 insertions and 1,638
deletions. Major additions include the CodeMirror editor, Mermaid and KaTeX
rendering, richer techdoc document/media and quality features, `DocumentTheme`
and themed shared services, extracted TUI screens, improved incremental
deployment, and updated help and packaging. The TUI is now split across screen
modules; the largest counted Python module is 560 lines, under the repository's
600-line limit.

### Phase 0 top five

| Priority | Area | Reason |
|---|---|---|
| 1 | Static asset symlinks | The deployer copies symlink targets into public output. |
| 2 | Techdoc quality scores | Resolved after the audit; see COR-15 follow-up. |
| 3 | Cleanup of temporary folders | Directory symlinks still make cleanup raise. |
| 4 | Dependency inputs | Test scripts pin a different Mako than package metadata. |
| 5 | Compatibility and typing | The deprecated service locator and package-wide type errors remain. |

## Phase 1: Automated baseline

### Results

| Check | Result |
|---|---|
| `./scripts/devel/test.sh` (audit baseline) | 1,545 passed, 4 failed, 179 skipped; 1,728 collected, 6:04. The four failures are listed under COR-15. |
| `./scripts/devel/test.sh` (post-fix) | 1,549 passed, 179 skipped; 1,728 collected, 5:43. |
| Browser tests | Skipped by the normal suite; Chromium was not installed and Playwright was unavailable. |
| `./scripts/devel/typecheck.sh` | Passed: mypy strict on the configured 13 source files/modules. |
| Normal mypy | `mypy --ignore-missing-imports kb4it`: 63 errors across 16 files, 83 source files checked. This is consistent with ARC-07 being only partially addressed. |
| `./scripts/devel/check_themes.sh` | Passed for apphelp, blog, bookshelf, and techdoc. |
| `ruff check .` | 248 diagnostics; no Ruff job or chosen Ruff configuration is present in CI. Most output is lint/import hygiene and was not treated as product defects. |
| Bandit | No high findings; 3 medium and 17 low on the package. The medium reports were reviewed: PyYAML uses a `SafeLoader` subclass, the all-interface report concerns the URL display mapping, and the Mako report does not account for the configured theme escaping. |
| Vulture | Two high-confidence dead items: `Optional` in `core/types.py` and `parameters` in `tui/screens/main.py`. |
| Radon | Average cyclomatic complexity A (3.90); maintainability index A for all inspected modules except `techdoc/logic/theme.py` at B. |
| `pip-audit -r requirements.txt` | No known vulnerabilities found. `pip-audit --locked .` found no supported Python lockfile. The checked-in Pixi lock is not understood by pip-audit; the pre-existing untracked `uv.lock` has only three metadata lines and no package resolutions. |
| Wheel and sdist | `uv build --sdist --wheel --out-dir /tmp/kb4it-audit-dist` succeeded. The wheel is 9,807,275 bytes with 2,376 files and all four themes, the editor bundle, and Mermaid resource; sdist is 8,049,573 bytes. |
| `scripts/devel/check_themes.sh` | Passed, as above. |

### Phase 1 top five

| Priority | Finding or area | Why |
|---|---|---|
| 1 | SEC-09 | A contributor-controlled symlink can disclose host/repository files into published output. |
| 2 | BASE-02 | The controller's documented default log-level path still crashes. |
| 3 | COR-11 | A directory symlink in cleanup input raises `OSError`. |
| 4 | DEP-02 | CI tests the old Mako pin rather than the declared runtime version. |
| 5 | COR-12 | Nested YAML mappings are converted to Python representation strings. |

## Phase 2: Correctness and robustness

The passing suite exercises frontmatter parsing, header cache reuse, rename and
delete behavior, incremental deployment, lock handling, Markdown links, and
failure exits. The BLAKE2b/header cache work is covered by `test_header_cache.py`;
the 2,000-document benchmark below confirms one changed document is recompiled
without recompiling the other 2,001 pages (including generated pages). No
separate stress test was made for enormous frontmatter or Windows/macOS path
semantics on this Linux host.

### Confirmed findings

**BASE-02 - Severity: Low - Incomplete prior finding**

Evidence: [kb4it/core/main.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/core/main.py:84)
sets `LOGLEVEL` when `log_level` is absent, then reads `log_level` at line 86.

Reproduction: `HOME=/tmp/kb4it-empty-home USERPROFILE=/tmp/kb4it-empty-home KB4IT_HOME=/tmp/kb4it-empty-home PYTHONPATH=$PWD python3 -c 'from kb4it.core.main import KB4IT; KB4IT()'`.
Observed: `KeyError: 'log_level'` at `KB4IT.__init__`.

Impact: library or embedded callers that construct `KB4IT` without argparse's
`log_level` cannot initialize. Minimal fix: use
`self.params.setdefault("log_level", "INFO")` before `setup_logging`.

**COR-11 - Severity: Low - Incomplete prior finding**

Evidence: [kb4it/core/files.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/core/files.py:192)
checks `isfile()` before calling `shutil.rmtree()` on everything else. A symlink
to a directory is not a regular file, and `rmtree` rejects symlinks. The cleanup
is called on `var/tmp` and `var/www` by
[deployer.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/services/deployer.py:397).

Reproduction: create a temporary directory `tmp`, create `outside/`, then add
`tmp/link -> outside` and call
`delete_target_contents(str(tmp))` from `kb4it.core.files`. Observed:
`OSError: Cannot call rmtree on a symbolic link` at `files.py:195`; the cleanup
and build abort. Minimal fix: test `os.path.islink()` first and unlink the link.

**COR-12 - Severity: Low - Incomplete prior finding**

Evidence: [kb4it/core/documents.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/core/documents.py:261)
converts non-list, non-string frontmatter values with `str(v)`.

Reproduction input: `Meta: {a: 1}` and `Author: Virseda, Tomas` in frontmatter
followed by `# Title`; call `parse_markdown_attributes` on that Markdown. Observed:
`{'Meta': ["{'a': '1'}"], 'Author': ['Virseda', 'Tomas'], ...}`. Minimal fix:
reject mappings as `DOC_INVALID`, and document quoted/list syntax for comma-bearing
values.

**COR-14 - Severity: Low - Incomplete prior finding**

Evidence: [kb4it/core/publish.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/core/publish.py:69)
replaces `T` and appends `Z` without preserving a supplied time-zone offset.

Reproduction: `PYTHONPATH=$PWD python3 -c 'from kb4it.core.publish import atom_date; print(atom_date("2026-10-08T14:30:00+02:00"))'`.
Observed: `2026-10-08T14:30:00Z`, two hours different from the input instant.
Minimal fix: parse ISO-8601 and preserve/normalize offsets; define a policy for
naive timestamps.

### Phase 2 top five

| Priority | Finding | Why |
|---|---|---|
| 1 | BASE-02 | Direct controller construction raises instead of using its documented default. |
| 2 | COR-11 | A symlink in a cleanup folder aborts cleanup. |
| 3 | COR-12 | Valid nested YAML is silently changed into Python representation text. |
| 4 | COR-14 | Atom readers receive a false UTC instant for offset dates. |
| 5 | SEC-09 | A source asset symlink can copy an external file into published output. |

## Phase 3: Security

**SEC-09 - Severity: Medium - Static asset symlink escape**

Evidence: [kb4it/core/files.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/core/files.py:153)
walks source files and passes each path to `sync_file` without checking whether
it is a symlink or whether its resolved target remains under `source/resources`.
[deployer.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/services/deployer.py:190)
deploys that tree into `target/resources`.

Reproduction: in a scratch repository, put `private-config` in
`repo/config/private.txt`, then create
`repo/source/resources/leak.txt -> ../../config/private.txt` and build the site.
The equivalent `sync_tree` reproduction returned `(1, 0, {.../site/resources/leak.txt})`
and reading the deployed file returned `private-config`.

Failure scenario: a build of an untrusted checkout (or a local checkout later
published) can copy any readable file reachable through a committed symlink into
the public site. The attack requires a build and publication step, but not a
custom hook. Minimal fix: reject symlinked files or resolve and enforce
containment within each asset root before copying; add a build regression test.

### Security checks and limits

- Hostile frontmatter escaping and optional Markdown sanitization tests pass.
  The existing trust model still allows raw HTML unless `markdown.sanitize` is
  enabled; this is documented behavior for trusted repositories.
- `site_url` Atom attribute quoting remains malformed for a quote in the URL;
  see SEC-06 below. This is a format/integrity issue, not an exploitable script
  path in this static feed.
- The techdoc `admin` setting intentionally writes guessable source/site ZIPs to
  the static target. `help/source/reference-theme-techdoc.md:235-242` explicitly
  tells public-site operators to protect `admin/` or disable the feature; no new
  finding is raised for documented behavior.
- The local server binds to `127.0.0.1` by default; `--host 0.0.0.0` is
  documented as network-visible. The status endpoint is read-only. The editor
  writes through browser file APIs/downloads, not an HTTP endpoint.
- Vendored versions are Mermaid 11.17.2 and KaTeX 0.19.0. The reviewed Mermaid
  advisories describe affected releases below 11.16.1 (for recent configuration
  issues) and the KaTeX advisory describes affected releases below 0.18.2; the
  bundled versions are newer. Sources: [Mermaid advisory](https://github.com/advisories/GHSA-c4c3-pg64-4m4v),
  [KaTeX advisory](https://github.com/advisories/GHSA-238p-pmpm-9mq7). CodeMirror
  packages are versioned in `kb4it/resources/editor/VERSIONS`; no matching
  advisory was found in the reviewed searches. This is not a substitute for
  continuous upstream monitoring.
- `bandit`'s `B506` result is a false positive for a `yaml.SafeLoader`
  subclass. Frontmatter size is not bounded; no YAML-expansion denial of service
  was reproduced in this audit.

**SEC-06 - Severity: Low - Incomplete prior finding**

Evidence: [kb4it/core/publish.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/core/publish.py:81)
uses XML text escaping inside quoted attributes. `xml.sax.saxutils.escape` does
not escape a quote. `site_url` accepts a quote in a path.

Reproduction: `PYTHONPATH=$PWD python3 -c 'from kb4it.core.publish import site_url, atom_feed; base=site_url({"site_url":"https://example.test/\""}); print(atom_feed("x",base,[]).splitlines()[1])'`.
Observed: `<feed ... xml:base="https://example.test/"/">`, which is malformed XML.
Minimal fix: use `quoteattr` for attributes or build the feed with an XML
serializer; escape `<updated>` as element text too.

### Phase 3 top five

| Priority | Finding or area | Why |
|---|---|---|
| 1 | SEC-09 | Published output can contain files outside the asset root. |
| 2 | SEC-06 | A quote in the configured URL breaks the Atom document. |
| 3 | SEC-07 | Frontmatter size/alias-resource limits remain unverified. |
| 4 | SEC-04 | Hooks and custom themes execute Python in the build process; review trust at CI boundaries. |
| 5 | Admin ZIP behavior | Explicitly documented, but operators must protect the static `admin/` directory. |

## Phase 4: Architecture and maintainability

`DocumentTheme` and theme mixins are present; the TUI is split into screen
modules; the public-name tests pass; the 600-line module test passes. The strict
typing seam passes as CI currently defines it, but ordinary mypy reports 63
errors. This is the acknowledged partial scope of ARC-07, not a new finding.

`KB4IT.get_service()` still resolves `Processor`, `Compiler`, and `Deployer`
through `_pipeline_service()` at `kb4it/core/main.py:164-187`, despite the
0.10-era plan/docs saying the shim would be removed in this minor version. This
is an incomplete deprecation, not a runtime regression: the compatibility path
still works and logs once per name.

### Phase 4 top five

| Priority | Area | Why |
|---|---|---|
| 1 | ARC-07 | Most of the package remains outside the strict typing boundary. |
| 2 | ARC-03 | Deprecated service-locator shim remains past the stated removal version. |
| 3 | Package-wide mypy | 63 ordinary mypy errors need a staged baseline. |
| 4 | Techdoc theme complexity | `techdoc/logic/theme.py` is Radon MI grade B. |
| 5 | Dead code | Vulture identified two high-confidence unused symbols. |

## Phase 5: Dependencies and packaging

The project metadata and `requirements.txt` agree on the current runtime
dependencies. `test.sh` and `check_themes.sh` do not: both pin Mako 1.3.12 while
`requirements.txt` and `pyproject.toml` specify 1.4.2. The tests therefore do
not validate the declared release dependency. `pixi.toml`/`pixi.lock` remain
tracked third-party environment definitions; the lock records KB4IT 0.7.20 and
Python `>=3.12`, unlike current metadata. `uv.lock` is an untracked, incomplete
local file, not a usable project lock.

**DEP-02 - Severity: Low - Dependency test pin drift (regressed)**

Evidence: [scripts/devel/test.sh](/home/t00m/Documents/devel/github/KB4IT/scripts/devel/test.sh:12)
and `scripts/devel/check_themes.sh:6` use `Mako==1.3.12`; `requirements.txt:1`
and `pyproject.toml:46` require `Mako==1.4.2`.

Reproduction: `./scripts/devel/test.sh` installs the explicit Mako 1.3.12 pin
from line 12, while a normal package install resolves 1.4.2. The baseline passed
most tests on the stale pin but failed four unrelated quality tests; it did not
exercise the declared Mako release version.

Minimal fix: make these scripts use `--with-requirements requirements.txt`, or
derive their constraints from one checked-in source.

### Phase 5 top five

| Priority | Finding or area | Why |
|---|---|---|
| 1 | DEP-02 | CI tests a different Mako version than users install. |
| 2 | DEP-01 | Pixi's lock and project metadata are stale. |
| 3 | DEP-03 | Several runtime dependencies have no upper bounds. |
| 4 | DEP-04/DEP-05 | Recheck vendored payload size and license notices when assets change. |
| 5 | DEP-07 | The CI Python matrix omits declared Python 3.12. |

## Phase 6: Tests and output quality

### Coverage and output

The requested coverage run collected the same 1,728 tests and measured 8,810
statements: 2,268 missed, **74% coverage**. At audit time it reproduced the four
quality failures, with 1,545 passed and 179 skipped. The editor/browser subset was
skipped because Playwright/Chromium was unavailable.

`validate_html.py` passed: **175 pages in 5 sites, 0 errors and warnings**. The
tests cover escaping, editor operation, diagrams, theme output, page landmarks,
and HTML quality. This run did not do a manual contrast/keyboard audit or a
cross-platform browser session.

The synthetic corpus benchmark ran in a temporary directory on Python 3.11. It
created 2,000 Markdown documents with one shared metadata key. First build:
38.801 seconds, 2,002 pages compiled (including generated pages), 8 keys and 14
key/value pages compiled, no failures. After changing one document: 2.630
seconds, 1 compiled and 2,001 skipped. Peak RSS was not measured.

**COR-15 - Severity: Medium - Floating-point quality scores fail CI - Fixed after audit**

Evidence: [techdoc_quality.py](/home/t00m/Documents/devel/github/KB4IT/kb4it/resources/themes/techdoc/logic/techdoc_quality.py:231)
divides a 16-point skeleton score across 3 sections. At lines 238 and 361-363,
those floats are summed without normalization.

Reproduction: `./scripts/devel/test.sh`. Observed: four failures in
`tests/themes/test_techdoc_quality.py`; a complete structured score sums to
`24.999999999999996`, not `25`, so `Check.passed` is false and exact score tests
fail. `score` itself is rounded, but individual dimensions/checks retain the
fractional error.

Fix: commit `cf96b7b` (`fix(techdoc): preserve full skeleton quality scores`).
The scorer gives the final skeleton section the remainder of the structured
dimension maximum after earlier checks, preserving the exact score across Python
versions.

Verification: `./scripts/devel/test.sh tests/themes/test_techdoc_quality.py`
passed (29 passed). The full `./scripts/devel/test.sh` passed (1,549 passed,
179 skipped). Browser tests were skipped because their prerequisites were
unavailable in this run.

### Phase 6 top five

| Priority | Finding or area | Why |
|---|---|---|
| 1 | SEC-09 | No symlink-escape regression test exists. |
| 2 | Coverage | At 74%, with workflow/deployer/theme branches still comparatively low. |
| 3 | Browser tests | 179 skips include the full Chromium suite in this environment. |
| 4 | Accessibility | Static validity is clean; contrast and keyboard navigation still need a browser/manual pass. |
| 5 | BASE-02 | Direct controller construction raises when `log_level` is omitted. |

## Findings by severity

Effort estimates are implementation estimates: S is a focused change, M is a
change with cross-module or test implications, and L spans substantial review.

| ID | Severity | Finding | Evidence | Effort |
|---|---|---|---|---|
| SEC-09 | Medium | A symlink under `source/resources` copies external file contents into public `target/resources`. | `core/files.py:153-180`, `services/deployer.py:190-204`; scratch `sync_tree` reproduction returned the linked file contents. | M |
| COR-15 | Medium | Floating point score accumulation made four quality tests fail and could mark a full structured score as incomplete. **Fixed in `cf96b7b`; focused 29/29 and full 1,549 passed, 179 skipped.** | `techdoc_quality.py:231-240`; pre-fix reproduction and post-fix test runs above. | S |
| BASE-02 | Low | Missing `log_level` default writes the wrong key and raises `KeyError`. | `core/main.py:84-86`; direct `KB4IT()` reproduction. | S |
| COR-11 | Low | Cleanup calls `rmtree` on directory symlinks and aborts. | `core/files.py:192-195`, `services/deployer.py:397-401`; direct symlink reproduction. | S |
| COR-12 | Low | Nested YAML mappings are converted to Python representation strings; comma-bearing scalar values split. | `core/documents.py:261-269`; direct parser reproduction. | S |
| COR-14 | Low | Atom dates discard input offsets and incorrectly append `Z`. | `core/publish.py:69-74`; direct offset reproduction. | S |
| SEC-06 | Low | Quotes in a valid `site_url` break Atom XML attributes. | `core/publish.py:15-26,81-95`; direct feed reproduction. | S |
| DEP-02 | Low | Test and theme scripts use Mako 1.3.12 while package metadata uses 1.4.2. | `scripts/devel/test.sh:12`, `check_themes.sh:6`, `requirements.txt:1`, `pyproject.toml:46`. | S |

## Suggested fix order

1. **Patch series A: protect file roots.** Reject or contain source-resource and override symlinks; test external file, in-root file, and platform-specific path behavior.
2. **Patch series B: completed.** The final skeleton section now receives the remaining structured-score maximum; focused and full test suites pass. Browser tests remain skipped where Chromium is unavailable.
3. **Patch series C: close focused correctness gaps.** Fix the log-level default, cleanup symlink handling, nested YAML mapping policy, Atom escaping, and Atom timezone conversion. Each can be reviewed as an independent change.
4. **Patch series D: align audit inputs.** Use one dependency source in test/theme scripts; decide whether to remove or regenerate Pixi files; add Python 3.12 to CI if it remains supported.
5. **Patch series E: sustain quality.** Add targeted symlink and full-score regression tests, improve coverage on deploy/workflow paths, and stage package-wide typing cleanup.

## Regression check against `AUDIT.md`

Post-audit follow-up: COR-15, introduced by this audit's baseline run, is fixed
in commit `cf96b7b`. Its focused tests and the full 1,728-test collection were
rerun successfully (1,549 passed, 179 skipped).

Status means the finding's prior proposed fix was checked against the current
tree. “Incomplete” includes prior findings that had no recorded fixed status and
remain visible in current code or tooling. Findings with “still fixed” were
checked through relevant code, current tests, or the requested validation run.

| Prior ID | Status | Check |
|---|---|---|
| BASE-01 | Still fixed | `exec_cmd`/`shell=True` helper is absent from the package. |
| BASE-02 | Incomplete | Reproduced `KeyError: log_level`; current finding above. |
| BASE-03 | Incomplete | Two Vulture findings remain; old broader dead-code list was not repeated. |
| BASE-04 | Incomplete | No Ruff CI check; 248 current Ruff diagnostics and 63 normal mypy errors. |
| BASE-05 | Still fixed | Radon average complexity A (3.90); no former D-grade hot-path result reported. |
| COR-01 | Still fixed | Failure tests and full run confirm failed builds return nonzero. |
| COR-02 | Still fixed | Cache commit and incremental failure tests pass. |
| COR-03 | Still fixed | Target overlap checks and deployment ownership tests pass. |
| COR-04 | Still fixed | Atomic JSON writes are present in `core/files.py`; registry and cache tests pass. |
| COR-05 | Still fixed | Core signature includes repo page settings; site-signature tests pass. |
| COR-06 | Still fixed | Broken template compile is distinguished from missing candidates; template tests pass. |
| COR-07 | Still fixed | First-heading tests cover fenced and indented code. |
| COR-08 | Still fixed | Undated blog tests pass. |
| COR-09 | Still fixed | Deployer records missing pages and reports failure; build failure tests pass. |
| COR-10 | Incomplete | Blog renderer still has a broad silent fallback at `blog/logic/theme.py:322-323`; prior scenario not separately reproduced here. |
| COR-11 | Incomplete | Directory symlink cleanup failure reproduced; current finding above. |
| COR-12 | Incomplete | Nested mapping and comma-split behavior reproduced; current finding above. |
| COR-13 | Still fixed | `Builder.get_theme_var()` copies repo settings before adding its timestamp. |
| COR-14 | Incomplete | Offset loss reproduced; current finding above. |
| SEC-01 | Still fixed | Autoescape and hostile-value tests pass; HTML validation is clean. |
| SEC-02 | Still fixed | Sanitization option and raw-script verification are present; trust behavior is documented. |
| SEC-03 | Still fixed | Property filename checks reject empty/invalid paths; regression tests pass. |
| SEC-04 | Incomplete | Hooks remain executable Python; action documentation still needs a clear untrusted-PR warning. |
| SEC-05 | Still fixed | The shell helper noted in SEC-05 was removed with BASE-01. |
| SEC-06 | Incomplete | Quote escaping gap reproduced in Atom output; current finding above. |
| SEC-07 | Incomplete | SafeLoader prevents object construction, but input size/alias cost remains uncapped and was not stress-tested. |
| SEC-08 | Still fixed | Localhost default and exposure warning are documented in preview help. |
| ARC-01 | Still fixed | Shared theme family code now lives in `services/themekit/`. |
| ARC-02 | Still fixed | Module-size test passes; files remain below 600 lines. |
| ARC-03 | Incomplete | Deprecated `get_service()` pipeline compatibility shim remains at 0.10.0. |
| ARC-04 | Still fixed | Path helpers are in `core/paths.py`; import boundaries remain centralized. |
| ARC-05 | Still fixed | Transformation/template-use checks pass; generated HTML validates. |
| ARC-06 | Still fixed | Build callbacks/runtime flags are passed or held per instance; state tests pass. |
| ARC-07 | Incomplete | Strict seam passes, but normal mypy still reports 63 errors across 16 files. |
| ARC-08 | Still fixed | Old root/PyPI leftovers and stale test comment remain removed/updated. |
| DEP-01 | Incomplete | Tracked Pixi files still contain stale package/version metadata. |
| DEP-02 | Regressed | Test/theme scripts pin Mako 1.3.12; current requirements/pyproject use 1.4.2. |
| DEP-03 | Incomplete | Runtime dependency constraints still have no upper bounds on several packages. |
| DEP-04 | Incomplete | Highlight.js and other vendored assets remain; package is 9.8 MB. |
| DEP-05 | Incomplete | No current evidence was gathered that the prior TimelineJS license concern was resolved. |
| DEP-06 | Incomplete | Metadata remains in `[tool.poetry]`, not PEP 621 `[project]`. |
| DEP-07 | Incomplete | CI still omits declared Python 3.12. |
| TST-01 | Still fixed | Failure branches are tested; failures correctly fail builds. |
| TST-02 | Still fixed | Escaping, settings, title, and HTML quality regression coverage is present. |
| HTML-01 | Still fixed | `validate_html.py`: 0 errors/warnings across all 175 checked pages. |
| HTML-02 | Still fixed | Theme HTML quality tests pass. |
| MD-01 | Still fixed | Fence-in-block verification and help guidance are present. |
| MD-02 | Incomplete | Markdown's mixed-list spacing behavior remains; not directly re-tested in this run. |
| MD-03 | Still fixed | Highlight-mode tests pass. |
| HTML-03 | Still fixed | Current Nu validation produced zero errors and warnings. |
| TST-03 | Still fixed | `tests/blog/post1.adoc` is absent. |

