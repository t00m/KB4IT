import json

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_mini_theme_builds(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert '<meta name="docs" content="1">' in (repo / "target" / "a.html").read_text(encoding="utf-8")
    assert json.loads((repo / "target" / "documents.json").read_text()) == ["a.md"]
