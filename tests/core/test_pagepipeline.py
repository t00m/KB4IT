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
