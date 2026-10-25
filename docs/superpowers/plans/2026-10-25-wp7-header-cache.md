# Header cache: read each document once per build (WP7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop parsing a document's YAML header on every build when the file did not change. Each source file is read once, hashed, and its parsed keys, body hash and metadata hash are reused from `kbdict.json` when the bytes are identical. On the 1,000-document timing site the unchanged build drops from 2.22 s to roughly 1.3 s (about 40%).

**Architecture:** `Processor.step_00_extraction()` reads the source bytes once and stores `file_hash` with the document entry. `kb4it/core/documents.py` gains a content-based parser that reports whether it logged the `title_in_frontmatter_ignored` warning; the path-based public helpers keep their signatures and behaviour. `kb4it/core/files.py` gains a bytes hash. The kbdict records the PyYAML version, and `Backend.load_kbdict()` drops a cache written under another version. The database, `Date` conversion and metadata index still run for every document.

**Tech Stack:** Python 3.11, PyYAML, blake2b, pytest.

**Spec:** `docs/superpowers/specs/2026-10-24-open-items-design.md`, section "WP7 Header cache"; analysis in `responses/20261023_154000_SORT-FIX-PROFILER-HELP-HEADER-CACHE.md`.

## Global Constraints

- Core change: run the full suite with `python3 -m pytest --ignore=tests/browser -q` before the final commit. Never run the browser tests.
- Keep the public helpers of `kb4it.core.util` unchanged; `tests/test_public_names.py` guards that list. New helpers stay in `documents.py` / `files.py` and are imported from there (or added to `util.__all__` only with a matching record update, which this plan does not do).
- A document that logged `title_in_frontmatter_ignored` is parsed at every build, so the warning stays.
- Invalid documents are never stored in `kbdict.json`; they are parsed and reported at every build, as today.
- `kb4it verify` and the editor checks keep parsing directly through `get_document_attributes`.
- Line ending and byte order mark behaviour must not change: a CRLF or BOM file gives the same keys and body hash as its LF twin.
- No em dash in code, comments, messages or documentation. One-line Conventional Commits, no trailers, never push, never branch.

## Review Focus

- **Exact bytes, not timestamps:** a file edited within the same second is still detected, because the key is the content hash.
- **Frontmatter-only edits:** the file hash changes, the header is parsed again, and `metadata_hash` decides whether pages that list the document are rebuilt.
- **Title changes:** `get_hash_from_body` still strips the first H1, so renaming a title does not recompile the body on its own.
- **Warnings:** a `Title:` in frontmatter logs at every build and is always parsed.
- **CRLF and BOM:** the cache stores the raw byte hash, so those files simply parse once more than an identical LF file; their keys and derived hashes stay equal to the LF twin.
- **PyYAML upgrade:** the cache is dropped, the build is correct, and the log names the mismatch.

## Baseline

Measured before the change on `/tmp/kb4it-wp7-perf` (1,000 generated documents, techdoc):

| Build | Seconds |
|---|---|
| First (full) | 15.79 |
| Unchanged | 2.24 / 2.21 / 2.21 |

---

### Task 1: Read and parse a document once

**Files:** modify `kb4it/core/files.py`, `kb4it/core/documents.py`; create `tests/core/test_header_cache.py` (unit part).

**Interfaces:**
- `files.get_hash_from_bytes(content: bytes) -> str`: blake2b of the bytes.
- `files.read_document(path: str) -> tuple[str, str]`: open once in binary, return `(text, byte_hash)`. Decode with `SOURCE_ENCODING` (drops a BOM) and normalise `\r\n` / `\r` to `\n`, exactly as text mode did.
- `documents.parse_markdown_attributes(content: str, basename: str) -> tuple[dict[str, list[str]], bool, str, bool]`: the existing parser over already-read text; the last value is `warned`, true when the frontmatter carried `Title`/`title`.
- `documents.get_markdown_attributes(docpath)` keeps returning `(keys, valid, reason)` and delegates to the new parser.
- `documents.get_hash_from_body(path, content: str | None = None)`: use `content` when given, otherwise read as before.

- [x] RED: unit tests for `read_document` (LF, CRLF, BOM give the same text and equal keys/hashes through the parser), `get_hash_from_bytes` stability, `parse_markdown_attributes` warning flag, and the unchanged three-value public helpers.
- [x] GREEN: implement; `get_markdown_attributes` still logs `[UTIL] DOC_INVALID` with the same reasons, including the YAML line/column form.
- [x] Run `python3 -m pytest tests/core/test_header_cache.py tests/core/test_invalid_docs.py tests/core/test_line_endings.py tests/core/test_title_rule.py tests/core/test_values_as_text.py -q`.
- [x] `scripts/devel/typecheck.sh` passes (`documents.py` and `files.py` are in the strict list).
- [x] Commit `refactor(core): read a document once and parse its header from the text`.

### Task 2: Store and reuse the file hash

**Files:** modify `kb4it/core/types.py`, `kb4it/services/processor.py`; extend `tests/core/test_header_cache.py`.

**Interfaces:**
- `DocumentMeta` gains `file_hash: str`, `warned: bool`.
- `Processor.step_00_extraction()`:
  1. `content, file_hash = read_document(filepath)`, with a read/decode failure reported as `[UTIL] DOC_INVALID doc=<name> reason=error error=<err>` and left out as today.
  2. `current = kbdict_cur["document"].get(docId, {})`; reuse only when `current.get("file_hash") == file_hash` and `current.get("warned") is not True`; then take `current["keys"]`, `current["body_hash"]`, `current["metadata_hash"]`.
  3. Otherwise call `parse_markdown_attributes(content, docId)` and compute `get_hash_from_body(filepath, content=content)` and `get_hash_from_dict(keys)`.
  4. Store `file_hash`, `warned`, `keys`, `body_hash`, `metadata_hash`.
  5. Log `[PROCESSOR] HEADER_CACHE doc=<name> action=reuse` or `[PROCESSOR] HEADER_CACHE doc=<name> action=parse reason=<missing|changed|warning>` at debug level.
- The rest of the metadata index, sorting, `Date` conversion and signature logic is untouched.

- [x] RED: a build stores `file_hash` per document, a second build logs one `action=reuse` per document and no `action=parse`, and an edited document logs one `action=parse` with the others reused.
- [x] GREEN: implement. Check `kbdict.json` from the 1,000-document site still gives the same sorted metadata and the same compiled count on the second build.
- [x] Run the header cache test file and `tests/core/test_metadata_order.py tests/core/test_metadata_pages.py tests/core/test_build_state.py -q`.
- [x] Commit `perf(processor): reuse parsed headers when a document did not change`.

### Task 3: PyYAML version invalidation

**Files:** modify `kb4it/services/backend.py`; extend `tests/core/test_header_cache.py`.

- `save_kbdict()` writes `kbdict["pyyaml_version"] = yaml.__version__`.
- `load_kbdict()` compares the stored value with `yaml.__version__`. A mismatch logs `[BACKEND] KBDICT_PYYAML_MISMATCH stored=<old> current=<new>`, sets `runtime["force_all"]`, and returns the empty dictionary that keeps the deploy records, exactly like a KB4IT version mismatch.
- A cache without the key counts as a mismatch (one full build after the upgrade).

- [ ] RED: after a build, changing `pyyaml_version` in `kbdict.json` makes the next build log the mismatch and compile every document; the new cache holds the current version.
- [ ] GREEN: implement.
- [ ] Run `tests/core/test_header_cache.py tests/core/test_json_safety.py tests/core/test_version.py -q`.
- [ ] Commit `perf(backend): drop the cache when the YAML version changes`.

### Task 4: Measurement, full check and changelog

- [ ] On `/tmp/kb4it-wp7-perf`, run three unchanged builds with the new code and record the times next to the 2.22 s baseline in the response note. The first build after the code change parses every header once more because the old cache has no `file_hash`; only the following builds measure the cache.
- [ ] `python3 -m pytest --ignore=tests/browser -q`.
- [ ] `scripts/devel/check_themes.sh` (core change can affect every theme).
- [ ] Build the help site with `python -m kb4it build help/config/repo.json` and run `python -m kb4it verify help/config/repo.json`; record the counts.
- [ ] `CHANGELOG.md` under `## [Unreleased] / ### Changed`: documents are read once per build and unchanged headers are served from `kbdict.json`; a PyYAML upgrade invalidates the cache.
- [ ] Save the report to `responses/<timestamp>_WP7-HEADER-CACHE.md` and commit `docs(changelog): note the header cache`.
