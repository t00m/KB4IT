from tests.helpers import mini_theme, page, run_kb4it, write_repo

GENERATED = "---\nSystemPage: Yes\n---\n# About KB4IT\n\nold build\n"
EDITED = "---\nSystemPage: Yes\n---\n# About our KB4IT setup\n\nKeep me.\n"


def _build(tmp_path, home, pages):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", pages, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    return repo


def test_build_leaves_source_untouched(tmp_path, home):
    repo = _build(tmp_path, home, {"a.md": page("A", Date="2026-01-01")})
    assert sorted(p.name for p in (repo / "source").iterdir()) == ["a.md"]
    assert (repo / "target" / "about_kb4it.html").exists()
    assert (repo / "target" / "about_app.html").exists()


def test_generated_about_kb4it_is_removed(tmp_path, home):
    repo = _build(tmp_path, home, {"a.md": page("A", Date="2026-01-01"), "about_kb4it.md": GENERATED})
    assert not (repo / "source" / "about_kb4it.md").exists()


def test_edited_about_kb4it_is_kept(tmp_path, home):
    repo = _build(tmp_path, home, {"a.md": page("A", Date="2026-01-01"), "about_kb4it.md": EDITED})
    assert (repo / "source" / "about_kb4it.md").read_text() == EDITED


def test_user_about_app_wins(tmp_path, home):
    mine = "---\nSystemPage: Yes\n---\n# About Foo\n\nFoo is great.\n"
    repo = _build(tmp_path, home, {"a.md": page("A", Date="2026-01-01"), "about_app.md": mine})
    assert "Foo is great." in (repo / "target" / "about_app.html").read_text()


def test_about_headings_are_rendered(tmp_path, home):
    repo = _build(tmp_path, home, {"a.md": page("A", Date="2026-01-01")})
    app = (repo / "target" / "about_app.html").read_text()
    assert "Page not found" in app
    assert "How to replace it" in app
    assert "Description" in (repo / "target" / "about_kb4it.html").read_text()
