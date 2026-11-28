"""blog document pages: which body template a page gets (theme base, part 1)."""

from tests.helpers import page, run_kb4it, write_repo

POST_MARKER = "post-card"  # printed by POST_HTML_SINGLE only


def _build(tmp_path, home, pages, **config):
    cfg = write_repo(tmp_path / "repo", "blog", pages, **config)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return tmp_path / "repo" / "target"


def _html(target, name):
    return (target / name).read_text(encoding="utf-8")


def test_strict_post_uses_post_template(tmp_path, home):
    target = _build(tmp_path, home, {"a.md": page("A", Category="Post", Date="2026-01-01"),
                                     "b.md": page("B", Category="Note", Date="2026-01-02")}, strict=True)
    assert POST_MARKER in _html(target, "a.html")
    assert POST_MARKER not in _html(target, "b.html")


def test_without_strict_every_document_is_a_post(tmp_path, home):
    target = _build(tmp_path, home, {"b.md": page("B", Category="Note", Date="2026-01-02")})
    assert POST_MARKER in _html(target, "b.html")


def test_post_template_failure_falls_back_to_plain_body(tmp_path, home):
    overrides = tmp_path / "repo" / "overrides" / "templates"
    overrides.mkdir(parents=True)
    (overrides / "POST_HTML_SINGLE.tpl").write_text("${var['missing']['x']}", encoding="utf-8")
    target = _build(tmp_path, home, {"a.md": page("A", Category="Post", Date="2026-01-01")})
    html = _html(target, "a.html")
    assert POST_MARKER not in html and 'class="kb-main"' in html
    log = (tmp_path / "repo" / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")
    assert "[THEME] POST_TEMPLATE_FALLBACK doc=a.md template=POST_HTML_SINGLE" in log


def test_new_post_link(tmp_path, home):
    git = {"git": True, "git_server": "https://github.com/", "git_user": "me", "git_repo": "kb", "git_branch": "main",
           "git_path": "source"}
    target = _build(tmp_path, home, {"a.md": page("A", Category="Post", Date="2026-01-01")}, **git)
    assert 'href="https://github.com/me/kb/new/main/source"' in _html(target, "a.html")


def test_date_property_is_not_a_link(tmp_path, home):
    """Date keys have no page, so the properties table shows the key name without a link."""
    target = _build(tmp_path, home, {"a.md": page("A", Category="Post", Date="2026-01-01")})
    html = _html(target, "a.html")
    assert 'href="Date.html"' not in html
    assert 'href="Category.html"' in html
