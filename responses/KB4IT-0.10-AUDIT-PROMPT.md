---
Author: Tomás Vírseda
Category: Task
Command: bandit, git, kb4it, mypy, pip-audit, pytest, radon, ruff, uv, vulture
Date: 2026-10-25
DocType: Reference
Language: Python
Product: Codex, KB4IT
Scope: Development
Tag: prompt, ai-agent
Topic: Audit, Security
---

# KB4IT 0.10 full audit prompt for Codex

## Overview

This is the prompt to give OpenAI Codex for a full read-only audit of KB4IT 0.10. It covers correctness, security, architecture, packaging, tests, HTML output and documentation.

It builds on the 0.9 audit in `AUDIT.md` (commit `b5330aa`). The new report goes to a separate file, and each 0.9 finding gets a regression check.

## Usage notes

- Codex reads `AGENTS.md` on its own, so the prompt points to it and does not repeat it.
- Run it in a fresh clone or worktree. An agent told to stay read-only can still "fix" things along the way.
- On a long run the report can outgrow the context. If that happens, run one phase per session: "Run phase 3 only, append to AUDIT-0.10.0.md". This also lets you review between phases, as with the 0.9 audit.

!!! note
    The prompt names the parts most likely to have security problems: `serve` and `webserver`, the editor that saves files, admin zips, raw `| n` template output, build hooks that run Python, and the GitHub Action.

## Prompt

```text
You are auditing the KB4IT repository (Python 3.11+ static site generator: Markdown + YAML
frontmatter -> HTML via python-markdown and Mako; services pipeline, Textual TUI, live
`serve` mode, in-browser editor, four themes, GitHub Action). Current version: kb4it/VERSION.

Read AGENTS.md first and follow its conventions (no em dashes, log style, module-size and
typing rules). Then read AUDIT.md: it is a previous audit of 0.9 (commit b5330aa) whose
findings were marked fixed. Do NOT edit AUDIT.md.

## Ground rules
- Read-only audit. The only file you create is AUDIT-<version>.md at the repo root.
  Do not modify code, commit, push, create branches, or touch GitHub.
- Run tools in throwaway environments (uv run --no-project --with ...); never install
  globally. Use scripts/devel/test.sh, scripts/devel/typecheck.sh,
  scripts/devel/check_themes.sh, scripts/devel/escape_audit.py and
  scripts/devel/validate_html.py where they apply.
- Every finding needs: ID (e.g. SEC-03), severity (Critical/High/Medium/Low/Info),
  file:line evidence, a concrete failure scenario or reproduction (command + input +
  observed result), and a minimal fix. Prefer proving it over guessing; mark anything
  unproven as "Suspected".
- No style nitpicks unless they hide a bug. Do not re-report findings already in AUDIT.md
  unless they regressed or the fix is incomplete; say which.

## Phases (finish each with a top-5 priority list)
0. Inventory: packages, entry points (CLI subcommands, TUI, serve, Action), data flow,
   what changed since b5330aa (git log/diff stat).
1. Automated baseline: pytest (all, plus browser tests if Chromium is available),
   ruff, mypy (strict on the typecheck.sh list, normal elsewhere), bandit, vulture,
   radon cc/mi, pip-audit against requirements.txt and the lockfiles. Summarise, then
   triage the real issues.
2. Correctness and robustness: incremental build and blake2b hashing (stale pages,
   renamed/deleted docs, key/value index invalidation, --force), frontmatter edge cases
   (missing/invalid YAML, unicode, duplicate keys, dates, huge files), link/anchor
   verification, lock handling, watcher/serve races, partial writes, error paths and
   exit codes, ENV frozen invariant, Windows/macOS path handling.
3. Security: path traversal and symlink escape (sources, assets, custom themes, admin
   zips, editor save endpoint, webserver), XSS (Mako expressions printed raw with | n,
   nh3 sanitisation coverage, Markdown extensions, Mermaid/KaTeX, search index JSON,
   Atom/sitemap), local webserver exposure (bind address, CSRF/origin checks on write
   endpoints, DNS rebinding), YAML loading, Python hooks execution model, admin/ backups
   being publicly guessable, GitHub Action and workflows (script injection via inputs,
   token permissions, unpinned actions, pull_request_target), supply chain of vendored
   JS (CodeMirror bundle, Mermaid, KaTeX: versions, known CVEs, integrity).
4. Architecture and maintainability: service boundaries, get_service vs constructor
   injection, god classes, duplication between theme.py files vs themekit, public API
   stability (tests/test_public_names.py), module-size limit, dead code, typing coverage.
5. Dependencies and packaging: pyproject (poetry) vs requirements.txt vs pixi.toml vs
   test.sh pins drift, wheel/sdist contents (resources included? stray files?), Python
   3.11-3.14 compatibility, optional deps, licensing of bundled third-party assets vs
   GPL-3.0-or-later, release scripts (RELEASING.md) correctness.
6. Tests and output quality: coverage gaps on risky code (run pytest --cov), tests
   that assert nothing or are flaky, missing regression tests for prior AUDIT.md fixes;
   generated HTML validity (Nu checker: 0 errors/0 warnings target), accessibility
   (landmarks, alt text, contrast, keyboard nav), SEO/Open Graph/canonical/sitemap
   correctness, offline/file:// behaviour, page weight and build performance on a
   large synthetic corpus (e.g. 2,000 docs: time, memory, incremental rebuild of 1 doc).
7. Documentation consistency: README, help/source/ and AGENTS.md vs actual behaviour
   (commands, repo.json keys, defaults). Run `kb4it verify help/config/repo.json`.

## Final section
- Executive summary (10 lines max) with an overall risk rating.
- A table of all findings sorted by severity, with effort estimates (S/M/L).
- A suggested fix order grouped into patch series that can each be reviewed on its own.
- Regression check: one line per AUDIT.md finding: still fixed / regressed / incomplete.
```
