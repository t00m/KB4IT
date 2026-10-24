# Category and WorkType split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the `Category` property into the form of a document (`Category`) and the type of work it records (`WorkType`), in techdoc, the core search and feed, and the sapbasis-docs repository, while repositories that are not migrated keep working.

**Architecture:** techdoc gets one small module, `techdoc_records.py`, that answers "what type of work is this document" with a fallback to the old `Category` values; the dashboard and the events page call it instead of reading `Category`. The core adds `WorkType` to the search facets and lets a feed filter match either key. A conversion script rewrites the frontmatter of existing repositories line by line and writes a CSV of its changes.

**Tech Stack:** Python 3.11, Mako templates, UIkit 3.21.13, pytest (build-based tests through `tests/helpers.run_kb4it`).

**Spec:** `docs/superpowers/specs/2026-10-24-document-quality-design.md`, Part F ("splitting Category", phase 0) and the "Decisions" section.

## Global Constraints

- Values of `Category` after the split: `Procedure`, `Note`, `Report`, `Template`, `Post`, `Record`, `Minutes`.
- Values of `WorkType`: `Change`, `Incident`, `Task`, `Meeting`. A document with a `WorkType` is a record.
- Record types read from a legacy `Category` when `WorkType` is missing: `Change`, `Incident`, `Task`, `Meeting`.
- Mapping: `Change`, `Incident`, `Task` become `Category: Record` plus `WorkType: <same>`; `Meeting` becomes `Category: Minutes` plus `WorkType: Meeting`; in a list (`Report, Incident`) each record type moves to `WorkType` and the remaining forms stay in `Category`; if nothing remains, `Record` (or `Minutes` for a meeting) is used.
- The `events` list in `repo.json` keeps its values; the event type of a document is its work type when it has one, otherwise its first `Category`.
- Never use the em dash; comments are one line, plain English (AGENTS.md, nonia).
- HTML stays W3C valid with UIkit attributes written `data-uk-*`; every new block has a `<!-- NAME :: START -->` / `<!-- NAME :: END -->` pair.
- Tests: theme-only tasks run `pytest tests/themes` and `scripts/devel/check_themes.sh`; tasks that touch `kb4it/` outside `resources/themes/` or touch `scripts/` run the full suite without browser tests: `pytest --ignore=tests/browser`. Browser tests are never run.
- Commits: one-line Conventional Commits message, no trailers, never push, never branch. Never stage `CLAUDE.md`, `claude/`, `skills/`, `uv.lock`.
- The user's knowledge bases (sapbasis-docs) are never put under git; back them up to the scratchpad first.

## Review Focus

- **A repository that never migrates.** `Category: Change` with no `WorkType` must still fill the alert bar, open items, the events page and the event badges. Test in Task 2.
- **Mixed repositories.** One document migrated (`Category: Record`, `WorkType: Change`) and one legacy (`Category: Change`) must both appear under Changes, in date order, once each. Test in Task 2.
- **Alert header links.** "Changes" must link to a page that exists: `WorkType_Change.html` when any document has `WorkType: Change`, otherwise `Category_Change.html`. Test in Task 2.
- **Frontmatter rewriting.** The script must touch only the frontmatter `Category` line, keep every other byte (body text that says "Category: Change", CRLF line endings, key order), and be idempotent. Tests in Task 1.
- **Feed settings written before the split.** `"categories": ["Change"]` must still select migrated change records. Test in Task 4.

---

### Task 1: Conversion script

**Files:**
- Create: `scripts/conv/split_category.py`
- Test: `tests/core/test_split_category.py`

**Interfaces:**
- Produces: `split_text(text: str) -> tuple[str, dict | None]` returns the new text and a change record `{"category_before": str, "category_after": str, "worktype": str}`, or `(text, None)` when nothing changes. `split_dir(source: Path, csv_path: Path | None, dry_run: bool) -> list[dict]` applies it to every `*.md` under `source` (not recursive into `resources/`), each change record extended with `"file": <name>`. CLI: `python scripts/conv/split_category.py SOURCE [--csv FILE] [--dry-run]`, prints `changed=<n> unchanged=<m>`.

- [ ] **Step 1: Write the failing tests** (load the module with `importlib.util.spec_from_file_location`, as `tests/core/test_validate_html.py` does)

```python
def test_change_becomes_record():
    text = "---\nAuthor: A\nCategory: Change\nStatus: Open\n---\n\n# T\n\nCategory: Change stays in the body.\n"
    new, change = split.split_text(text)
    assert new == "---\nAuthor: A\nCategory: Record\nWorkType: Change\nStatus: Open\n---\n\n# T\n\nCategory: Change stays in the body.\n"
    assert change == {"category_before": "Change", "category_after": "Record", "worktype": "Change"}

def test_meeting_becomes_minutes():
    new, _ = split.split_text("---\nCategory: Meeting\n---\n\n# T\n")
    assert "Category: Minutes\nWorkType: Meeting\n" in new

def test_list_keeps_the_forms():
    new, change = split.split_text("---\nCategory: Report, Incident\n---\n\n# T\n")
    assert "Category: Report\nWorkType: Incident\n" in new
    assert change["category_after"] == "Report"

def test_forms_and_migrated_documents_are_untouched():
    for text in ("---\nCategory: Procedure, Note\n---\n\n# T\n",
                 "---\nCategory: Record\nWorkType: Change\n---\n\n# T\n",
                 "---\nAuthor: A\n---\n\n# T\n", "# No frontmatter\n"):
        assert split.split_text(text) == (text, None)

def test_crlf_and_idempotence():
    text = "---\r\nCategory: Task\r\n---\r\n\r\n# T\r\n"
    new, _ = split.split_text(text)
    assert new == "---\r\nCategory: Record\r\nWorkType: Task\r\n---\r\n\r\n# T\r\n"
    assert split.split_text(new) == (new, None)

def test_split_dir_writes_csv_and_respects_dry_run(tmp_path):
    (tmp_path / "a.md").write_text("---\nCategory: Change\n---\n\n# A\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("---\nCategory: Note\n---\n\n# B\n", encoding="utf-8")
    changes = split.split_dir(tmp_path, tmp_path / "out.csv", dry_run=True)
    assert [c["file"] for c in changes] == ["a.md"]
    assert "Category: Change" in (tmp_path / "a.md").read_text(encoding="utf-8")
    split.split_dir(tmp_path, tmp_path / "out.csv", dry_run=False)
    assert "WorkType: Change" in (tmp_path / "a.md").read_text(encoding="utf-8")
    assert (tmp_path / "out.csv").read_text(encoding="utf-8").splitlines()[0] == "file,category_before,category_after,worktype"
```

- [ ] **Step 2: Run them and see them fail**

Run: `pytest tests/core/test_split_category.py -v`
Expected: FAIL (file not found).

- [ ] **Step 3: Implement `scripts/conv/split_category.py`**

Work on lines, not on parsed YAML, so formatting survives: find the frontmatter between the first `---` line and the next `---` line (keep the original line ending), match `^Category:\s*(.*?)\s*$` there, skip when a `WorkType:` line exists. Split the value on commas, move record types to `WorkType` (first one wins if several), rebuild `Category` from the remaining values or the default form. A module docstring and one-line comments, like `scripts/devel/validate_html.py`.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/core/test_split_category.py -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite without browser tests**

Run: `pytest --ignore=tests/browser -q`
Expected: no failures.

- [ ] **Step 6: Commit**

```bash
git add scripts/conv/split_category.py tests/core/test_split_category.py
git commit -m "feat(scripts): add split_category.py to move record types from Category to WorkType"
```

### Task 2: techdoc reads the work type

**Files:**
- Create: `kb4it/resources/themes/techdoc/logic/techdoc_records.py`
- Modify: `kb4it/resources/themes/techdoc/logic/techdoc_dashboard.py` (`_index_doc_row`, `_build_index_alert_bar`, `_build_index_open_items`, `_build_index_events_panel`, `_build_index_recent_events`; `OPEN_ITEM_CATEGORIES` renamed `OPEN_ITEM_TYPES`)
- Modify: `kb4it/resources/themes/techdoc/logic/theme.py` (`build_page_events`)
- Modify: `kb4it/resources/themes/techdoc/templates/PAGE_INDEX.tpl` (alert headers and the three badge links)
- Test: `tests/themes/test_techdoc.py`

**Interfaces:**
- Produces (in `techdoc_records.py`):
  - `RECORD_TYPES = ('Change', 'Incident', 'Task', 'Meeting')`
  - `work_type(srvdtb, doc_id) -> str`: first `WorkType` value; else the first `Category` value that is in `RECORD_TYPES`; else `''`.
  - `event_type(srvdtb, doc_id) -> str`: `work_type(...)` or the first `Category` value or `''`.
  - `docs_of_work_type(srvdtb, value) -> list`: documents whose `work_type` is `value`, newest first (`srvdtb.sort_by_date`), each once.
  - `kind_url(srvdtb, value) -> str`: `WorkType_<value>.html` when any document has `WorkType: <value>`, else `Category_<value>.html` (file names through `valid_filename`, as `_build_index_diataxis` does).
- Row dicts of `_index_doc_row`, the events panel and recent events keep the key `category` for the badge text and gain `category_url` from `kind_url`; `PAGE_INDEX.tpl` uses `row['category_url']` instead of `category_url(row['category'])`. `var['page']['alert_bar']` gains `changes_url` and `incidents_url`.

- [ ] **Step 1: Write the failing tests** in `tests/themes/test_techdoc.py`

Add to `PAGES`: a migrated change `"change2.md": page("Migrated change", Date=day(2), Category="Record", WorkType="Change", Status="Open", Priority="Low")` and a legacy one already exists (`change.md`). Then:

```python
def test_alert_bar_and_open_items_read_worktype_with_legacy_fallback(site):
    html = read(site, "index.html")
    bar = html[html.index("CHANGES AND INCIDENTS :: START"):html.index("CHANGES AND INCIDENTS :: END")]
    assert bar.count('href="change2.html"') == 1 and bar.count('href="change.html"') == 1
    assert bar.index('href="change.html"') < bar.index('href="change2.html"')  # newest Date first: day(3) before day(2)
    assert 'href="WorkType_Change.html">Changes</a>' in html
    assert 'href="Category_Incident.html">Incidents</a>' in html   # only legacy incidents in this site

def test_events_page_uses_worktype(site):
    assert "change2.html" in read(site, "events.html")
```

- [ ] **Step 2: Run them and see them fail**

Run: `pytest tests/themes/test_techdoc.py -v -k "worktype"`
Expected: FAIL (`change2.html` missing from the index).

- [ ] **Step 3: Implement**

Create `techdoc_records.py`; in the dashboard replace each `get_docs_by_key_value('Category', X)` with `docs_of_work_type(self.srvdtb, X)` and each badge `Category` read with `event_type`; set `category_url` on the rows and the two alert URLs; in `theme.py` use `event_type` in `build_page_events`. In the template drop `category_url()` from the `<%! %>` block and link with the row values. Keep `category_css()`: it still receives Change, Incident and the forms.

- [ ] **Step 4: Run the theme tests and the theme check**

Run: `pytest tests/themes -q && scripts/devel/check_themes.sh`
Expected: all pass, all themes compliant.

- [ ] **Step 5: Commit**

```bash
git add kb4it/resources/themes/techdoc/logic/techdoc_records.py kb4it/resources/themes/techdoc/logic/techdoc_dashboard.py kb4it/resources/themes/techdoc/logic/theme.py kb4it/resources/themes/techdoc/templates/PAGE_INDEX.tpl tests/themes/test_techdoc.py
git commit -m "feat(techdoc): read the type of work from WorkType, falling back to the old Category values"
```

### Task 3: techdoc skeletons, app settings and help

**Files:**
- Modify: `kb4it/resources/themes/techdoc/templates/skeletons/CHANGE-SKELETON.md`, `INCIDENT-SKELETON.md`, `TASK-SKELETON.md`, `MEETING-SKELETON.md`
- Modify: `kb4it/resources/themes/techdoc/apps/default/config/repo.json`, `kb4it/resources/themes/techdoc/apps/sapbasis/config/repo.json`
- Modify: `kb4it/resources/themes/techdoc/templates/PAGE_HELP.tpl`, `help/source/reference-theme-techdoc.md`, `CHANGELOG.md`
- Test: `tests/themes/test_techdoc.py`

**Interfaces:**
- Consumes: the mapping in Global Constraints; `scripts/conv/split_category.py` from Task 1 (named in the help).

- [ ] **Step 1: Write the failing test** (import `ROOT` from `tests.helpers`)

```python
SKELETONS = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "templates" / "skeletons"

@pytest.mark.parametrize("name,category,worktype", [("CHANGE", "Record", "Change"), ("INCIDENT", "Record", "Incident"),
                                                     ("TASK", "Record", "Task"), ("MEETING", "Minutes", "Meeting")])
def test_record_skeletons_use_worktype(name, category, worktype):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    assert f"\nCategory: {category}\nWorkType: {worktype}\n" in text

def test_apps_list_worktype_after_category():
    for app in ("default", "sapbasis"):
        conf = json.loads((ROOT / "kb4it/resources/themes/techdoc/apps" / app / "config/repo.json").read_text(encoding="utf-8"))
        for key in ("datatable", "menu"):
            assert conf[key].index("WorkType") == conf[key].index("Category") + 1
```

- [ ] **Step 2: Run them and see them fail**

Run: `pytest tests/themes/test_techdoc.py -v -k "skeletons_use_worktype or worktype_after"`
Expected: FAIL.

- [ ] **Step 3: Implement**

Skeletons: replace the `Category:` line as in the mapping and add `WorkType:` right after it. App configs: insert `"WorkType"` after `"Category"` in `datatable` and `menu`. Help: in `reference-theme-techdoc.md` replace the `Category` row of "Properties it reacts to" with two rows (Category with the form values; WorkType with the record types, which drive the alert bar, open items and the calendar together with `events`), add a short "Upgrading an older repository" section that shows `python scripts/conv/split_category.py source --csv split.csv --dry-run` then without `--dry-run`, and says that unmigrated repositories keep working; mention `WorkType` in `PAGE_HELP.tpl` next to `Category`. CHANGELOG under Unreleased, Added: the `WorkType` property, the fallback and the script.

- [ ] **Step 4: Run the theme tests, the theme check and the help build**

Run: `pytest tests/themes tests/help -q && scripts/devel/check_themes.sh`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add kb4it/resources/themes/techdoc/templates/skeletons kb4it/resources/themes/techdoc/apps kb4it/resources/themes/techdoc/templates/PAGE_HELP.tpl help/source/reference-theme-techdoc.md CHANGELOG.md tests/themes/test_techdoc.py
git commit -m "feat(techdoc): record skeletons and app settings use Category Record or Minutes with WorkType"
```

### Task 4: Core search facets and feed filter

**Files:**
- Modify: `kb4it/services/builder.py` (`search_record`, the feed filter in the feed writer)
- Modify: `kb4it/resources/common/js/kb4it-search-ui.js` (`FACETS`)
- Modify: `help/source/reference-repo-json.md` (feed `categories`, search filters)
- Test: `tests/themes/test_search.py`, `tests/core/test_publish.py`

**Interfaces:**
- Produces: search records carry `"f": {"Category": [...], "WorkType": [...], "Tag": [...]}` (keys only when they have values); the feed keeps a dated document when `wanted` meets `Category ∪ WorkType`.

- [ ] **Step 1: Write the failing tests**

In `tests/themes/test_search.py`:

```python
def test_worktype_is_a_facet(tmp_path, home):
    _cfg, target, _ = _build(tmp_path, home, "techdoc", {"c.md": page("Change one", Category="Record", WorkType="Change", Date="2026-10-08")})
    assert _index(target)["c.html"]["f"] == {"Category": ["Record"], "WorkType": ["Change"]}
```

In `tests/core/test_publish.py`:

```python
def test_feed_category_filter_matches_worktype(tmp_path, home):
    pages = {"r.md": page("Migrated", Category="Record", WorkType="Change", Date="2026-01-02"),
             "n.md": page("Note", Category="Note", Date="2026-01-03")}
    feed = {"enabled": True, "limit": 5, "categories": ["Change"], "full_content": False}
    cfg = write_repo(tmp_path / "td", "techdoc", pages, site_url="https://x.org/", feed=feed)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert [e[0] for e in _feed(tmp_path / "td" / "target" / "feed.xml")] == ["Migrated"]
```

- [ ] **Step 2: Run them and see them fail**

Run: `pytest tests/themes/test_search.py tests/core/test_publish.py -v -k "worktype"`
Expected: FAIL.

- [ ] **Step 3: Implement**

`search_record`: facet keys `("Category", "WorkType", "Tag")`. Feed: `categories = set(Category values) | set(WorkType values)`. `FACETS = ["Category", "WorkType", "Tag"]` in the search UI. Help: one line each in `reference-repo-json.md`.

- [ ] **Step 4: Run the full suite without browser tests**

Run: `pytest --ignore=tests/browser -q && scripts/devel/check_themes.sh`
Expected: no failures. Also `python scripts/devel/validate_html.py` on a built techdoc sample: 0 errors, 0 warnings.

- [ ] **Step 5: Commit**

```bash
git add kb4it/services/builder.py kb4it/resources/common/js/kb4it-search-ui.js help/source/reference-repo-json.md tests/themes/test_search.py tests/core/test_publish.py
git commit -m "feat(search): add WorkType as a search filter and let feed categories match it"
```

### Task 5: Migrate sapbasis-docs

Operational task on the user's knowledge base. No commit in that repository; it has no git and must not get one.

**Files:**
- Modify: `/home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/source/*.md` (frontmatter only)
- Create: `/home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/category-split.csv`
- Modify: `/home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/config/repo.json` (`datatable`, `menu`)

- [ ] **Step 1: Back up the sources** to `<scratchpad>/sapbasis-before-category-split/` (`cp -a source`), and the config file next to it.

- [ ] **Step 2: Dry run**

Run: `python3 scripts/conv/split_category.py /home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/source --csv /home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/category-split.csv --dry-run`
Expected: `changed=529 unchanged=505` (Change 307, Incident 167, Task 44, Meeting 9, "Report, Incident" 2).

- [ ] **Step 3: Apply** (same command without `--dry-run`), then count: `grep -l "^WorkType:" source/*.md | wc -l` gives 529; `grep -h "^Category:" source/*.md | sort | uniq -c` shows no Change, Incident, Task or Meeting.

- [ ] **Step 4: Config:** insert `"WorkType"` after `"Category"` in `datatable` (if present) and `menu`.

- [ ] **Step 5: Rebuild and check:** `PYTHONPATH=<repo> python3 -c "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()" build /home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/config/repo.json` exits 0; `target/WorkType_Change.html` exists; `target/index.html` links "Changes" to `WorkType_Change.html`; `target/events.html` lists as many documents as before the split (compare with the backup's last build).

- [ ] **Step 6: Report** the counts and the CSV path in the response file. Nothing to commit in KB4IT for this task.
