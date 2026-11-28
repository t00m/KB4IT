"""Post-build checks (P7): a shared Problem type, the anchor check, severities and strict mode."""

import logging
from types import SimpleNamespace

import pytest

from kb4it.core.checks import Problem, check_anchors
from kb4it.core.exceptions import ThemeError
from kb4it.services.builder import Builder
from tests.helpers import mini_theme, page, run_kb4it, write_repo


def _write(folder, name, body):
    (folder / name).write_text(f"<html><body>{body}</body></html>", encoding="utf-8")


def test_problem_text():
    assert str(Problem("ANCHOR_MISSING", "a.html", "to=b.html#x", label="from")) == "ANCHOR_MISSING from=a.html to=b.html#x"
    assert str(Problem("CONTRACT_MISSING", "", "entry=x", severity="error")) == "CONTRACT_MISSING entry=x"
    assert str(Problem("X", "a.html", "")) == "X page=a.html"


def test_anchor_missing_found(tmp_path):
    _write(tmp_path, "a.html", '<a href="b.html#nope">b</a><a href="b.html#here">ok</a><a href="c.html">gone</a>')
    _write(tmp_path, "b.html", '<h2 id="here">Here</h2>')
    problems = check_anchors(tmp_path, ["a.html", "b.html"])
    assert [str(p) for p in problems] == ["ANCHOR_MISSING from=a.html to=b.html#nope",
                                          "ANCHOR_MISSING from=a.html to=c.html"]
    assert {p.severity for p in problems} == {"warning"}


def test_external_links_ignored(tmp_path):
    """Links that leave the target root or the site are not checked (Review Focus 4)."""
    _write(tmp_path, "a.html", '<p id="top"></p><a href="../x.html">up</a><a href="/abs.html">abs</a>'
                               '<a href="mailto:a@b">mail</a><a href="https://x/y.html#z">web</a>'
                               '<a href="#top">top</a><a href="sub/p.html#q">sub</a><a href="">empty</a>')
    assert check_anchors(tmp_path, ["a.html"]) == []


def test_script_routes_are_not_anchors(tmp_path):
    """The Add page reads its fragment as key=value pairs (add.html#new=person&title=X); no element has that id."""
    _write(tmp_path, "a.html", '<a href="add.html#new=person&amp;title=Jane%20Doe">add</a>')
    _write(tmp_path, "add.html", "<p>editor</p>")
    assert check_anchors(tmp_path, ["a.html"]) == []


def test_missing_anchor_on_the_same_page(tmp_path):
    _write(tmp_path, "a.html", '<a href="#gone">x</a>')
    assert [str(p) for p in check_anchors(tmp_path, ["a.html"])] == ["ANCHOR_MISSING from=a.html to=#gone"]


def _host(problems, strict=False):
    return SimpleNamespace(log=logging.getLogger("test-checks"), checks=lambda target: problems,
                           srvbes=SimpleNamespace(get_dict=lambda name: {"strict": strict}))


def test_error_fails_build(tmp_path):
    host = _host([Problem("X", "a.html", "", severity="error")])
    with pytest.raises(ThemeError, match="1 post-build problem"):
        Builder.run_checks(host, str(tmp_path))


def test_strict_fails_on_warning(tmp_path):
    host = _host([Problem("X", "a.html", "")], strict=True)
    with pytest.raises(ThemeError):
        Builder.run_checks(host, str(tmp_path))


def test_warning_passes_without_strict(tmp_path, caplog):
    host = _host([Problem("ANCHOR_MISSING", "a.html", "to=b.html#x", label="from")])
    with caplog.at_level(logging.WARNING, logger="test-checks"):
        assert Builder.run_checks(host, str(tmp_path)) == host.checks(None)
    assert "[CHECK] ANCHOR_MISSING from=a.html to=b.html#x" in caplog.text


def _mini_site(tmp_path, home, **repo):
    theme = mini_theme(tmp_path / "mini")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme), **repo)
    return cfg


def test_build_logs_a_broken_anchor(tmp_path, home):
    cfg = _mini_site(tmp_path, home)
    (tmp_path / "repo" / "source" / "b.md").write_text(page("B", "[x](a.html#nowhere)", Tag="y"), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "[CHECK] ANCHOR_MISSING from=b.html to=a.html#nowhere" in result.stdout


def test_verify_runs_checks(tmp_path, home):
    cfg = _mini_site(tmp_path, home, strict=True)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    page_path = tmp_path / "repo" / "target" / "a.html"
    page_path.write_text(page_path.read_text(encoding="utf-8").replace("</body>", '<a href="a.html#gone">x</a></body>'),
                         encoding="utf-8")
    result = run_kb4it("verify", cfg, cwd=tmp_path / "repo", home=home)
    assert result.returncode == 1, result.stdout
    assert "ANCHOR_MISSING from=a.html to=a.html#gone" in result.stdout


def test_verify_skips_without_target(tmp_path, home):
    cfg = _mini_site(tmp_path, home)
    result = run_kb4it("verify", cfg, cwd=tmp_path / "repo", home=home)
    assert "post-build checks skipped: no built site" in result.stdout


def test_only_real_id_attributes_count(tmp_path):
    _write(tmp_path, "a.html", '<a href="b.html#x">x</a><a href="b.html#y">y</a><a href="b.html#z">z</a>')
    _write(tmp_path, "b.html", '<div data-id="x"></div><p\nid="y"></p><script>var s = \' id="z"\';</script>')
    assert [str(p) for p in check_anchors(tmp_path, ["a.html", "b.html"])] == [
        "ANCHOR_MISSING from=a.html to=b.html#x", "ANCHOR_MISSING from=a.html to=b.html#z"]
