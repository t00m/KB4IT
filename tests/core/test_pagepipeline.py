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
