"""The document themes share their code through kb4it.services.themekit (AR-01)."""

import ast

import pytest

from kb4it.services.builder import Builder
from kb4it.services.themekit import DocumentTheme
from tests.helpers import ROOT

THEMES = ROOT / "kb4it" / "resources" / "themes"
DOCUMENT_THEMES = ("techdoc", "blog", "bookshelf")

# Methods of the AR-01 table that live in themekit; the list grows with each mixin.
SHARED = {
    "metadata": ["get_labels", "get_html_values_from_key", "build_metadata_section", "get_page_actions"],
}


def _theme_methods(theme):
    tree = ast.parse((THEMES / theme / "logic" / "theme.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Theme":
            return {f.name: f for f in node.body if isinstance(f, ast.FunctionDef)}
    raise AssertionError(f"{theme}: no Theme class")


@pytest.mark.parametrize("theme", DOCUMENT_THEMES)
def test_document_themes_subclass_document_theme(theme):
    tree = ast.parse((THEMES / theme / "logic" / "theme.py").read_text(encoding="utf-8"))
    bases = [ast.unparse(b) for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Theme" for b in n.bases]
    assert bases == ["DocumentTheme"]


def test_shared_methods_are_defined_once():
    """A theme redefines a shared method only with a docstring starting "Override:" that says why."""
    stray = []
    for theme in DOCUMENT_THEMES:
        methods = _theme_methods(theme)
        for names in SHARED.values():
            for name in names:
                node = methods.get(name)
                if node and not (ast.get_docstring(node) or "").startswith("Override:"):
                    stray.append(f"{theme}.{name}")
    assert stray == [], "defined in a theme and in themekit; delete it or document the override"


def test_shared_methods_live_in_themekit():
    for names in SHARED.values():
        for name in names:
            owner = next(c for c in DocumentTheme.__mro__ if name in vars(c))
            assert owner.__module__.startswith("kb4it.services.themekit."), name
            assert not hasattr(Builder, name), f"Builder grew {name}"


class _Template:
    def __init__(self, name):
        self.name = name

    def render(self, var):
        return f"<{self.name} {sorted(var.items())}>"


class _Db:
    def __init__(self, broken=False):
        self.broken = broken

    def get_values(self, doc, key):
        return {"Tag": ["a", "b", ""]}.get(key, [])

    def get_custom_keys(self, doc):
        if self.broken:
            raise KeyError(doc)
        return ["Tag"]


class _Log:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


class _Theme(DocumentTheme):
    def __init__(self, broken=False):  # no services: only what the metadata methods use
        self.srvdtb = _Db(broken)
        self.log = _Log()

    def template(self, name):
        return _Template(name)


def test_metadata_helpers():
    theme = _Theme()
    assert theme.get_html_values_from_key("doc.md", "Tag") == [("Tag_a.html", "a"), ("Tag_b.html", "b"), ("Tag_.html", "")]
    labels = theme.get_labels([("Tag_a.html", "a"), ("Tag_.html", "")])
    assert labels.count("<METADATA_VALUE_LINK") == 1 and "Tag_a.html" in labels
    section = theme.build_metadata_section("doc.md")
    assert section.startswith("<METADATA_SECTION") and "'key': 'Tag'" in section and "'vfkey': 'Tag'" in section
    assert theme.get_page_actions({"x": 1}) == "<SECTION_ACTIONS [('x', 1)]>"


def test_metadata_failure_is_logged_and_raised():
    theme = _Theme(broken=True)
    with pytest.raises(KeyError):
        theme.build_metadata_section("doc.md")
    assert theme.log.errors == ["[THEME] METADATA_FAIL doc=doc.md error='doc.md'"]
