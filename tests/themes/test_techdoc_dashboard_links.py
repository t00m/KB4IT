"""techdoc dashboard: no link to a page the build never writes (found by the post-build check)."""

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo


def _build(tmp_path, home, docs):
    cfg = write_repo(tmp_path / "repo", "techdoc", docs, **_app_conf("techdoc"))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / "repo" / "target"
    return target, (target / "index.html").read_text(encoding="utf-8"), result.stdout


def test_authors_stat_without_authors_is_not_a_link(tmp_path, home):
    target, html, log = _build(tmp_path, home, {"a.md": page("A", "Text.", Category="Note", Date="2020-01-01", Tag="x")})
    assert 'href="Author.html"' not in html and not (target / "Author.html").exists()
    assert "ANCHOR_MISSING from=index.html to=Author.html" not in log


def test_month_headers_link_only_built_pages(tmp_path, home):
    import re
    from datetime import date
    today = date.today().isoformat()
    docs = {"c.md": page("C", "Text.", Category="Record", WorkType="Change", Date=f"{today} 23:59", Tag="x")}
    target, html, log = _build(tmp_path, home, docs)
    headers = re.findall(r'<div class="kb-events-month-header">(.*?)</div>', html)
    assert len(headers) == 2 and "Current" in headers[0] and "Next" in headers[1]
    assert "<a " not in headers[1], "next month has no events, so no page"
    for link in re.findall(r'href="(events_\d+\.html)"', " ".join(headers)):
        assert (target / link).is_file(), link
    assert "ANCHOR_MISSING from=index.html to=events_" not in log
