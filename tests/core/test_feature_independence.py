"""Built-in features stand alone: a feature imports no other feature module and no themekit mixin.

A feature reaches another one only through requires, uses and site.features (or Feature.feature()).
"""

import ast

import pytest

from kb4it.theme.features import REGISTRY
from tests.helpers import ROOT

FEATURES_DIR = ROOT / "kb4it" / "theme" / "features"
MODULES = sorted(p.stem for p in FEATURES_DIR.glob("*.py") if p.stem != "__init__")


def _imports(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


@pytest.mark.parametrize("module", MODULES)
def test_feature_imports_no_other_feature(module):
    imported = _imports(FEATURES_DIR / f"{module}.py")
    others = {f"kb4it.theme.features.{m}" for m in MODULES if m != module}
    assert not imported & others, "a feature imports another feature"
    assert not any(name.startswith("kb4it.services.themekit") for name in imported)
    assert "kb4it.resources" not in " ".join(imported)


def test_every_feature_module_is_registered():
    modules = {cls.__module__.rsplit(".", 1)[1] for cls in REGISTRY.values()}
    assert set(MODULES) <= modules | {"__init__"}


def test_feature_names_are_unique_and_set():
    assert all(name and cls.name == name for name, cls in REGISTRY.items())
