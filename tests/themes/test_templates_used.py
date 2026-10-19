"""Every bundled template is used: by name in the code, or as half of a transformation (AR-04, ARC-05)."""

import ast
import json
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


def _theme_template_dirs(theme):
    """The theme's templates folder, then its template base's (AR-01)."""
    resources = PACKAGE / "resources"
    dirs = [resources / "themes" / theme / "templates"]
    base = json.loads((resources / "themes" / theme / "theme.json").read_text(encoding="utf-8")).get("template_base")
    if base:
        dirs.append(resources / "bases" / base / "templates")
    return dirs


def test_every_transformation_has_both_halves():
    common = PACKAGE / "resources" / "common" / "templates"
    for name in _transformations():
        assert (common / f"{name}_MD.tpl").is_file(), name
        for theme in ("techdoc", "blog", "bookshelf"):
            assert any((d / f"{name}_NEW.tpl").is_file() for d in _theme_template_dirs(theme)), (theme, name)


def test_no_template_duplicated_between_themes_sharing_a_base():
    """A template identical in two themes of the same base belongs in the base (AR-01)."""
    themes = sorted((PACKAGE / "resources" / "themes").iterdir())
    by_base = {}
    for theme in themes:
        dirs = _theme_template_dirs(theme.name)
        if len(dirs) > 1:
            by_base.setdefault(dirs[1], []).append(dirs[0])
    duplicated = []
    for folders in by_base.values():
        seen = {}
        for folder in folders:
            for path in sorted(folder.glob("*.tpl")):
                other = seen.setdefault(path.name, path)
                if other is not path and other.read_bytes() == path.read_bytes():
                    duplicated.append(path.name)
    assert duplicated == [], "identical in themes that share a base; move them to the base"


def test_base_templates_are_not_shadowed_by_identical_copies():
    for theme in sorted((PACKAGE / "resources" / "themes").iterdir()):
        dirs = _theme_template_dirs(theme.name)
        if len(dirs) < 2:
            continue
        for path in sorted(dirs[1].glob("*.tpl")):
            own = dirs[0] / path.name
            assert not (own.is_file() and own.read_bytes() == path.read_bytes()), (theme.name, path.name)
