"""techdoc settings from TechdocConfig: theme.json, then the "techdoc" block of repo.json (P5)."""

from tests.core.test_highlight import _app_conf
from tests.helpers import mini_theme, page, run_kb4it, write_repo

FOUR = "## One\n\nA.\n\n## Two\n\nB.\n\n## Three\n\nC.\n\n## Four\n\nD."
DOCS = {"four.md": page("Four sections", FOUR, Category="Note", Date="2026-10-01")}


def _repo(tmp_path, block):
    conf = _app_conf("techdoc")
    conf["techdoc"] = block
    return write_repo(tmp_path / "repo", "techdoc", DOCS, **conf)


def test_techdoc_repo_block_toc_sidebar(tmp_path, home):
    cfg = _repo(tmp_path, {"toc_sidebar": True})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "repo" / "target" / "four.html").read_text(encoding="utf-8")
    assert '<aside class="kb-toc-sidebar' in html
    assert "THEME_SETTING_UNKNOWN" not in result.stdout


def test_wrong_type_stops_the_build_and_names_the_key(tmp_path, home):
    cfg = _repo(tmp_path, {"toc_sidebar": "yes"})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode != 0
    assert "toc_sidebar" in result.stdout


def test_unknown_key_is_logged_and_fails_verify(tmp_path, home):
    cfg = _repo(tmp_path, {"tocsidebar": True})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "[FRONTEND] THEME_SETTING_UNKNOWN theme=techdoc key=tocsidebar" in result.stdout
    verify = run_kb4it("verify", cfg, cwd=tmp_path / "repo", home=home)
    assert verify.returncode == 1, verify.stdout
    assert "THEME_SETTING_UNKNOWN theme=techdoc key=tocsidebar" in verify.stdout


def test_theme_without_config_class_gets_plain_settings(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme),
                     mini={"anything": 1})
    result = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "[FRONTEND] THEME_SETTINGS id=mini class=ThemeSettings" in result.stdout
    assert "THEME_SETTING_UNKNOWN" not in result.stdout, "a theme without config_class checks no block"
