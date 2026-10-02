from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_verify_runs_theme_hook(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    (theme / "logic" / "verify.py").write_text(
        "def verify(repo, docs):\n    return [f'{name}: checked' for name in sorted(docs)]\n")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert "a.md: checked" in result.stdout
