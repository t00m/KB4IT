import markdown
import pytest

from kb4it.core.mdlinks import MdLinkExtension, rewrite_md_href
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
