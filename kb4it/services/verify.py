"""
Verify service: the checks of kb4it verify (documents, theme hook, repo.json settings, links).

# File: verify.py
# Author: Tomás Vírseda
# License: GPL v3
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.exceptions import ConfigError, KB4ITError
from kb4it.core.mdconfig import load_settings
from kb4it.core.mdlinks import scan_document, suggest_md
from kb4it.core.paths import resolve_repo_path
from kb4it.core.structured import iso_date, load_seo
from kb4it.core.util import (SOURCE_ENCODING, fences_in_blocks, get_document_attributes, get_source_docs,
                             is_windows_reserved, json_load, page_name_clashes, raw_script_lines)
from kb4it.services.addpage import ADD_DOC, check_editor_setting, check_theme_editor, editor_on


class VerifyMixin:
    """kb4it verify, for Workflow."""

    def _verify_links(self, docs):
        """LINK_BROKEN, LINK_NO_EXTENSION and ANCHOR_MISSING lines for links between source documents."""
        scanned = {}
        for doc in docs:
            try:
                scanned[os.path.basename(doc)] = scan_document(doc)
            except Exception as e:
                self.log.warning(f"[LINKS] SCAN_FAIL doc={os.path.basename(doc)} error={e}")
        problems = []
        for name in sorted(scanned):
            links, _anchors, bare = scanned[name]
            for path in bare:
                suggestion = suggest_md(path, set(scanned))
                if suggestion:
                    problems.append(f"LINK_NO_EXTENSION from={name} to={path} suggest={suggestion}")
                else:
                    problems.append(f"LINK_BROKEN from={name} to={path}")
            for path, fragment in links:
                target = os.path.normpath(path).replace(os.sep, "/")
                if target not in scanned:
                    problems.append(f"LINK_BROKEN from={name} to={path}")
                elif fragment and fragment not in scanned[target][1]:
                    problems.append(f"ANCHOR_MISSING from={name} to={path}#{fragment}")
        return problems

    def verify_sources(self):
        """Verify project sources, display non-conformant ones and fail when there are any."""
        self.log.info("[WORKFLOW] ACTION name=verify_sources")
        backend = self.app.get_service("Backend")
        config_file = backend.get_value("app", "config")

        if config_file is None or not os.path.exists(config_file):
            print("Error: Configuration file not found.")
            raise ConfigError(f"Configuration file not found: {config_file}")

        try:
            repo = json_load(config_file)
        except Exception as e:
            self.log.error(f"[WORKFLOW] VERIFY_ERROR reason={e}")
            raise ConfigError(f"Config load failed: {e}") from e

        source_dir = repo.get("source")
        if not source_dir:
            print("Error: 'source' directory not defined in config.")
            raise ConfigError("'source' directory not defined in config")
        source_dir = resolve_repo_path(source_dir, Path(config_file).absolute().parent.parent)
        if not os.path.exists(source_dir):
            print(f"Error: Source directory not found: {source_dir}")
            raise ConfigError(f"Source directory not found: {source_dir}")

        docs = get_source_docs(source_dir)
        if not docs:
            print(f"No source documents found in {source_dir}")
            return

        print(f"Verifying {len(docs)} source documents in {source_dir}...")
        non_conformant = []
        theme_class = self._theme_class(repo, config_file)
        reserved = tuple(getattr(theme_class, "reserved_pages", ()))
        if self._editor_on(repo, config_file, theme_class):
            reserved = (*reserved, ADD_DOC)
        for doc in docs:
            if is_windows_reserved(doc) or os.path.basename(doc) in reserved:
                non_conformant.append((doc, "reserved_name"))
                continue
            keys, success, reason = get_document_attributes(doc)
            if not success:
                non_conformant.append((doc, reason))
                continue
            for value in keys.get("Modified") or []:
                if value and not iso_date(value):
                    non_conformant.append((doc, f"bad_modified_date value={value}"))
        for first, second in page_name_clashes(os.path.basename(d) for d in docs):
            non_conformant.append((os.path.join(source_dir, second), f"name_clash_with={first}"))

        if non_conformant:
            print("\nNon-conformant source files found:")
            print("-" * 80)
            for doc, reason in non_conformant:
                print(f"{os.path.abspath(doc)} (Reason: {reason})")
            print("-" * 80)
            print(f"Total: {len(non_conformant)} non-conformant files.")
        else:
            print("\nAll source documents are conformant.")

        try:
            problems = self._theme_verify(repo, config_file, docs)
        except Exception as e:
            self.log.error(f"[WORKFLOW] THEME_VERIFY_ERROR reason={e}")
            raise KB4ITError(f"Theme verify hook failed: {e}") from e
        settings = None
        try:
            settings = load_settings(repo)
        except ConfigError as e:
            problems = [f"repo.json: {e}", *problems]
        try:
            check_editor_setting(repo)
        except ConfigError as e:
            problems = [str(e), *problems]
        seo = None
        try:
            seo = load_seo(repo)
        except ConfigError as e:
            problems = [str(e), *problems]
        if problems:
            print("\nTheme checks:")
            for line in problems:
                print(f"  {line}")
            print(f"Total: {len(problems)} theme problems.")

        markdown_warnings = self._verify_fences(docs, settings)
        if markdown_warnings:
            print("\nMarkdown (warnings):")
            for line in markdown_warnings:
                print(f"  {line}")

        raw_html = self._verify_raw_scripts(docs, settings)
        if raw_html:
            print("\nRaw HTML (information: it reaches the pages as written; see markdown.sanitize):")
            for line in raw_html:
                print(f"  {line}")

        if seo is not None and seo.index is None:
            self.log.info("[SEO] INDEX_UNSET hint=set seo.index in repo.json to true or false")
            print("\nSearch engines (information):")
            print("  INDEX_UNSET: decide whether search engines may index this site; set \"seo\": {\"index\": true} "
                  "or {\"index\": false} in repo.json")

        link_problems = self._verify_links(docs)
        if link_problems:
            print("\nLinks:")
            for line in link_problems:
                print(f"  {line}")
            print(f"Total: {len(link_problems)} broken links.")

        if non_conformant or problems or link_problems:
            raise KB4ITError(f"Verification failed: {len(non_conformant)} non-conformant files, "
                             f"{len(problems)} theme problems, {len(link_problems)} broken links")

    def _verify_fences(self, docs, settings):
        """MD_FENCE_IN_BLOCK lines for fences that python-markdown cannot see without superfences."""
        if settings is None or "pymdownx.superfences" in settings.extensions:
            return []
        lines = []
        for doc in sorted(docs):
            with open(doc, encoding=SOURCE_ENCODING) as fh:
                numbers = fences_in_blocks(fh.read())
            if numbers:
                name = os.path.basename(doc)
                self.log.warning(f"[WORKFLOW] MD_FENCE_IN_BLOCK doc={name} lines={','.join(map(str, numbers))}")
                lines.append(f"MD_FENCE_IN_BLOCK doc={name} lines={','.join(map(str, numbers))}: "
                             "indent the code instead of fencing it, or enable pymdownx.superfences")
        return lines

    def _verify_raw_scripts(self, docs, settings):
        """DOC_RAW_SCRIPT lines for documents with scripts or event handlers, when sanitize is off."""
        if settings is None or settings.sanitize:
            return []
        lines = []
        for doc in sorted(docs):
            with open(doc, encoding=SOURCE_ENCODING) as fh:
                numbers = raw_script_lines(fh.read())
            if numbers:
                name = os.path.basename(doc)
                line = f"DOC_RAW_SCRIPT doc={name} lines={','.join(map(str, numbers))}"
                self.log.info(f"[WORKFLOW] {line}")
                lines.append(line)
        return lines

    def _find_theme_dir(self, repo, config_file):
        """Return the theme folder for a repo, following the same order as the build."""
        root = Path(config_file).absolute().parent.parent
        if repo.get("theme_path"):
            return resolve_repo_path(repo["theme_path"], root)
        theme = repo.get("theme", "")
        source = resolve_repo_path(repo.get("source", "source"), root)
        for base in (os.path.join(source, "resources", "themes"), ENV["LPATH"]["THEMES"], ENV["GPATH"]["THEMES"]):
            candidate = os.path.join(base, theme)
            if os.path.isfile(os.path.join(candidate, "theme.json")):
                return candidate
        return None

    def _editor_on(self, repo, config_file, theme_class):
        """True when the Add page is on: theme_class supports it and editor_on() says so."""
        theme_dir = self._find_theme_dir(repo, config_file)
        try:
            with open(os.path.join(theme_dir, "theme.json"), encoding="utf-8") as fin:
                theme = json.load(fin)
        except (OSError, ValueError, TypeError):
            theme = {}
        if not isinstance(theme, dict):
            theme = {}
        check_theme_editor(theme)
        if not getattr(theme_class, "add_page", False):
            return False
        return editor_on(repo, theme)

    def _theme_class(self, repo, config_file):
        """The Theme class of logic/theme.py in the repository's theme, or None. It runs theme.py, so call it once."""
        theme_dir = self._find_theme_dir(repo, config_file)
        logic = os.path.join(theme_dir, "logic") if theme_dir else ""
        path = os.path.join(logic, "theme.py")
        if not os.path.isfile(path):
            return None
        sys.path.insert(0, logic)
        try:
            spec = importlib.util.spec_from_file_location(f"kb4it_reserved_{repo.get('theme', 'theme')}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.Theme
        except Exception:
            return None
        finally:
            sys.path.remove(logic)

    def _theme_verify(self, repo, config_file, docs):
        """Run the theme's optional logic/verify.py and return its problem lines."""
        theme_dir = self._find_theme_dir(repo, config_file)
        hook = os.path.join(theme_dir, "logic", "verify.py") if theme_dir else ""
        if not os.path.isfile(hook):
            return []
        spec = importlib.util.spec_from_file_location(f"kb4it_verify_{repo.get('theme', 'theme')}", hook)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        metadata = {}
        for doc in docs:
            keys, ok, _reason = get_document_attributes(doc)
            if ok:
                metadata[os.path.basename(doc)] = keys
        return [str(line) for line in module.verify(repo, metadata)]
