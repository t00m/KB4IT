"""Template output is escaped for themes that opt in, and always in KB4IT's common templates (SC-01)."""

from tests.helpers import mini_theme, page, run_kb4it, write_repo

HOSTILE = '"><script>alert(1)</script>'


def _site(tmp_path, **theme_json):
    theme = mini_theme(tmp_path / "mini", **theme_json)
    body = "Some <b>bold</b> HTML from Markdown."
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page(f"A {HOSTILE}", body, Tag="x")},
                     theme_path=str(theme), site_url="https://example.org/kb/", description=HOSTILE)
    return cfg, tmp_path / "repo" / "target"


def test_theme_without_the_flag_warns_once_and_prints_as_before(tmp_path, home):
    cfg, target = _site(tmp_path)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert result.stdout.count("THEME_AUTOESCAPE_OFF theme=mini") == 1
    html = (target / "a.html").read_text(encoding="utf-8")
    assert "<b>bold</b>" in html  # the theme's ${var['body']} is still raw


def test_common_templates_escape_hostile_values(tmp_path, home):
    cfg, target = _site(tmp_path)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    html = (target / "a.html").read_text(encoding="utf-8")
    head = html[html.find("<head>"):html.find("</head>")]
    assert "<script>alert(1)</script>" not in head
    assert "&lt;script&gt;" in head


def test_theme_with_the_flag_escapes_and_does_not_warn(tmp_path, home):
    cfg, target = _site(tmp_path, autoescape=True)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "THEME_AUTOESCAPE_OFF" not in result.stdout
    # mini prints the page body with a plain ${...}: now it shows as text.
    assert "&lt;b&gt;bold&lt;/b&gt;" in (target / "a.html").read_text(encoding="utf-8")


def test_raw_marker_prints_html(tmp_path, home):
    cfg, target = _site(tmp_path, autoescape=True)
    body = tmp_path / "mini" / "templates" / "HTML_BODY.tpl"
    body.write_text(body.read_text(encoding="utf-8").replace("${var['body']}", "${var['body'] | n}"),
                    encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "<b>bold</b>" in (target / "a.html").read_text(encoding="utf-8")
