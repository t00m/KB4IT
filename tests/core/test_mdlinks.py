import markdown
import pytest

from kb4it.core.mdlinks import (
    MdLinkExtension,
    bare_link_path,
    rewrite_md_href,
    suggest_md,
)
from tests.helpers import mini_theme, page, run_kb4it, write_repo


@pytest.mark.parametrize("href, expected", [
    ("b.md", "b.html"),
    ("b.md#fields", "b.html#fields"),
    ("b.markdown#x", "b.html#x"),
    ("B.MD", "B.html"),
    ("b.md?embed=1#x", "b.html?embed=1#x"),
    ("./b.md", "./b.html"),
    ("my%20page.md#a", "my%20page.html#a"),
    ("https://example.com/b.md", None),
    ("mailto:someone@example.com", None),
    ("/abs/b.md", None),
    ("#local", None),
    ("b.html#x", None),
    ("b.mdx", None),
    ("", None),
])
def test_rewrite_md_href(href, expected):
    assert rewrite_md_href(href) == expected


def test_extension_rewrites_and_records_links():
    md = markdown.Markdown(extensions=["extra", MdLinkExtension()])
    html = md.convert("[a](b.md#fields) [c](https://x.org/d.md) [e][r]\n\n[r]: f.md\n")
    assert 'href="b.html#fields"' in html
    assert 'href="https://x.org/d.md"' in html
    assert 'href="f.html"' in html
    assert md.kb4it_links == [("b.md", "fields"), ("f.md", "")]


def test_build_rewrites_links_and_reports_broken(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {
        "a.md": page("A", "[b](b.md#fields) and [gone](missing.md)", Date="2026-01-01"),
        "b.md": page("B", "## Fields {#fields}\n\ntext", Date="2026-01-02"),
    }, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "a.html").read_text(encoding="utf-8")
    assert 'href="b.html#fields"' in html
    assert "LINK_BROKEN from=a.md to=missing.md" in result.stdout


@pytest.mark.parametrize("href, expected", [
    ("b", "b"), ("dir/b", "dir/b"), ("my%20page", "my page"), ("old.adoc", "old.adoc"), ("OLD.ADOC#x", "OLD.ADOC"),
    ("b.md", None), ("folder/", None), ("#part", None), ("/abs/b", None), ("mailto:x@y.org", None),
    ("https://x.org/page", None), ("resources/images/x.png", None), ("b.html", None), ("", None),
])
def test_bare_link_path(href, expected):
    assert bare_link_path(href) == expected


def test_suggest_md():
    known = {"b.md", "dir/c.md", "old.md"}
    assert suggest_md("b", known) == "b.md"
    assert suggest_md("dir/c", known) == "dir/c.md"
    assert suggest_md("old.adoc", known) == "old.md"
    assert suggest_md("gone", known) is None


def test_extension_records_bare_links_without_rewriting():
    md = markdown.Markdown(extensions=["extra", MdLinkExtension()])
    html = md.convert("[a](b) [c](d.md) [e](old.adoc) [f](https://x.org/g)\n")
    assert 'href="b"' in html and 'href="old.adoc"' in html
    assert md.kb4it_links == [("d.md", "")]
    assert md.kb4it_bare_links == ["b", "old.adoc"]
