"""kb4it/theme/site.py: the read-only view of a knowledge base that themes get."""

import logging

import pytest

from kb4it.services.database import Database
from kb4it.services.processor import BuildPlan
from kb4it.theme.site import Doc, Site, Table, page_name


class Backend:
    def __init__(self, repo, theme=None, plan=None, dirs=None):
        self.repo, self.theme, self.plan, self.dirs = repo, theme or {"id": "x"}, plan, dirs or {}

    def get_dict(self, domain):
        return {"repo": self.repo, "theme": self.theme}.get(domain)

    def get_path(self, name):
        return self.dirs.get(name)

    def get_plan(self):
        return self.plan


DOCS = {
    "a.md": {"Title": ["Alpha"], "Date": ["2025-03-02"], "Tag": ["linux", "backup"]},
    "b.md": {"Title": ["Beta"], "Date": ["2025-01-10"], "Tag": ["linux"], "Author": ["Jane Doe"]},
    "c.md": {"Title": ["Gamma"], "Tag": ["backup"], "Secret": ["x"]},
    "index.md": {"Title": ["Home"], "SystemPage": ["Yes"]},
}


def make_site(plan=None, dirs=None, host=None, repo=None):
    backend = Backend(repo or {"ignored_keys": ["Secret"], "title": "KB", "nested": {"list": [1, 2]}},
                      plan=plan, dirs=dirs)
    db = Database.__new__(Database)
    db.log = logging.getLogger("test")
    db.get_service = lambda name: backend
    db._initialize()
    for doc_id, keys in DOCS.items():
        db.add_document(doc_id)
        for key, values in keys.items():
            for value in values:
                db.add_document_key(doc_id, key, value)
    return Site(db, backend, host=host)


def test_documents_are_newest_first_without_system_pages():
    site = make_site()
    assert [d.id for d in site.documents] == ["a.md", "b.md", "c.md"]
    assert len(site.documents) == 3
    assert "index.md" not in site.documents and "a.md" in site.documents
    assert site.documents.latest(1) == [Doc(site, "a.md")]
    assert [d.id for d in site.documents.with_value("Tag", "backup")] == ["a.md", "c.md"]
    assert [d.id for d in site.documents.filter(lambda d: d.date is None)] == ["c.md"]
    assert site.documents.get("index.md").is_system and site.documents.get("nope.md") is None


def test_doc_values_are_read_only():
    doc = make_site().doc("a.md")
    assert (doc.title, doc.name, doc.url, doc.date) == ("Alpha", "a", "a.html", "2025-03-02")
    assert doc.values("Tag") == ("linux", "backup") and isinstance(doc.values("Tag"), tuple)
    assert doc.values("Missing") == () and doc.value("Missing", "-") == "-"
    assert doc.links("Tag") == [{"name": "linux", "url": "Tag_linux.html"}, {"name": "backup", "url": "Tag_backup.html"}]
    with pytest.raises(TypeError):
        doc.properties["Tag"] = ("x",)
    assert doc.datetime.year == 2025


def test_properties():
    site = make_site()
    assert "Secret" not in site.properties.keys() and "Tag" in site.properties.keys()
    assert "Secret" in site.properties.all_keys()
    assert site.properties.values("Tag") == ("backup", "linux")
    assert "Title" in site.properties.blocked and "Secret" in site.properties.ignored
    assert site.properties.url("Tag", "SAP basis") == page_name("Tag", "SAP basis") == "Tag_SAP_basis.html"


def test_settings_are_frozen_copies():
    site = make_site()
    assert site.repo["title"] == "KB" and site.repo["nested"]["list"] == (1, 2)
    with pytest.raises(TypeError):
        site.repo["title"] = "changed"
    with pytest.raises(TypeError):
        site.repo["nested"]["new"] = 1


def test_build_reads_the_plan():
    plan = BuildPlan(docs_to_compile={"b.md"}, K_PATH=[("Tag", ["linux"], True), ("OS", [], False)],
                     invalid_docs=[("bad.md", "no title")], backlinks={"a.md": [["Beta", "b.md"]]},
                     modified={"a.md": "2025-04-01"})
    site = make_site(plan=plan)
    assert site.build.changed("b.md") and not site.build.changed(site.doc("a.md"))
    assert site.build.documents_changed == 1 and site.build.keys_changed == ("Tag",)
    assert site.build.invalid == ("bad.md",) and not site.build.force
    assert site.doc("a.md").backlinks == [{"title": "Beta", "url": "b.html"}]
    assert site.doc("a.md").modified == "2025-04-01"


def test_without_a_plan_everything_counts_as_changed():
    site = make_site()
    assert site.build.changed("a.md") and site.build.force


def test_source_reads_the_markdown(tmp_path):
    (tmp_path / "a.md").write_text("# Alpha\n", encoding="utf-8")
    site = make_site(dirs={"source": str(tmp_path)})
    assert site.doc("a.md").source() == "# Alpha\n"
    assert site.doc("index.md").source() == ""


def test_writers_need_a_host():
    with pytest.raises(RuntimeError):
        make_site().page("x", "X", "<p></p>")


def test_writers_delegate_to_the_host():
    calls = []

    class Host:
        def add_system_page(self, *args, **kwargs):
            calls.append(("page", args, kwargs))

        def _reuse_cached_page(self, *args):
            calls.append(("keep", args))
            return True

        def build_datatable(self, *args):
            calls.append(("table", args))
            return "<table>"

    site = make_site(host=Host())
    site.page("about", "About", "text", markdown=True)
    assert site.keep("stats")
    assert site.table(Table(documents=(site.doc("a.md"), "b.md"), columns=("Date", "Title"), id="t")) == "<table>"
    assert calls == [("page", ("about", "About", "text"), {"as_html": False, "listing": False}),
                     ("keep", ("stats", "nck", "no_changes", "stats")),
                     ("table", (["Date", "Title"], ["a.md", "b.md"], "t"))]


def test_features_by_name_and_attribute():
    site = Site(None, Backend({}), features={"events": "E"})
    assert site.features["events"] == site.features.events == "E"
    with pytest.raises(AttributeError):
        site.features.gallery
