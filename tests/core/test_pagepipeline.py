"""The shared page facts and page pipeline of every theme (kb4it/services/pagepipeline.py)."""

from types import SimpleNamespace

import pytest

from kb4it.services.builder import Builder

GIT = {"git": True, "git_user": "u", "git_repo": "r", "git_branch": "main", "git_path": "docs"}


def builder(repo, props=None):
    """A Builder with only the services these tests touch."""
    props = props or {}
    b = Builder.__new__(Builder)
    b.srvbes = SimpleNamespace(get_dict=lambda name: repo if name == "repo" else {})
    b.srvdtb = SimpleNamespace(get_doc_properties=lambda doc: props.get(doc, {}))
    return b


@pytest.mark.parametrize("server", ["https://github.com", "https://github.com/", "github.com", "/github.com/"])
def test_edit_url_accepts_host_or_url(server):
    assert builder({**GIT, "git_server": server}).edit_url("a.md") == "https://github.com/u/r/edit/main/docs/a.md"


def test_edit_url_keeps_another_scheme():
    assert builder({**GIT, "git_server": "http://git.local"}).edit_url("a.md") == \
        "http://git.local/u/r/edit/main/docs/a.md"


def test_edit_url_without_git_path_has_no_double_slash():
    repo = {**GIT, "git_server": "github.com", "git_path": ""}
    assert builder(repo).edit_url("a.md") == "https://github.com/u/r/edit/main/a.md"


def test_edit_url_root_is_the_source_folder():
    assert builder({**GIT, "git_server": "github.com"}).edit_url() == "https://github.com/u/r/edit/main/docs"


@pytest.mark.parametrize("change", [{"git": False}, {"git_user": ""}, {"git_repo": "{repo}"}])
def test_edit_url_is_empty_when_git_is_not_ready(change):
    assert builder({**GIT, "git_server": "github.com", **change}).edit_url("a.md") == ""


def test_page_title_uses_title_or_untitled_label():
    b = builder({}, props={"a.md": {"Title": "Alpha"}, "b.md": {}})
    b.untitled_label = "Untitled"
    assert b.page_title("a.md") == "Alpha"
    assert b.page_title("b.md") == "Untitled"


@pytest.fixture
def fake_builder():
    """A Builder that records what it distributes and what it writes into the database."""
    b = Builder.__new__(Builder)
    b.distributed = []
    b.db_calls = []
    b.distribute_md = lambda name, content, as_html=True, listing=False: \
        b.distributed.append((name, content, as_html, listing))
    b.srvdtb = SimpleNamespace(
        add_document=lambda doc: b.db_calls.append(("add_document", doc)),
        add_document_key=lambda doc, key, value: b.db_calls.append(("add_document_key", doc, key, value)))
    return b


def test_add_system_page_distributes_and_registers(fake_builder):
    fake_builder.add_system_page("stats", "Stats", "<p>x</p>", listing=True)
    assert fake_builder.distributed == [("stats", "<p>x</p>", True, True)]
    assert fake_builder.db_calls == [("add_document", "stats.md"),
                                     ("add_document_key", "stats.md", "Title", "Stats"),
                                     ("add_document_key", "stats.md", "SystemPage", "Yes")]


def test_add_system_page_keeps_markdown_pages(fake_builder):
    fake_builder.add_system_page("help", "Help", "# Help", as_html=False)
    assert fake_builder.distributed == [("help", "# Help", False, False)]


def test_add_system_page_without_html_only_registers(fake_builder):
    fake_builder.add_system_page("all", "All documents")
    assert fake_builder.distributed == []
    assert ("add_document", "all.md") in fake_builder.db_calls


class _Tpl:
    def __init__(self, text):
        self.text = text

    def render(self, **kwargs):
        return self.text


class Recorder(Builder):
    """A Builder whose hooks note the order they run in."""

    def page_toc(self, source_html):
        self.calls.append("page_toc")
        return ""

    def page_context(self, doc_id, var):
        self.calls.append("page_context")
        self.body_in_context = var["source_html"]
        return var

    def body_transforms(self, doc_id, var):
        self.calls.append("body_transforms")
        return [str.upper]

    def page_actions(self, var):
        self.calls.append("page_actions")
        return ""

    def render_page(self, doc_id, var):
        self.calls.append("render_page")
        self.seen = var
        return var["source_html"]

    def finalize_html(self, html):
        self.calls.append("finalize_html")
        return f"FINAL {html}"


def _pipeline_builder(cls, props=None, system=False):
    import logging
    b = cls.__new__(cls)
    b.calls = []
    b._xform_pairs = []  # no heading templates to load
    b.page_pipeline = True
    b.has_template = lambda name: True
    b.log = logging.getLogger("kb4it-test-pipeline")
    b.get_theme_var = lambda: {"page": {"title": ""}}
    b.srvbes = SimpleNamespace(get_dict=lambda name: {})
    b.srvdtb = SimpleNamespace(get_doc_properties=lambda doc: dict(props or {}),
                               is_system=lambda doc: system)
    b.template = lambda name: _Tpl({"HTML_HEADER_COMMON": "H", "HTML_BODY": "B", "HTML_FOOTER": "F"}[name])
    return b


@pytest.fixture
def page_files(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "a.html").write_text("<p>body</p>", encoding="utf-8")
    return tmp_path


def test_pipeline_runs_hooks_in_order(page_files):
    b = _pipeline_builder(Recorder, {"Title": "A"})
    b.build_page(str(page_files / "a.md"))
    assert b.calls == ["page_toc", "page_context", "body_transforms", "page_actions", "render_page", "finalize_html"]
    assert (page_files / "a.html").read_text(encoding="utf-8") == "FINAL <P>BODY</P>"


def test_pipeline_fills_the_shared_page_keys(page_files):
    b = _pipeline_builder(Recorder, {"Title": "A"}, system=True)
    b.build_page(str(page_files / "a.md"))
    var = b.seen
    assert (var["basename_md"], var["basename_hdoc"], var["source_md"]) == ("a.md", "a.html", "# A\n")
    assert var["SystemPage"] is True and var["has_toc"] is True and var["edit_url"] == ""
    assert var["page"]["title"] == "A" and var["page"]["title-tooltip"] == "A"
    assert var["keys"] == {"Title": "A"} and var["timestamp"]
    assert b.body_in_context == "<p>body</p>"  # the compiled body, before the transforms
    assert var["source_html"] == "<P>BODY</P>"


def test_pipeline_logs_missing_html_with_theme_area(page_files, caplog):
    b = _pipeline_builder(Recorder)
    b.log_area = "BOOKSHELF"
    with caplog.at_level("ERROR", logger="kb4it-test-pipeline"):
        b.build_page(str(page_files / "missing.md"))
    assert "[BOOKSHELF] HTML_MISSING doc=missing.md" in caplog.text
    assert b.calls == []


def test_default_render_is_header_body_footer(page_files):
    b = _pipeline_builder(Builder, {"Title": "A"})
    b.build_page(str(page_files / "a.md"))
    assert (page_files / "a.html").read_text(encoding="utf-8") == "HBF"


def test_long_title_is_ellipsized_unless_the_theme_says_no(page_files):
    title = "T" * 100
    b = _pipeline_builder(Recorder, {"Title": title})
    b.build_page(str(page_files / "a.md"))
    assert len(b.seen["page"]["title"]) < 100 and b.seen["page"]["title-tooltip"] == title
    (page_files / "a.html").write_text("<p>body</p>", encoding="utf-8")
    b = _pipeline_builder(Recorder, {"Title": title})
    b.ellipsize_titles = False
    b.build_page(str(page_files / "a.md"))
    assert b.seen["page"]["title"] == title


def test_untitled_page_uses_label_without_ellipsis(page_files):
    b = _pipeline_builder(Recorder, {})
    b.untitled_label = "No title found..."
    b.build_page(str(page_files / "a.md"))
    assert b.seen["page"]["title"] == "No title found..." == b.seen["page"]["title-tooltip"]


def test_without_opt_in_build_page_leaves_the_body(page_files):
    b = _pipeline_builder(Recorder, {"Title": "A"})
    b.page_pipeline = False
    b.build_page(str(page_files / "a.md"))
    assert b.calls == [] and (page_files / "a.html").read_text(encoding="utf-8") == "<p>body</p>"


def test_render_skips_missing_header_and_footer(page_files):
    b = _pipeline_builder(Builder, {"Title": "A"})
    b.has_template = lambda name: name == "HTML_BODY"
    b.build_page(str(page_files / "a.md"))
    assert (page_files / "a.html").read_text(encoding="utf-8") == "B"
