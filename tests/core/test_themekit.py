"""The document themes share their code through kb4it.services.themekit (AR-01)."""

import ast
import math

import pytest

from kb4it.services.builder import Builder
from kb4it.services.themekit import DocumentTheme
from tests.helpers import ROOT

THEMES = ROOT / "kb4it" / "resources" / "themes"
DOCUMENT_THEMES = ("techdoc", "blog", "bookshelf")

# Methods of the AR-01 table that live in themekit; the list grows with each mixin.
SHARED = {
    "metadata": ["get_labels", "get_html_values_from_key", "build_metadata_section", "get_page_actions"],
    "keypages": ["build_page_key", "build_page_key_value", "build_page_properties", "build_tagcloud_from_key",
                 "get_maxkv_freq", "build_page_stats", "build_page_bookmarks", "build_page_index_all"],
    "tables": ["build_datatable"],
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


def test_builder_does_not_grow():
    """apphelp and custom themes subclass Builder, which keeps only its own stubs (D-G2)."""
    shared = {name for names in SHARED.values() for name in names}
    assert shared & set(vars(Builder)) == {"build_page_key", "build_page_key_value"}


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

    def get_documents(self):
        # doc1 and doc2 have Tag=a; doc3 to doc5 have no Tag, which reads as [""]
        return ["doc1.html", "doc2.html", "doc3.html", "doc4.html", "doc5.html"]

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
    def __init__(self, broken=False):  # no services: only what the shared methods use
        self.srvdtb = _Db(broken)
        self.log = _Log()

    def template(self, name):
        return _Template(name)

    def get_theme_var(self):
        return {"page": {}}


class _CloudDb(_Db):
    def get_values(self, doc, key):
        return ["a"] if doc in ("doc1.html", "doc2.html") else [""]


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


def test_cloud_measure_scales_by_log():
    theme = _Theme()
    assert theme.cloud_measure(4, 4) == {"count": 4, "weight": 1.0}
    assert theme.cloud_measure(1, 4)["weight"] == round(math.log(2) / math.log(5), 3)
    assert theme.cloud_measure(0, 0) == {"count": 0, "weight": 0.0}


@pytest.mark.parametrize("skip_empty, weight", [(False, round(math.log(3) / math.log(4), 3)), (True, 1.0)])
def test_tagcloud_scale_with_and_without_the_empty_value(skip_empty, weight):
    """Documents without the property read as an empty value; bookshelf leaves it out of the scale."""
    theme = _Theme()
    theme.srvdtb = _CloudDb()
    theme.tagcloud_scale_skips_empty = skip_empty
    cloud = theme.build_tagcloud_from_key("Tag")
    assert cloud.startswith("<WORDCLOUD") and f"'weight': {weight}" in cloud and "'word': 'a'" in cloud


_TABLE_PROPS = {
    "a.html": {"Title": "A <b>", "Title_Url": "a.html", "Tag": ["x", "y"], "Tag_x_Url": "Tag_x.html"},
    "sys.html": {"Title": "System"},
}


class _TableDb:
    def get_doc_properties(self, doc):
        return _TABLE_PROPS[doc]

    def is_system(self, doc):
        return doc == "sys.html"

    def get_doc_timestamp(self, doc):
        return "2026-10-15T09:30:00"


class _Backend:
    def get_dict(self, name):
        return {}


def test_datatable_rows_and_hooks():
    theme = _Theme()
    theme.srvdtb, theme.srvbes = _TableDb(), _Backend()
    html = theme.build_datatable([], ["a.html", "sys.html"], table_id="t1")
    assert html.startswith("<DATATABLE") and "'table_id', 't1'" in html
    assert "events_20261015.html" in html and "2026-10-15T09:30" in html
    assert "A &lt;b&gt;" in html and "System" not in html
    # Tag_y has no page: the whole cell stays empty, as before the move
    assert "LINK_DATATABLE" not in html
    html = theme.build_datatable(["Tag"], ["a.html"])
    assert "<td class=\"\"></td>" in html

    theme.datatable_value_link = lambda props, key, value: {"title": value, "url": props.get(f"{key}_{value}_Url", "#")}
    html = theme.build_datatable(["Tag"], ["a.html"])
    assert html.count("<LINK_DATATABLE") == 2 and "Tag_x.html" in html
