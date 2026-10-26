"""Backlinks: pages list the documents that link to them, and stay correct across incremental builds."""

import json

import pytest

from tests.helpers import page, run_kb4it, write_repo

THEMES = ["techdoc", "blog", "bookshelf", "apphelp"]


def _conf(theme):
    from tests.helpers import ROOT
    path = ROOT / "kb4it" / "resources" / "themes" / theme / "apps" / "default" / "config" / "repo.json"
    conf = json.loads(path.read_text(encoding="utf-8"))
    for key in ("theme", "source", "target", "title"):
        conf.pop(key, None)
    if theme == "apphelp":
        conf.setdefault("apphelp", {})["strict"] = False
    return conf


def _page(title, body):
    return page(title, body, Category="Post", Date="2026-10-08", DocType="Reference", Tag="x")


@pytest.mark.parametrize("theme", THEMES)
def test_target_lists_the_linking_page(tmp_path, home, theme):
    pages = {"a.md": _page("Alpha", "See [the beta page](b.md#part)."), "b.md": _page("Beta", "## Part\n\nText.")}
    cfg = write_repo(tmp_path / theme, theme, pages, **_conf(theme))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / theme / "target"
    beta = (target / "b.html").read_text(encoding="utf-8")
    assert "Linked from" in beta and 'href="a.html"' in beta.split("Linked from", 1)[1]
    assert "Linked from" not in (target / "a.html").read_text(encoding="utf-8")


def test_incremental_backlinks(tmp_path, home):
    pages = {"a.md": _page("Alpha", "See [beta](b.md)."), "b.md": _page("Beta", "Text."), "c.md": _page("Gamma", "Alone.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    source = tmp_path / "repo" / "source"
    target = tmp_path / "repo" / "target"

    unchanged = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert "COMPILED doc=b.md" not in unchanged.stdout, "nothing changed, nothing recompiled"

    (source / "a.md").write_text(_page("Alpha", "No more links."), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert "COMPILED doc=b.md" in result.stdout, "b.md lost a backlink and is rebuilt"
    assert "COMPILED doc=c.md" not in result.stdout
    assert "Linked from" not in (target / "b.html").read_text(encoding="utf-8")

    links = json.loads((tmp_path / "repo" / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))["links"]
    assert links["a.md"] == [] and links["b.md"] == []


def test_backlinks_false_hides_the_section(tmp_path, home):
    pages = {"a.md": _page("Alpha", "See [beta](b.md)."), "b.md": _page("Beta", "Text.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages, backlinks=False)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "Linked from" not in (tmp_path / "repo" / "target" / "b.html").read_text(encoding="utf-8")


def test_verify_reports_broken_links_and_anchors(tmp_path, home):
    pages = {"a.md": _page("Alpha", "[ok](b.md#part) [gone](missing.md) [no anchor](b.md#nowhere)"),
             "b.md": _page("Beta", "## Part\n\nText.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    result = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "LINK_BROKEN from=a.md to=missing.md" in result.stdout
    assert "ANCHOR_MISSING from=a.md to=b.md#nowhere" in result.stdout
    assert "b.md#part" not in result.stdout
    build = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert build.returncode == 0, "a broken link is only a warning when building"


def test_build_and_verify_report_links_without_extension(tmp_path, home):
    pages = {"a.md": _page("Alpha", "[one](b) [two](c.adoc) [three](b.md)"), "b.md": _page("Beta", "Text.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    build = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert build.returncode == 0
    assert "LINK_NO_EXTENSION from=a.md to=b suggest=b.md" in build.stdout
    assert "LINK_BROKEN from=a.md to=c.adoc" in build.stdout
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert verify.returncode == 1
    assert "LINK_NO_EXTENSION from=a.md to=b suggest=b.md" in verify.stdout and "LINK_BROKEN from=a.md to=c.adoc" in verify.stdout


def test_a_link_without_extension_is_not_a_backlink(tmp_path, home):
    pages = {"a.md": _page("Alpha", "See [beta](b)."), "b.md": _page("Beta", "Text.")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "Linked from" not in (tmp_path / "repo" / "target" / "b.html").read_text(encoding="utf-8")
