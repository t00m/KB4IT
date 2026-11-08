"""Layer 1 kits stand alone: a kit imports no other kit and not DocumentTheme (spec anti-goal)."""

import ast
import subprocess
import sys

import pytest

from tests.helpers import ROOT

# Module and mixin class of every Layer 1 kit.
KITS = {
    "kb4it.services.themekit.diagrams": "DiagramsMixin",
    "kb4it.services.themekit.filters": "FilterMixin",
    "kb4it.services.themekit.gallery": "GalleryMixin",
    "kb4it.services.themekit.navigation": "NavigationMixin",
    "kb4it.services.themekit.related": "RelatedMixin",
    "kb4it.services.themekit.tocsidebar": "TocSidebarMixin",
}


def _imports(module):
    path = ROOT / (module.replace(".", "/") + ".py")
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


@pytest.mark.parametrize("module", sorted(KITS))
def test_kit_imports_no_other_kit(module):
    imported = _imports(module)
    assert not imported & (set(KITS) - {module}), "a kit depends on another kit"
    assert "kb4it.services.themekit.DocumentTheme" not in imported
    assert "kb4it.services.themekit" not in imported


@pytest.mark.parametrize("module", sorted(KITS))
def test_kit_imports_alone(module):
    code = (f"from {module} import {KITS[module]} as Kit\n"
            "from kb4it.services.builder import Builder\n"
            "type('T', (Kit, Builder), {})\n")
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
