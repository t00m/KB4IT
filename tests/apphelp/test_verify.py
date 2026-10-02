from tests.helpers import page, run_kb4it, write_repo


def test_verify_lists_metadata_problems(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "apphelp", {
        "a.md": page("A", Kind="howto", Section="S", Order="1", Feature="Backup"),
    }, apphelp={"vocabulary": {"Feature": ["Backup"]}})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert "META_MISSING doc=a.md key=Summary" in result.stdout


def test_verify_fails_on_invalid_frontmatter(tmp_path, home):
    repo = tmp_path / "repo"
    broken = "---\nFeature: Backup\nKind: howto\nOrder: 1\nSection: S\nSummary: Broken: colon.\n---\n\n# B\n"
    cfg = write_repo(repo, "apphelp", {"broken.md": broken}, apphelp={"vocabulary": {"Feature": ["Backup"]}})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert result.returncode == 1, result.stdout
    assert "broken.md" in result.stdout
