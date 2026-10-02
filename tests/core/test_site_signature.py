import pytest

from tests.helpers import mini_theme, page, run_kb4it, write_repo


@pytest.mark.parametrize("flag, expected", [(True, "3"), (False, "2")])
def test_signature_change_rebuilds_unchanged_pages(tmp_path, home, flag, expected):
    theme = mini_theme(tmp_path / "mini", test_signature=flag)
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {
        "a.md": page("A", Date="2026-01-01"),
        "b.md": page("B", Date="2026-01-02"),
    }, theme_path=str(theme))
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    (repo / "source" / "c.md").write_text(page("C", Date="2026-01-03"))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "a.html").read_text()
    assert f'<meta name="docs" content="{expected}">' in html
