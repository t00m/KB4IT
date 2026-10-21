# Help center implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `help/` site the official documentation: shipped inside the package for offline use, published to GitHub Pages, with a first-run notice and a `kb4it help` command.

**Architecture:** The apphelp theme builds `help/` in two ways from the same source. The release tooling builds an offline copy into `kb4it/resources/help/` (git-ignored, never committed) and includes it in the wheel and sdist. The existing `help.yml` workflow builds the online copy on master. A small `kb4it/core/notice.py` module owns the notice text and the dismiss marker. The CLI gains a `help` subcommand, and `main()` prints the notice before it dispatches any action.

**Tech Stack:** Python 3.11+, argparse, `webbrowser`, the apphelp theme, pytest, Textual pilot tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-20-help-center-design.md`

## Global Constraints

- Never use the em dash character in code, comments, docs or commit messages.
- The page text never names the framework behind the four section names. A test checks the built site.
- The help never makes a network call. The online URL is only printed or linked.
- The notice goes to stderr. Stdout stays clean for scripts.
- The dismiss marker lives under `ENV["LPATH"]["ROOT"]` (`KB4IT_HOME` or `~/.kb4it`).
- Commits: one-line Conventional Commits message, no trailers. Never push, never create a branch.
- Run the suite with `uv run pytest`. Run the new tests against the working tree, never the installed tool.

## Review Focus

1. A dev checkout without an offline build: `kb4it help` must say the offline copy is missing and name the build script. It must not crash.
2. No browser on the machine: `kb4it help` must print the offline path and exit 0.
3. Unwritable `KB4IT_HOME`: `kb4it help --dismiss` must print an error and exit 1. Other commands must still run.
4. Paths with spaces or non-ASCII characters in the offline path: the file URL opened by `kb4it help` must be correct.
5. CI runs (`CI` set): the notice must not clutter logs, and stdout must not change.

Each line has its test in the owning task.

---

### Task 1: Notice module

**Files:**
- Create: `kb4it/core/notice.py`
- Test: `tests/core/test_notice.py`

**Interfaces:**
- Produces: `help_notice_lines(offline: Path | None, online_url: str) -> list[str]`, `help_notice_dismissed() -> bool`, `dismiss_help_notice() -> None`, `HELP_ONLINE_URL` constant (`https://t00m.github.io/KB4IT/`), `offline_index() -> Path | None` (returns `kb4it/resources/help/index.html` when it exists, else `None`).

- [ ] **Step 1: Write the failing tests**

Tests (names and assertions):
- `test_notice_names_the_command_and_the_urls`: `help_notice_lines(Path("/x/index.html"), HELP_ONLINE_URL)` joined text contains `kb4it help`, `kb4it help --dismiss`, the offline path and the online URL.
- `test_notice_is_short`: at most 3 lines.
- `test_dismiss_writes_the_marker_and_stops_the_notice`: with `KB4IT_HOME` set to a tmp path (monkeypatch the `ENV` value), `help_notice_dismissed()` is False, `dismiss_help_notice()`, then True.
- `test_marker_that_is_empty_still_counts`: an empty marker file counts as dismissed.
- `test_offline_index_is_none_without_a_build`: with the resource folder absent, `offline_index()` returns `None`.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `uv run pytest tests/core/test_notice.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kb4it.core.notice'`.

- [ ] **Step 3: Implement `kb4it/core/notice.py`**

Read the marker path from `ENV["LPATH"]["ROOT"]` at call time, not at import time, so tests can change `KB4IT_HOME`. Name the marker `help-notice-dismissed`. The notice lines: one line that says the help center exists, with the offline path and the online URL, and one line that says how to hide it. Use `importlib.resources` for `offline_index()`.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `uv run pytest tests/core/test_notice.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add kb4it/core/notice.py tests/core/test_notice.py
git commit -m "feat(help): add the first-run help notice module"
```

---

### Task 2: `kb4it help` command

**Files:**
- Modify: `kb4it/core/main.py` (add the subparser near `themes`; handle the action in `main()`)
- Test: `tests/core/test_help_command.py`
- Modify: `tests/helpers.py` (add an `env` keyword to `run_kb4it`, passed to `isolated_env`)

**Interfaces:**
- Consumes: `offline_index()`, `dismiss_help_notice()`, `HELP_ONLINE_URL` from Task 1.
- Produces: subcommand `help` with flags `--url` (print online URL only, exit 0), `--dismiss` (write marker, print one confirmation line, exit 0; on `OSError` print the error and exit 1). Without flags: open `offline_index()` with `webbrowser.open`; if no offline copy, print the message from the build script name and exit 1; if the browser call returns False, print the path and exit 0.

- [ ] **Step 1: Write the failing tests**

- `test_help_url_prints_the_online_address`: `run_kb4it("help", "--url")` returns 0 and stdout contains `HELP_ONLINE_URL`.
- `test_help_dismiss_hides_the_notice`: run `help --dismiss`, then run `themes`; second stdout does not contain `kb4it help`.
- `test_help_without_offline_copy_names_the_build_script`: returns 1, stdout contains `scripts/help/build_offline.py`.
- `test_help_opens_the_offline_index`: create a fake offline index is not possible without the build, so monkeypatch by setting `BROWSER` to a script in tmp_path that writes its argument to a file; the test writes `kb4it/resources/help/index.html` only in a temp copy (use a helper that patches `offline_index` through the `KB4IT_HELP_INDEX` environment variable read by `offline_index()`). Assert the file holds a `file://` URL with the index path, percent-encoded for spaces.
- `test_dismiss_on_unwritable_home_reports_an_error`: point `KB4IT_HOME` to a file path, expect exit 1 and a message.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `uv run pytest tests/core/test_help_command.py -v`
Expected: FAIL, `invalid choice: 'help'` or similar.

- [ ] **Step 3: Implement**

Add `KB4IT_HELP_INDEX` override read inside `offline_index()` (Task 1 file). Add the subparser and the handler. Keep `main()` changes small: the handler lives in `kb4it/core/notice.py` or a new function there, called from `main()`.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `uv run pytest tests/core/test_help_command.py tests/core/test_notice.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add kb4it/core/main.py kb4it/core/notice.py tests/core/test_help_command.py tests/helpers.py
git commit -m "feat(help): add kb4it help with --url and --dismiss"
```

---

### Task 3: First-run notice in the CLI

**Files:**
- Modify: `kb4it/core/main.py` (print the notice before `app.run()`, for every action except `help`)
- Test: `tests/core/test_help_notice_cli.py`

**Interfaces:**
- Consumes: `help_notice_lines`, `help_notice_dismissed`, `offline_index`, `HELP_ONLINE_URL` from Task 1.

- [ ] **Step 1: Write the failing tests**

- `test_first_run_prints_the_notice_on_stderr`: `run_kb4it("themes")` returns the notice in stderr, and stdout equals the stdout of a dismissed run. (Task 2 adds `run_kb4it(..., env=None)` and a `split_streams=True` option that returns stdout and stderr apart.)
- `test_notice_is_not_printed_when_dismissed`: after `help --dismiss`, no notice.
- `test_notice_is_not_printed_under_ci`: with `CI=true`, no notice, even when not dismissed.
- `test_help_action_does_not_print_the_notice`: `help --url` prints only the URL.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `uv run pytest tests/core/test_help_notice_cli.py -v`
Expected: FAIL, notice missing.

- [ ] **Step 3: Implement**

In `main()`, after `params = parser.parse_args()` and before dispatch: if `params.action != "help"`, not `help_notice_dismissed()`, and `os.environ.get("CI")` is empty, write each notice line to stderr.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `uv run pytest tests/core/test_help_notice_cli.py tests/core/test_help_command.py tests/core/test_notice.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add kb4it/core/main.py tests/core/test_help_notice_cli.py tests/helpers.py
git commit -m "feat(help): show the help notice until the user dismisses it"
```

---

### Task 4: Notice in the TUI

**Files:**
- Modify: `kb4it/tui/` main screen (add a banner widget, hidden once dismissed; pick the screen that opens with no arguments)
- Test: `tests/tui/test_tui.py` (new test)

**Interfaces:**
- Consumes: `help_notice_dismissed`, `dismiss_help_notice`, `help_notice_lines`.

- [ ] **Step 1: Write the failing test**

- `test_tui_shows_the_help_banner_until_dismissed`: with the `registry` fixture and a clean `KB4IT_HOME`, the main screen has a visible `#help-banner`; pressing its dismiss key (choose `d`) hides it and writes the marker.

- [ ] **Step 2: Run and watch it fail**

Run: `uv run pytest tests/tui/test_tui.py -k help_banner -v`
Expected: FAIL, no `#help-banner`.

- [ ] **Step 3: Implement the banner and the key binding**

Keep it one `Static` with the first notice line and a binding that calls `dismiss_help_notice()`.

- [ ] **Step 4: Run and watch it pass**

Run: `uv run pytest tests/tui/test_tui.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add kb4it/tui tests/tui/test_tui.py
git commit -m "feat(tui): show the help banner until it is dismissed"
```

---

### Task 5: Offline build script and version

**Files:**
- Create: `scripts/help/build_offline.py`
- Modify: `.gitignore` (add `kb4it/resources/help/`)
- Test: `tests/packaging/test_help_offline.py`

**Interfaces:**
- Produces: `python scripts/help/build_offline.py` builds `help/` into `kb4it/resources/help/`. It writes a temporary copy of `help/config/repo.json` with `target` set to the output folder, then runs `kb4it build` on the copy with the working tree's KB4IT (`PYTHONPATH` set to the repo root). It exits non-zero when the build fails.

- [ ] **Step 1: Write the failing tests**

- `test_offline_build_writes_index_and_search`: run the script, assert `kb4it/resources/help/index.html` exists in a tmp output (the script takes `--out` for tests).
- `test_offline_build_shows_the_package_version`: the built `index.html` contains `0.9.1` (read from `kb4it/VERSION`) and does not contain `"0.8"` as the version.
- `test_offline_build_has_no_absolute_paths`: no `/home/` or `C:\\` string in any generated `.html` file.
- `test_help_config_version_is_not_hardcoded`: the test reads `help/config/repo.json` and asserts the `version` key is absent or equals the VERSION file. (Fixes the stale `"0.8"`.)

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/packaging/test_help_offline.py -v`
Expected: FAIL, script missing; the version test fails on `"0.8"`.

- [ ] **Step 3: Implement the script.** The version needs no change here: `help/config/repo.json` already says `"version": "kb4it"` (done in the version fix).

- [ ] **Step 4: Run and watch them pass**

Run: `uv run pytest tests/packaging/test_help_offline.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/help/build_offline.py .gitignore help/config/repo.json tests/packaging/test_help_offline.py
git commit -m "feat(help): build the offline help copy from the working tree"
```

---

### Task 6: Ship the offline copy in releases

**Files:**
- Modify: the release packaging step in `scripts/distribution/build_all.sh` (the first step that builds the packages; locate it first), and `scripts/release.sh` if it builds packages.
- Test: `tests/packaging/test_scripts.py` (new test)

**Interfaces:**
- Consumes: `scripts/help/build_offline.py` from Task 5.

- [ ] **Step 1: Write the failing test**

- `test_release_builds_the_offline_help_before_packaging`: read the packaging script text; assert `scripts/help/build_offline.py` appears before the first `build` command for the wheel or sdist.

- [ ] **Step 2: Run and watch it fail**

Run: `uv run pytest tests/packaging/test_scripts.py -k offline -v`
Expected: FAIL.

- [ ] **Step 3: Add the step**

- [ ] **Step 4: Run and watch it pass**, then build a wheel into a temp folder and check it contains `kb4it/resources/help/index.html` (add as a test marked to run only when `KB4IT_BUILD_WHEEL=1`, to keep the normal suite fast).

- [ ] **Step 5: Commit**

```bash
git add scripts/distribution/build_all.sh tests/packaging/test_scripts.py
git commit -m "build: include the offline help in release packages"
```

---

### Task 7: Coverage test

**Files:**
- Create: `tests/help/test_coverage.py`
- Modify: `kb4it/core/main.py` (extract `build_parser()` so the test reads the subcommands without running `main()`)

**Interfaces:**
- Produces: `build_parser() -> argparse.ArgumentParser` in `kb4it/core/main.py`; `main()` calls it.

- [ ] **Step 1: Write the failing tests**

- `test_every_command_has_a_page_mention`: for each subparser name, `help/source` contains `kb4it <name>`.
- `test_every_bundled_theme_has_a_reference_page`: each folder in `kb4it/resources/themes/` (skip private ones) has `help/source/reference-theme-<name>.md`.
- `test_every_repo_json_key_is_documented`: the keys the code validates (find the list the builder locates in `kb4it/core/mdconfig.py` or the config loader) all appear in `reference-repo-json.md`.
- `test_every_logged_error_code_is_documented`: every code matching the pattern of the error tags in `kb4it/` (builder defines the regex from existing `DOC_INVALID`, `META_CONFIG`, `MD_EXTENSION_MISSING` style tags) appears in `help/source/troubleshooting.md` or `reference-*.md`.
- `test_section_names_only`: every page in `help/source` has `Section` set to one of `Start here`, `Guides`, `Reference`, `Concepts`, `Questions`.
- `test_no_framework_name_in_the_site`: the built offline copy (skip when not built) contains no `taxis` and no `Diátaxis`.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/help/test_coverage.py -v`
Expected: some tests fail. The failure list is the gap list. Record it in the ledger before writing content.

- [ ] **Step 3: Extract `build_parser()`** (a small refactor; the CLI behavior does not change).

- [ ] **Step 4: Write the missing pages and fix the `Section` values** until each test passes. Content tasks are driven by the failing output; each page follows the `kb4itdoc` structure and the DocType rules.

- [ ] **Step 5: Run and watch them pass**, then commit per group of pages:

```bash
git add tests/help/test_coverage.py kb4it/core/main.py help/source
git commit -m "docs(help): cover every command, theme, key and error code"
```

---

### Task 8: Section structure and questions

**Files:**
- Modify: `help/source/*.md` (the `Section` property), `help/config/repo.json` (`Feature` vocabulary if the nav needs it)
- Test: covered by `test_section_names_only` (Task 7)

- [ ] **Step 1:** Map existing pages: Tutorial → `Start here`; How-to guide → `Guides`; Reference → `Reference`; Explanation → `Concepts`; `faq`, `tips`, `troubleshooting` → `Questions`. The `dev-*` pages keep their current section and move to `Reference` only if they describe the product. Record the mapping in the ledger.

- [ ] **Step 2:** Run `uv run pytest tests/help -v`. Expected: `test_section_names_only` passes.

- [ ] **Step 3:** Build the offline copy with `python scripts/help/build_offline.py` and read the navigation in the output. Check the four section names and `Questions` appear in the menu.

- [ ] **Step 4: Commit**

```bash
git add help/source help/config/repo.json
git commit -m "docs(help): group pages into start, guides, reference, concepts and questions"
```

---

### Task 9: Online copy and release check

**Files:**
- Modify: `.github/workflows/help.yml` only if a check is missing. The workflow already deploys on master, and release tags point at master merges.
- Test: `tests/packaging/test_workflows.py` (add one assertion that the help workflow still deploys on `master`).

- [ ] **Step 1: Write the failing assertion** that the workflow's config path is `help/config/repo.json` and that the upload step is guarded by `refs/heads/master`. (Likely passes already; the test pins it.)

- [ ] **Step 2: Run.** Expected: PASS. If it fails, fix the workflow.

- [ ] **Step 3: Commit** only if the workflow changed.

---

### Task 10: Final review

- [ ] Run the full suite: `uv run pytest`. Expected: all pass except tests that need a build (skipped when the offline copy is absent).
- [ ] Build the offline copy and run `kb4it help` on it. Expected: the page opens (or the path prints when no browser is set).
- [ ] Run the self-review: spec coverage, Review Focus tests present, no em dash (U+2014) in changed files, checked with `grep -n $'\xe2\x80\x94'` on each file.
- [ ] Write the response doc with the `kb4itdoc` skill in `responses/`.

## Rulings to record in the ledger

- Ruling: the offline copy is git-ignored and built by release tooling, not committed. The spec said "committed for releases only"; a generated folder in git drifts. Cost if wrong: a release needs the build step to succeed.
- Ruling: the notice is silent when `CI` is set. The spec said "every start"; CI logs would fill with it. Cost if wrong: CI users do not see the notice, and the online docs remain the source.
- Ruling: `help/config/repo.json` names the version with the token `"kb4it"`, which apphelp resolves to `kb4it/VERSION`. Every version in code, theme metadata and docs now comes from that file, checked by `tests/core/test_version_sources.py`. Cost if wrong: a user app that wants the literal word `kb4it` as its version cannot have it.
- Ruling: theme versions are set at load from `kb4it/VERSION`. `theme.json` no longer has a `version` key, and the unused `theme.csv` files were removed. The `kb4it` requirement floors stay, because they name the oldest KB4IT a theme works with.
- Ruling: the TUI banner uses one line, not a panel. Cost if wrong: a later visual change.
