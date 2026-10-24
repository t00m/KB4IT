# Core fixes (WP1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a Summary with commas whole everywhere, list a repeated value once, report links written without an extension, tell theme authors to rebuild with `--force`, and make the wheel test show why it fails.

**Architecture:** Small, separate changes in `kb4it/core/` and `kb4it/services/`, each with its own test. Links without an extension are kept in a list of their own (`md.kb4it_bare_links`), so backlinks never count a link that is broken on the page.

**Tech Stack:** Python 3.11, python-markdown, pytest (build-based tests through `tests/helpers`).

**Spec:** `docs/superpowers/specs/2026-10-24-open-items-design.md`, section "WP1 Core fixes" (items 1 to 5, with the user's decision on item 2).

## Global Constraints

- Each task runs its own test files; Task 5 runs the full suite without browser tests (`pytest --ignore=tests/browser -q`) three times, which covers every task. Browser tests are never run.
- New log codes a user can see are documented in `help/source/troubleshooting.md` (`test_every_logged_error_code_is_documented`).
- No change to how values are split on commas (spec non-goal).
- Links without an extension are reported, never rewritten.
- Comments are one line, plain English; never the em dash. Help pages never name the documentation framework.
- Commits: one-line Conventional Commits message, no trailers, never push, never branch. Never stage `CLAUDE.md`, `claude/`, `skills/`, `uv.lock`.

## Review Focus

- **Links that only look extensionless.** `folder/` (a folder), `#part`, `mailto:x`, `https://x.org/page` and `resources/images/x.png` must never be reported. Test in Task 3.
- **A bare link next to a real document of the same stem.** `[x](b)` with `b.md` in the source is a warning with `suggest=b.md`, not `LINK_BROKEN`. Test in Task 3.
- **Backlinks.** A page linked only by `[x](b)` (no extension) gets no "Linked from" entry, because the link does not work. Test in Task 3.
- **Summary empty or missing.** The description still falls back to the first section's text. The existing `test_page_metadata_with_site_url` (page `a.md` has no Summary) must still pass in Task 1.
- **Repeated values in a YAML list.** `Tag: [a, a]` is cleaned like `Tag: a, a`. Test in Task 2.

---

### Task 1: One rule for a Summary with commas

**Files:**
- Modify: `kb4it/core/documents.py` (new `joined_value`)
- Modify: `kb4it/services/headmeta.py:47`, `kb4it/services/builder.py` (`search_record`, the feed writer), `kb4it/resources/themes/techdoc/logic/techdoc_docpage.py` (`summary`), `kb4it/resources/themes/apphelp/logic/apphelp_meta.py` (`_joined`)
- Test: `tests/core/test_publish.py`, `tests/themes/test_search.py`

**Interfaces:**
- Produces: `joined_value(values: list[str] | None) -> str` in `kb4it/core/documents.py`: the non-empty values joined with `", "`; `""` for `None` or an empty list.

- [ ] **Step 1: Write the failing tests.**

In `tests/core/test_publish.py`:

```python
def test_summary_with_commas_is_whole_in_description_and_feed(tmp_path, home):
    pages = {"a.md": page("Alpha", "Body.", Summary="Request it, then register it.", Date="2026-01-02", Category="Note")}
    feed = {"enabled": True, "limit": 5, "full_content": False}
    cfg = write_repo(tmp_path / "td", "techdoc", pages, site_url="https://x.org/", feed=feed)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    html = (tmp_path / "td" / "target" / "a.html").read_text(encoding="utf-8")
    assert '<meta name="description" content="Request it, then register it.">' in _head(html)
    assert _feed(tmp_path / "td" / "target" / "feed.xml")[0][3] == "Request it, then register it."
```

In `tests/themes/test_search.py`:

```python
def test_summary_with_commas_is_whole_in_the_index(tmp_path, home):
    _cfg, target, _ = _build(tmp_path, home, "techdoc", {"a.md": page("Alpha", Summary="One, two, three", Date="2026-10-08")})
    assert _index(target)["a.html"]["s"] == "One, two, three"
```

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/core/test_publish.py tests/themes/test_search.py -q -k "summary_with_commas"`. Expected: 2 failed (the description and the index hold "Request it" and "One").
- [ ] **Step 3: Implement.** Add `joined_value` with a docstring. `headmeta.py`: `text = joined_value(values("Summary")) or (sections[0]["text"] if sections else "")`. `builder.py`: `summary = joined_value(values("Summary"))` in `search_record`, and `summary = joined_value(self.srvdtb.get_values(doc_id, "Summary"))` in the feed writer. techdoc `summary()` returns `joined_value(srvdtb.get_values(doc_id, 'Summary'))`; apphelp `_joined(keys, name)` returns `joined_value(keys.get(name))`.
- [ ] **Step 4: Run the affected tests.** Run: `pytest tests/core/test_publish.py tests/themes -q`. Expected: all pass (including `test_page_metadata_with_site_url` and the apphelp tests).
- [ ] **Step 5: Commit.**

```bash
git add kb4it/core/documents.py kb4it/services/headmeta.py kb4it/services/builder.py kb4it/resources/themes/techdoc/logic/techdoc_docpage.py kb4it/resources/themes/apphelp/logic/apphelp_meta.py tests/core/test_publish.py tests/themes/test_search.py
git commit -m "fix(core): keep a Summary with commas whole in the description, search index and feed"
```

### Task 2: A repeated value is kept once

**Files:**
- Modify: `kb4it/core/documents.py` (`get_markdown_attributes`, the loop that fills `keys`)
- Test: `tests/core/test_frontmatter_null.py`

- [ ] **Step 1: Write the failing test.**

```python
def test_repeated_values_are_kept_once(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("---\nTag: zeta, alpha, zeta\nTopic: [a, a, b]\n---\n\n# Title\n\nBody\n", encoding="utf-8")
    keys, ok, _reason = get_document_attributes(str(doc))
    assert ok
    assert keys["Tag"] == ["zeta", "alpha"]
    assert keys["Topic"] == ["a", "b"]
```

- [ ] **Step 2: Run it and see it fail.** Run: `pytest tests/core/test_frontmatter_null.py -q -k repeated`. Expected: FAIL (`['zeta', 'alpha', 'zeta']`).
- [ ] **Step 3: Implement.** After the value list of a key is built, keep the first of each value in order (`list(dict.fromkeys(values))`), with a one-line comment.
- [ ] **Step 4: Run the tests.** Run: `pytest tests/core/test_frontmatter_null.py tests/core/test_metadata_pages.py -q`. Expected: all pass.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/core/documents.py tests/core/test_frontmatter_null.py
git commit -m "fix(core): keep a repeated property value once"
```

### Task 3: Report links written without an extension

**Files:**
- Modify: `kb4it/core/mdlinks.py`
- Modify: `kb4it/services/compiler.py` (`check_links`, where `self.links` is filled), `kb4it/services/workflow.py` (`_verify_links`), `kb4it/services/processor.py:240` (the `scan_document` call)
- Modify: `help/source/troubleshooting.md` (new section `LINK_NO_EXTENSION`), `help/source/howto-write-documents.md` (one sentence after the `LINK_BROKEN` line), `help/source/reference-command-line.md` (`verify` row lists `LINK_NO_EXTENSION`)
- Test: `tests/core/test_mdlinks.py`, `tests/core/test_backlinks.py`

**Interfaces:**
- Produces, in `kb4it/core/mdlinks.py`:
  - `bare_link_path(href: str) -> str | None`: the unquoted path of a relative link (no scheme, no netloc, not starting with `#` or `/`, not ending with `/`) whose last path part has no extension or ends in `.adoc` (any case); else `None`.
  - `suggest_md(path: str, known: set[str]) -> str | None`: `path + ".md"` for a path without an extension, or the path with `.adoc` replaced by `.md`, when that name (normalized with `os.path.normpath`, `/` separators) is in `known`; else `None`.
  - `MdLinkExtension` also sets `md.kb4it_bare_links: list[str]`, filled by `_MdLinkProcessor` with `bare_link_path` results; the `href` is left as written.
  - `scan_document(path) -> tuple[list, set, list]`: `(links, anchors, bare_links)`.
- `compiler.py` keeps `self.bare_links: dict[str, list[str]]` next to `self.links`.
- Log lines: `[COMPILER] LINK_NO_EXTENSION from=<doc> to=<path> suggest=<name>.md` (warning) when `suggest_md` finds a document, else `[COMPILER] LINK_BROKEN from=<doc> to=<path>` as today. `kb4it verify` prints the same text without the `[COMPILER]` tag and exits 1 when any is found.

- [ ] **Step 1: Write the failing tests.**

In `tests/core/test_mdlinks.py`:

```python
@pytest.mark.parametrize("href, expected", [
    ("b", "b"), ("dir/b", "dir/b"), ("my%20page", "my page"), ("old.adoc", "old.adoc"), ("OLD.ADOC#x", "OLD.ADOC"),
    ("b.md", None), ("folder/", None), ("#part", None), ("/abs/b", None), ("mailto:x@y.org", None),
    ("https://x.org/page", None), ("resources/images/x.png", None), ("b.html", None), ("", None),
])
def test_bare_link_path(href, expected):
    assert bare_link_path(href) == expected


def test_suggest_md():
    known = {"b.md", "dir/c.md", "old.md"}
    assert suggest_md("b", known) == "b.md"
    assert suggest_md("dir/c", known) == "dir/c.md"
    assert suggest_md("old.adoc", known) == "old.md"
    assert suggest_md("gone", known) is None


def test_extension_records_bare_links_without_rewriting():
    md = markdown.Markdown(extensions=["extra", MdLinkExtension()])
    html = md.convert("[a](b) [c](d.md) [e](old.adoc) [f](https://x.org/g)\n")
    assert 'href="b"' in html and 'href="old.adoc"' in html
    assert md.kb4it_links == [("d.md", "")]
    assert md.kb4it_bare_links == ["b", "old.adoc"]
```

In `tests/core/test_backlinks.py`:

```python
def test_build_and_verify_report_links_without_extension(tmp_path, home):
    pages = {"a.md": _page("Alpha", "[one](b) [two](c.adoc) [three](b.md)"), "b.md": _page("Beta", "Text.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    build = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert build.returncode == 0
    assert "LINK_NO_EXTENSION from=a.md to=b suggest=b.md" in build.stdout
    assert "LINK_BROKEN from=a.md to=c.adoc" in build.stdout
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert verify.returncode == 1
    assert "LINK_NO_EXTENSION from=a.md to=b suggest=b.md" in verify.stdout and "LINK_BROKEN from=a.md to=c.adoc" in verify.stdout


def test_a_link_without_extension_is_not_a_backlink(tmp_path, home):
    pages = {"a.md": _page("Alpha", "See [beta](b)."), "b.md": _page("Beta", "Text.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "Linked from" not in (tmp_path / "repo" / "target" / "b.html").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/core/test_mdlinks.py tests/core/test_backlinks.py -q`. Expected: the new tests fail (import error for `bare_link_path`, then missing log lines); the backlink test may already pass, which is fine: it guards the separate list.
- [ ] **Step 3: Implement** the two helpers, the extension list, the 3-tuple of `scan_document` and its three callers (`processor.py` ignores the third item), the compiler and verify reporting, and the help: troubleshooting section "The build warns LINK_NO_EXTENSION" (Cause: a link to a document without `.md`, which works on no web server; Fix: add `.md`, the warning names the document to link to); one sentence in `howto-write-documents.md`; `LINK_NO_EXTENSION` in the `verify` row of `reference-command-line.md`.
- [ ] **Step 4: Run the tests.** Run: `pytest tests/core/test_mdlinks.py tests/core/test_backlinks.py tests/core/test_deploy.py tests/help -q`. Expected: all pass.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/core/mdlinks.py kb4it/services/compiler.py kb4it/services/workflow.py kb4it/services/processor.py help/source/troubleshooting.md help/source/howto-write-documents.md help/source/reference-command-line.md tests/core/test_mdlinks.py tests/core/test_backlinks.py
git commit -m "feat(core): report links to documents written without the .md extension"
```

### Task 4: Tell theme authors to rebuild with --force

**Files:**
- Modify: `help/source/howto-create-theme.md` (where it says how to try a theme change), `help/source/troubleshooting.md` (new section)

- [ ] **Step 1: Write the text.** In `howto-create-theme.md`, after the step that builds with the new theme: "After you change a template, the theme's Python code or `theme.json`, run `kb4it build --force`. A normal build only rebuilds the documents whose source changed, so the other pages keep the old theme." In `troubleshooting.md`, a section "Pages do not change after a theme edit" {#theme-edit}: Cause (the build only rebuilds documents whose source changed), Fix (`kb4it build --force`; CSS and JavaScript files are copied at every build and need no `--force`).
- [ ] **Step 2: Run the help tests.** Run: `pytest tests/help -q`. Expected: all pass.
- [ ] **Step 3: Commit.**

```bash
git add help/source/howto-create-theme.md help/source/troubleshooting.md
git commit -m "docs(help): rebuild with --force after a theme edit"
```

### Task 5: The wheel test shows its error, and three full runs

**Files:**
- Modify: `tests/packaging/test_scripts.py` (`test_build_python_makes_wheel_and_sdist`)

- [ ] **Step 1: Change the test.** Run the script with `capture_output=True, text=True` and no `check=True`; then `assert result.returncode == 0, f"build_python.sh exit {result.returncode}\n--- stdout\n{result.stdout}\n--- stderr\n{result.stderr}"`. The rest of the test stays.
- [ ] **Step 2: Run it.** Run: `pytest tests/packaging/test_scripts.py -q -k wheel_and_sdist`. Expected: PASS.
- [ ] **Step 3: Commit.**

```bash
git add tests/packaging/test_scripts.py
git commit -m "test(packaging): show the build script output when the wheel build fails"
```

- [ ] **Step 4: Full suite, three times.** Run `pytest --ignore=tests/browser -q` three times, each with its output saved to the workspace. Expected: no failures. If the wheel test fails, its message now holds the script output: find the cause with superpowers:systematic-debugging, fix it with a test that fails first, and run the suite again. If it does not fail in three runs, write that in the response file and close the item.
