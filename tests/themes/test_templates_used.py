"""Every bundled template is used: by name in the code, or as half of a transformation (AR-04, ARC-05)."""

import ast
import re

from tests.helpers import ROOT

PACKAGE = ROOT / "kb4it"


def _string_literals():
    found = set()
    for path in PACKAGE.rglob("*.py"):
        if "framework" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
    return found


def _transformations():
    from kb4it.services.builder import Builder
    return set(Builder._XFORM_NAMES)


def test_no_unused_template():
    literals, xforms = _string_literals(), _transformations()
    unused = []
    for path in sorted(PACKAGE.glob("resources/**/templates/*.tpl")):
        stem = path.stem
        base = re.sub(r"_(MD|NEW)$", "", stem)
        if stem in literals or (stem != base and base in xforms):
            continue
        unused.append(str(path.relative_to(ROOT)))
    assert unused == [], "templates that nothing renders; remove them or render them"


def test_every_transformation_has_both_halves():
    common = PACKAGE / "resources" / "common" / "templates"
    for name in _transformations():
        assert (common / f"{name}_MD.tpl").is_file(), name
        for theme in ("techdoc", "blog", "bookshelf"):
            assert (PACKAGE / "resources" / "themes" / theme / "templates" / f"{name}_NEW.tpl").is_file(), (theme, name)
