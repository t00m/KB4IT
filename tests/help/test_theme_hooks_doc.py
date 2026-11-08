"""The theme API reference pages are generated from the docstrings; they must match the code."""

import subprocess
import sys

from kb4it.theme import FEATURES
from tests.helpers import ROOT

SCRIPT = ROOT / "scripts" / "devel" / "theme_hooks_doc.py"
PAGE = ROOT / "help" / "source" / "reference-theme-hooks.md"
LEGACY = ROOT / "help" / "source" / "reference-theme-legacy.md"


def test_hook_reference_is_current():
    result = subprocess.run([sys.executable, str(SCRIPT), "--check"], cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr


def test_hook_reference_lists_the_public_api():
    text = PAGE.read_text(encoding="utf-8")
    for name in ("setup", "prepare", "build", "after_build", "after_deploy", "checks", "after_checks", "page_context",
                 "body_transforms", "page_template", "render_page", "finalize_html", "render", "config_class",
                 "datatable_date_cell", "event_documents", "has_day_page", "ordered_pages", "neighbours",
                 "related_candidates", "search_record", "value_page"):
        assert f"`{name}" in text, name
    for name in ("## BaseTheme", "## Site", "## Doc", "## Table", "## Features"):
        assert name in text
    for feature in FEATURES:
        assert f"### {feature}" in text or f"| `{feature}` |" in text, feature


def test_legacy_reference_lists_the_old_hooks():
    text = LEGACY.read_text(encoding="utf-8")
    assert "**Deprecated.**" in text
    for name in ("page_context", "body_transforms", "render_page", "add_system_page", "checks", "run_checks",
                 "search_record", "ordered_pages", "neighbours", "related_docs", "toc_sidebar", "config_class"):
        assert f"`{name}" in text, name
    assert "## Navigation kit" in text and "## Page pipeline" in text
