---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-15
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Approved
Tag: specification, audit, architecture, refactoring, themes
Topic: Architecture, Development
---

# KB4IT architecture series specification (group G)

## Overview

The audit fix specification (`responses/KB4IT-0.9-AUDIT-FIX-SPEC.md`) named three
architecture requirements, AR-01 to AR-03, and Decision D-6 moved them to a series
of their own, after the escaping (SC-01) and markup (HT-01) work had changed the
same files. That work is done (patches 0077 to 0107). This specification defines
the architecture series.

It covers the three Medium architecture findings of `AUDIT.md` and, subject to
Decision D-G5, the Low and Info ones of the same phase, since they touch the same
code and are cheapest to do together:

| Finding | Severity | State today | Here |
|---|---|---|---|
| ARC-01 duplicated theme code | Medium | Open | AR-01 |
| ARC-02 large classes and modules | Medium | Open | AR-02 |
| ARC-03 service locator, pipeline built mid-build | Medium | Open | AR-03 |
| ARC-04 `core` importing a service for a path helper | Low | Fixed by 0083 (`core/paths.py`); `core` imports services only in `main.py`, the controller | Status line only |
| ARC-05 dead templates and transformations | Low | `HTML_TAG_A` removed in 0100; the rest open | AR-04 |
| ARC-06 state shared between builds in one process | Low | Open | AR-05 |
| ARC-07 type hints, no mypy | Low | Open | AR-06 (scoped) |
| ARC-08 leftovers (`index.html`, `pypi/`, a stale comment) | Info | Open | AR-07 |

The rule for the whole series: **no change a user can see**. Every page of every
sample site is byte-identical before and after each commit, `kb4it` commands and
their output are unchanged, and themes written for 0.9 keep working. The only
exceptions are named in Compatibility.

The base is the branch after patch 0108. The work follows the usual cycle: this
specification (approved 2026-10-15), then an implementation plan, then a `git am`
patch series. It ships in 0.9.0, before the release is tagged (Decision D-G1): its
`CHANGELOG.md` entries go under 0.9.0, and every "for one release" below means kept
in 0.9.x and removed in 0.10.0.

### Measurements at the base (patch 0107)

| Area | Value |
|---|---|
| Modules over 600 lines | `tui/app.py` 1,457; techdoc `theme.py` 1,273; blog `theme.py` 971; bookshelf `theme.py` 762; `core/util.py` 754 |
| Classes over 300 lines | techdoc `Theme` 1,190 lines / 40 methods; blog `Theme` 946 / 28; bookshelf `Theme` 682 / 33; `Builder` 497 / 37; `Backend` 453 / 27; `Workflow` 435 / 16; `Processor` 426 / 15 |
| Theme methods in two or more themes | 23; identical or nearly so (93 to 100%): `get_page_actions`, `get_labels`, `get_html_values_from_key`, `generate_sources`, `build_metadata_section`, `build_page_key`, `build_events` (136 lines), `post_activities`, `build_page_key_value` |
| Theme methods 80 to 85% alike | `build`, `build_page_bookmarks`, `build_datatable` (89 lines), `extract_toc`, `build_page_stats` |
| Identical templates | 38 groups, all between techdoc and blog (the two UIkit themes); none shared by three themes |
| Unreferenced templates | 62 (techdoc 16, blog 45, bookshelf 1) |
| Transformation pairs | 23; 13 can never match python-markdown output (`HTML_TAG_PRE`, `HTML_TAG_TABLE`, `HTML_TAG_TABLE_KB4IT`, the five `HTML_TAG_ADMONITION_*` and the five `HTML_TAG_ADMONITION_ICON_*`, which hold Asciidoctor markup) |
| Services registered during a build | `Theme` (by `Frontend`), `Processor`, `Compiler`, `Deployer` (by `Backend`) |
| Shared state | `Builder.theme_var` class attribute; module-level progress callbacks in `compiler.py`; `params["force"]` and `repo["updated"]` written during a build |

### Requirement groups

| Group | Requirements | Findings |
|---|---|---|
| G1. Remove before moving | AR-04, AR-07 | ARC-05, ARC-08 |
| G2. Share and split | AR-01, AR-02 | ARC-01, ARC-02 |
| G3. Explicit structure | AR-05, AR-03, AR-06 | ARC-06, ARC-03, ARC-07 |

The groups are in implementation order: dead code goes first so nothing dead is
moved or split; state and wiring change last, on smaller modules.

## Conventions

As before: one-line Conventional Commits without trailers; code, tests, help pages
and `CHANGELOG.md` entry in the same commit; `[<COMPONENT>] EVENT key=value`
logging; UTF-8; no em dashes. Each requirement names its acceptance test. Commits
are `refactor:` unless they change something a user can notice, which this series
avoids.

Every commit of the series must keep these four checks green, in addition to its
own acceptance test:

1. `./scripts/devel/test.sh`.
2. `scripts/devel/theme_snapshot.py --content`: no difference from the snapshot
   taken at patch 0107, for every bundled theme, with the audit fixtures.
3. `scripts/devel/validate_html.py`: 0 errors besides UIkit attributes.
4. `tests/themes/test_escaping.py` and `tests/themes/test_html_quality.py`.

`theme_snapshot.py` gains the techdoc `sapbasis` app, so both techdoc samples are
compared.

## G1. Remove before moving

### AR-04 Dead templates and transformations (ARC-05)

**Requirement.**

- The 13 transformation pairs that can never match are removed: their names leave
  `Builder._XFORM_NAMES`, their `_MD` templates leave
  `resources/common/templates/` and their `_NEW` templates leave every bundled
  theme.
- Templates that no code, template or transformation name refers to are removed
  (62 at the base; the plan lists them). A template is kept if its name is built
  dynamically; the plan's search covers f-strings and `%` formatting.
- The pairs that can match are kept, including `HTML_TAG_SECT3`, `HTML_TAG_SECT4`
  and `HTML_TAG_H4`, which match documents with headings of level 4 and 5.
- A test lists the transformation sources and fails for one that the compiler
  cannot produce (it compiles a document with every Markdown construct the
  bundled extensions support, and checks each `_MD` pattern against the output).

**Out of scope.** Replacing string transformations with CSS on python-markdown's
own markup, and the compiler's `sect1`/`sectionbody` restructuring that keeps them
working. Both change output.

**Acceptance.** Snapshot identical; the new test passes; no bundled template is
unreferenced (a test, so new dead templates are caught).

### AR-07 Leftovers (ARC-08)

**Requirement.** `index.html` at the repository root and the `pypi/` folder are
deleted (Decision D-G6), and the comment in `tests/conftest.py` says what the code
does today.

**Acceptance.** `git ls-files index.html pypi` is empty; no file in the
repository, the packages or the workflows refers to them.

## G2. Share and split

### AR-01 Shared theme code and templates (ARC-01)

**Requirement.**

- A package `kb4it/services/themekit/` holds the code shared by the document
  themes (techdoc, blog, bookshelf), as mixins grouped by concern:

  | Mixin | Methods |
  |---|---|
  | `MetadataMixin` | `get_labels`, `get_html_values_from_key`, `build_metadata_section`, `get_page_actions` |
  | `KeyPagesMixin` | `build_page_key`, `build_page_key_value`, `build_page_properties`, `build_tagcloud_from_key`, `get_maxkv_freq`, `build_page_stats`, `build_page_bookmarks`, `build_page_index_all` |
  | `TableMixin` | `build_datatable` |
  | `EventsMixin` | `build_events` and the calendar helpers |
  | `TocMixin` | `extract_toc` |

  They combine into `DocumentTheme(Builder)` (Decision D-G2). techdoc, blog and
  bookshelf subclass `DocumentTheme`; apphelp and custom themes keep subclassing
  `Builder`, which does not grow.
- Where the themes differ today (template names, CSS classes, a column, a filter),
  the shared method takes the difference as a class attribute or a small hook
  method that the theme overrides. A theme keeps its own method only when the
  logic itself differs; each such override says why in its docstring.
- Methods that are identical in every theme that has them, and `generate_sources`
  and `post_activities` where they equal `Builder`'s, are deleted from the themes.
- Templates identical in techdoc and blog move to a shared template layer
  (Decision D-G3): `kb4it/resources/common/bases/uikit/templates/`, used by a
  theme that declares `"template_base": "uikit"` in `theme.json`. The lookup
  order becomes: repository overrides, the theme, its template base, the common
  templates. A theme without the key looks up exactly as today.
- `escape_audit.py` and `test_escaping.py` cover the template base.

**Acceptance.** Snapshot identical; a test (`ast`) checks that each method in the
table is defined once, in `themekit`, unless a theme overrides it with a docstring
saying why; no template is byte-identical in two themes; the template lookup has a
unit test with and without `template_base`.

### AR-02 Smaller modules (ARC-02)

**Requirement.**

- No Python module under `kb4it/` is over 600 lines (bundled third-party files
  excluded). A test enforces it.
- Theme modules: after AR-01 the shared code has left them; what remains is split
  by concern inside each theme's `logic/` folder where still needed (techdoc's
  dashboard and add page are the likely candidates).
- `kb4it/tui/app.py` becomes a package layout: `tui/projects.py` (registry, themes
  and apps helpers), `tui/servers.py` (local web servers), `tui/screens/` (one
  module per screen or pair of small screens) and `tui/app.py` (the `App` class
  and `run`). `tui/app.py` re-exports every public name it has today.
- `kb4it/core/util.py` is split by subject: `core/dates.py` (`DateCache`,
  `guess_datetime`, the `get_human_*` and timestamp helpers), `core/documents.py`
  (frontmatter and title: `get_markdown_attributes`, `get_document_attributes`,
  `first_heading`, `strip_first_heading`, `fences_in_blocks`,
  `raw_script_lines`, `extract_sections_from_md`) and `core/files.py` (copy,
  delete, JSON, `quarantine`, hashing). `core/util.py` keeps the rest and
  re-exports every name it has today, since themes, hooks and applications import
  from it.
- No public name used by themes or applications changes; where a name moves, the
  old import path keeps working.

**Acceptance.** Snapshot identical; the module-size test passes; a test imports
every name that `kb4it.core.util` and `kb4it.tui.app` export at patch 0107 (list
recorded in the test); the TUI tests pass, with their patch targets moved to the
new modules.

## G3. Explicit structure

### AR-05 State belongs to one build (ARC-06)

**Requirement.**

- `Builder.theme_var` becomes an instance attribute.
- The TUI's progress callbacks are passed to the build (through the `KB4IT`
  parameters and on to the `Compiler`), not set as module globals in
  `compiler.py`; `set_progress_callback` and `clear_progress_callback` stay as
  thin wrappers in 0.9.x, removed in 0.10.0.
- Decisions taken during a build (a full rebuild because the cache is corrupt or
  from another version) go to `runtime`, not into `params["force"]`; the
  generation time shown on pages goes to the template variables, not into
  `repo["updated"]`, so the `repo` dictionary is what `repo.json` (and
  `on_config`) said.

**Acceptance.** Snapshot identical; a test runs two builds in one process (as the
TUI and `kb4it serve` do) with different callbacks and settings and checks that
nothing of the first reaches the second; the `repo` dictionary seen by
`on_build_end` equals the loaded settings.

### AR-03 Explicit pipeline collaborators (ARC-03)

**Requirement.**

- `Processor`, `Compiler` and `Deployer` take their collaborators in their
  constructor: `Processor(backend, db, theme)`, `Compiler(backend, db, processor,
  theme, settings, callbacks)`, `Deployer(backend, theme)`. A small `Pipeline`
  object, created once in stage 1, builds and holds them; `Backend` stops
  registering services during the build and the stages use the pipeline.
- The registry keeps the application-level services: `Backend`, `DB`, `Builder`
  (the theme base), `Frontend`, `Workflow`, and `Theme` once loaded. Bundled and
  custom themes keep `self.srvbes`, `self.srvdtb` and `get_service` as today.
- In 0.9.x, `get_service("Processor")`, `"Compiler"` and `"Deployer"` still
  answer, with the pipeline's objects and one `[CONTROLLER] SERVICE_DEPRECATED
  name=...` warning per build (Decision D-G4).
- `AGENTS.md` describes the lifecycle: what exists before stage 1, what stage 1
  creates, and who may call whom.

**Acceptance.** Snapshot identical; `tests/core/test_pipeline_units.py` constructs
each of the three services with stand-in collaborators, without a `KB4IT` app, and
exercises one real method of each (the change analysis, the compile of one
document, the deploy of one page); the existing build tests pass unchanged.

### AR-06 Types at the seams (ARC-07)

**Requirement.** Scoped to what this series creates or reshapes, not the whole
package:

- Full annotations on `kb4it/core/paths.py`, the modules split out of `util.py`,
  `kb4it/services/themekit/`, the `Pipeline` and the constructors of AR-03.
- `get_service` returns a typed result for the application-level names
  (overloads), so tools can follow a service from lookup to use.
- CI runs mypy on exactly those modules, as a blocking step; the list grows in
  later work.

**Acceptance.** `mypy` reports 0 errors on the listed modules here and in CI.

## Compatibility

| Change | Who notices | How |
|---|---|---|
| Dead transformation pairs removed (AR-04) | A document that holds raw Asciidoctor markup such as `<pre class="CodeRay highlight">`, or an override of one of the 13 `_NEW` templates | It is no longer rewritten; release notes list the removed names |
| Unreferenced templates removed (AR-04) | A repository override or custom theme that copied one of them and calls it by name from its own logic | It keeps working when the template is in the override or the custom theme; only the bundled copy goes |
| `DocumentTheme` and `themekit` (AR-01) | Nobody: techdoc, blog and bookshelf change their base class; `Builder` is unchanged for custom themes | Help: custom themes may subclass `DocumentTheme` to reuse the document pages |
| `template_base` (AR-01) | Custom themes copied from techdoc or blog keep their own copies and do not need the key | Help documents the key |
| Split modules (AR-02) | Code importing from `kb4it.core.util` or `kb4it.tui.app` | Old import paths keep working |
| Pipeline services (AR-03) | Code calling `get_service("Processor")`, `"Compiler"` or `"Deployer"` | Works in 0.9.x with a warning, removed in 0.10.0; release notes name the replacement |
| Progress callbacks (AR-05) | Applications embedding KB4IT that call `set_progress_callback` | Works in 0.9.x, removed in 0.10.0; release notes show the parameter |
| `repo["updated"]` (AR-05) | Custom templates reading `var['repo']['updated']` | Kept as an alias in the template variables in 0.9.x, removed in 0.10.0 |

## Decisions for review

Answered on 2026-10-15, and the specification was approved: D-G1 the alternative (the series ships in 0.9.0, before the tag); D-G2 to D-G6 the recommendation. With D-G1, the deprecation window of D-G4 is 0.9.x, with removal in 0.10.0.

| # | Decision | Recommendation | Alternative |
|---|---|---|---|
| D-G1 | Release vehicle | After the 0.9.0 tag, as the start of 0.10.0: no user-visible change, a large diff, and 0.9.0 is ready to ship | Before 0.9.0, so the release carries the new structure |
| D-G2 | Where the shared theme code goes (AR-01) | `DocumentTheme(Builder)` built from mixins in `kb4it/services/themekit/`; `Builder` stays the small base for every theme | Move the methods into `Builder`, which every custom theme then inherits |
| D-G3 | Identical techdoc and blog templates (AR-01) | A template base, `common/bases/uikit/`, chosen by `"template_base": "uikit"` | Move them to `common/templates/`, where every theme, including bookshelf and custom themes, would fall back to UIkit markup; or keep the duplicates |
| D-G4 | `get_service` for pipeline services (AR-03) | Deprecated aliases for one release, removed in the next minor | Remove them now |
| D-G5 | Scope | AR-01 to AR-07: the Low and Info findings of the same phase come along | AR-01 to AR-03 only; ARC-05 to ARC-08 stay in `AUDIT.md` |
| D-G6 | `index.html` and `pypi/` (AR-07) | Delete: Pages is published by `help.yml`, so `index.html` is not served, and `pyproject.toml` uses `README.md` | Keep them; please say so if anything outside the repository links to them, which I cannot check from here |

## Testing summary

| Check | Where |
|---|---|
| Full test suite | Here, every commit |
| Content snapshot of every sample app (techdoc default and sapbasis, blog, bookshelf, apphelp) with the audit fixtures: no difference from 0107 | Here, every commit |
| Nu HTML Checker (`validate_html.py`) | Here, every commit, and CI |
| New structural tests: transformation sources, unreferenced templates, single definitions, module size, import compatibility, two builds in one process, pipeline units | Here, with the commit that needs them |
| mypy on the modules of AR-06 | Here and CI |
| macOS and Windows | CI after you push |

## Related Topics

- `AUDIT.md`, Phase 4: findings ARC-01 to ARC-08 and their evidence.
- `responses/KB4IT-0.9-AUDIT-FIX-SPEC.md`: the original AR-01 to AR-03 and Decision D-6.
- `responses/KB4IT-0.9-AUDIT-FIX-PLAN.md`: the implementation notes of the fix series, which this one follows.
