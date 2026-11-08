"""help/source/reference-theme-hooks.md is generated from the docstrings; it must match the code."""

import subprocess
import sys

from tests.helpers import ROOT

SCRIPT = ROOT / "scripts" / "devel" / "theme_hooks_doc.py"
PAGE = ROOT / "help" / "source" / "reference-theme-hooks.md"


def test_hook_reference_is_current():
    result = subprocess.run([sys.executable, str(SCRIPT), "--check"], cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr


def test_hook_reference_lists_the_main_hooks():
    text = PAGE.read_text(encoding="utf-8")
    for name in ("page_context", "body_transforms", "render_page", "add_system_page", "checks", "run_checks",
                 "search_record", "ordered_pages", "neighbours", "related_docs", "toc_sidebar", "config_class"):
        assert f"`{name}" in text, name
    assert "## Navigation kit" in text and "## Page pipeline" in text
