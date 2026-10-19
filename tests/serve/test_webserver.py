"""The shared local web server: plain serving, live reload injection and the status endpoint."""

import json
import socket
import urllib.request

import pytest

from kb4it.core import webserver
from kb4it.core.webserver import BuildStatus, SiteServer, inject_reload


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, resp.headers.get("Content-Type", ""), resp.read().decode("utf-8")


@pytest.fixture
def site(tmp_path):
    (tmp_path / "index.html").write_text("<html><body><p>Home</p></body></html>", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "index.html").write_text("<p>no body tag</p>", encoding="utf-8")
    (tmp_path / "style.css").write_text("p{}", encoding="utf-8")
    return tmp_path


def test_plain_server_serves_files_unchanged(site):
    server = SiteServer(site).start()
    try:
        status, _ctype, body = _get(server.url)
        assert status == 200 and "kb4it-live-reload" not in body
    finally:
        server.shutdown()


def test_reload_injects_script_into_html_only(site):
    server = SiteServer(site, reload=True).start()
    try:
        _status, ctype, body = _get(server.url)
        assert "text/html" in ctype
        assert body.index("kb4it-live-reload") < body.index("</body>")
        assert "kb4it-live-reload" in _get(server.url + "sub/")[2]
        assert "kb4it-live-reload" not in _get(server.url + "style.css")[2]
        assert "kb4it-live-reload" not in (site / "index.html").read_text(encoding="utf-8")
    finally:
        server.shutdown()


def test_status_endpoint_reports_builds(site):
    status = BuildStatus()
    server = SiteServer(site, reload=True, status=status).start()
    try:
        assert json.loads(_get(server.url + "__kb4it/status")[2]) == {"build": 0, "ok": True, "error": ""}
        status.record(False, "invalid frontmatter in a.md")
        assert json.loads(_get(server.url + "__kb4it/status")[2]) == {
            "build": 1, "ok": False, "error": "invalid frontmatter in a.md"}
    finally:
        server.shutdown()


def test_busy_port_moves_to_the_next(site):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("127.0.0.1", 0))
        taken = busy.getsockname()[1]
        busy.listen(1)
        server = SiteServer(site, port=taken).start()
        try:
            assert server.port != taken
        finally:
            server.shutdown()


def test_inject_without_body_appends():
    assert inject_reload(b"<p>x</p>").startswith(b"<p>x</p><script")
    assert webserver.STATUS_PATH in webserver.RELOAD_SCRIPT
