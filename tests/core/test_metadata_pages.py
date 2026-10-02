from tests.helpers import mini_theme, page, run_kb4it, write_repo


def _build(tmp_path, home, theme):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01", Tag="alpha")},
                     theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    return repo / "target"


def test_metadata_pages_are_built_by_default(tmp_path, home):
    target = _build(tmp_path, home, mini_theme(tmp_path / "mini"))
    assert (target / "Tag.html").exists()
    assert (target / "Tag_alpha.html").exists()


def test_theme_can_turn_off_metadata_pages(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", metadata_pages=False)
    (theme / "templates" / "PAGE_KEY.tpl").unlink()
    (theme / "templates" / "PAGE_KEY_VALUE.tpl").unlink()
    target = _build(tmp_path, home, theme)
    assert (target / "a.html").exists()
    assert not (target / "Tag.html").exists()
    assert not (target / "Tag_alpha.html").exists()
