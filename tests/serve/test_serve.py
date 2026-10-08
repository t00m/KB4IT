"""kb4it serve: first build, live reload script, rebuild on change, error banner, lock."""

import json
import subprocess
import sys
import time
import urllib.request

import pytest

from kb4it.core.lock import FileLock
from kb4it.core.webserver import find_free_port
from tests.helpers import isolated_env, page, run_kb4it, write_repo

RUNNER = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read().decode("utf-8")


def _wait(predicate, timeout=60):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            value = predicate()
        except OSError:
            value = None
        if value:
            return value
        time.sleep(0.2)
    raise AssertionError("timed out")


@pytest.fixture
def served(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("Alpha", "First text.", Tag="x")})
    port = find_free_port(start=18642)
    proc = subprocess.Popen([sys.executable, "-c", RUNNER, "serve", str(cfg), "--port", str(port), "--interval", "0.2"],
                            cwd=str(tmp_path), env=isolated_env(home), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    url = f"http://127.0.0.1:{port}/"
    try:
        _wait(lambda: _get(url + "__kb4it/status"))
        yield cfg, url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def _status(url):
    return json.loads(_get(url + "__kb4it/status"))


def test_serve_builds_reloads_and_reports_errors(served):
    cfg, url = served
    assert _status(url) == {"build": 1, "ok": True, "error": ""}
    html = _get(url + "a.html")
    assert "First text." in html and "kb4it-live-reload" in html
    target_html = (cfg.parent.parent / "target" / "a.html").read_text(encoding="utf-8")
    assert "kb4it-live-reload" not in target_html, "the script is never written to disk"

    source = cfg.parent.parent / "source" / "a.md"
    source.write_text(page("Alpha", "Second text.", Tag="x"), encoding="utf-8")
    _wait(lambda: _status(url)["build"] >= 2)
    assert "Second text." in _get(url + "a.html")

    (cfg.parent.parent / "source" / "boom.md").write_text("no frontmatter here\n", encoding="utf-8")
    cfg.write_text(cfg.read_text(encoding="utf-8").replace('"title": "Test"', '"title": "Test", "fail_on_invalid": true'),
                   encoding="utf-8")
    status = _wait(lambda: (lambda s: s if not s["ok"] else None)(_status(url)))
    assert "boom.md" in status["error"]


def test_serve_holds_the_repository_lock(served, tmp_path, home):
    cfg, _url = served
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "already working on this repository" in result.stdout


def test_serve_refuses_a_locked_repository(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")})
    with FileLock(tmp_path / "repo" / "var" / "kb4it.lock"):
        result = run_kb4it("serve", cfg, "--no-watch", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "already working on this repository" in result.stdout


def test_serve_help_lists_its_options(tmp_path, home):
    result = run_kb4it("serve", "--help", cwd=tmp_path, home=home)
    for option in ("--host", "--port", "--no-watch", "--no-reload", "--open", "--interval", "--force"):
        assert option in result.stdout


def test_background_server_rebuilds_without_holding_the_lock(tmp_path):
    from kb4it.core.serve import Server
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("Alpha", "First.", Tag="x")})
    results = []
    live = Server({"config": str(cfg), "interval": 0.2}, holds_lock=False,
                  on_build=lambda ok, error: results.append(ok))
    assert live.build() is True
    live.start_background(str(tmp_path / "repo" / "target"))
    try:
        # Not holding the lock: another build of the repository may run meanwhile.
        with FileLock(tmp_path / "repo" / "var" / "kb4it.lock"):
            pass
        (tmp_path / "repo" / "source" / "a.md").write_text(page("Alpha", "Second.", Tag="x"), encoding="utf-8")
        _wait(lambda: len(results) >= 2)
        assert results[-1] is True
        assert "Second." in _get(live.server.url + "a.html")
    finally:
        live.stop_background()
