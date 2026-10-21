"""The local web server answers missing pages with the site's 404.html."""

import urllib.error
import urllib.request

import pytest

from kb4it.core.webserver import SiteServer

PAGE = "<html><body><h1>Lost page</h1></body></html>"


def _fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8")


@pytest.mark.parametrize("reload", [False, True])
def test_missing_page_serves_site_404(tmp_path, reload):
    (tmp_path / "index.html").write_text("<p>Home</p>", encoding="utf-8")
    (tmp_path / "404.html").write_text(PAGE, encoding="utf-8")
    server = SiteServer(tmp_path, reload=reload).start()
    try:
        status, body = _fetch(server.url + "nope.html")
        assert status == 404
        assert "Lost page" in body
        assert ("kb4it-live-reload" in body) is reload
        status, body = _fetch(server.url + "nope.html", "HEAD")
        assert status == 404 and body == ""
    finally:
        server.shutdown()


def test_missing_page_without_404_html(tmp_path):
    (tmp_path / "index.html").write_text("<p>Home</p>", encoding="utf-8")
    server = SiteServer(tmp_path).start()
    try:
        status, body = _fetch(server.url + "nope.html")
        assert status == 404
        assert "Error response" in body and "Lost page" not in body
    finally:
        server.shutdown()


def test_served_404_base_points_to_local_root(tmp_path):
    page = '<html><head>\n<base href="https://ex.org/kb/">\n</head><body><h1>Lost page</h1></body></html>'
    (tmp_path / "404.html").write_text(page, encoding="utf-8")
    server = SiteServer(tmp_path).start()
    try:
        status, body = _fetch(server.url + "deep/nope.html")
        assert status == 404
        assert '<base href="/">' in body
        assert "ex.org" not in body
    finally:
        server.shutdown()
    assert (tmp_path / "404.html").read_text(encoding="utf-8") == page
