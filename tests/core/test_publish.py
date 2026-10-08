"""Publishing: site_url, sitemap.xml, robots.txt, Atom feed and page metadata."""

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.publish import absolute, site_url
from tests.helpers import page, run_kb4it, write_repo


@pytest.mark.parametrize("raw, expected", [
    (None, None), ("", None),
    ("https://t00m.github.io/blog", "https://t00m.github.io/blog/"),
    ("http://example.org/", "http://example.org/"),
])
def test_site_url(raw, expected):
    assert site_url({"site_url": raw} if raw is not None else {}) == expected


@pytest.mark.parametrize("raw", ["t00m.github.io/blog", "ftp://x.org/", 42])
def test_bad_site_url(raw):
    with pytest.raises(ConfigError):
        site_url({"site_url": raw})


def test_absolute():
    assert absolute("https://x.org/kb/", "a.html") == "https://x.org/kb/a.html"
    assert absolute("https://x.org/kb/", "admin\\index.html") == "https://x.org/kb/admin/index.html"


def test_bad_site_url_stops_the_build(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")}, site_url="example.org")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "site_url" in result.stdout
