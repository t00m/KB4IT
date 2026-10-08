"""Per-repository overrides: templates looked up before the theme's, static files copied to the site."""

import json

from tests.helpers import page, run_kb4it, write_repo


def _repo(tmp_path, **conf):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="y")}, **conf)
    return cfg, tmp_path / "repo"


def test_template_override_reaches_every_page_and_can_be_removed(tmp_path, home):
    cfg, repo = _repo(tmp_path)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    override = repo / "overrides" / "templates" / "HTML_FOOTER.tpl"
    override.parent.mkdir(parents=True)
    override.write_text("<footer id='my-footer'>Ours</footer>\n", encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "TEMPLATE_OVERRIDE name=HTML_FOOTER" in result.stdout
    assert "CORE_SIGNATURE_CHANGED" in result.stdout
    for name in ("a.html", "b.html", "index.html"):
        assert "my-footer" in (repo / "target" / name).read_text(encoding="utf-8"), name
    override.unlink()
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "my-footer" not in (repo / "target" / "a.html").read_text(encoding="utf-8")


def test_static_files_and_custom_folder(tmp_path, home):
    cfg, repo = _repo(tmp_path, overrides="custom")
    static = repo / "custom" / "static" / "css"
    static.mkdir(parents=True)
    (static / "site.css").write_text("body{}", encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert (repo / "target" / "css" / "site.css").read_text(encoding="utf-8") == "body{}"


def test_override_can_supply_a_required_template(tmp_path, home):
    from tests.helpers import mini_theme
    theme = mini_theme(tmp_path / "mini")
    body = (theme / "templates" / "HTML_BODY.tpl").read_text(encoding="utf-8")
    (theme / "templates" / "HTML_BODY.tpl").unlink()
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 1
    override = tmp_path / "repo" / "overrides" / "templates" / "HTML_BODY.tpl"
    override.parent.mkdir(parents=True)
    override.write_text(body, encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert json.loads((tmp_path / "repo" / "target" / "documents.json").read_text(encoding="utf-8"))
