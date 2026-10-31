"""kb4it verify reports date notices as warnings and information, and never fails on them."""

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_verify_reports_date_problems_without_failing(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {
        "a.md": page("A", Date="02/11/2026"),
        "b.md": page("B", Start="2026-11-02", End="2026-11-01"),
        "c.md": page("C", Date="2026-11-02", Downtime="Yes")},
        theme_path=str(mini_theme(tmp_path / "mini")))
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "Dates (warnings):" in result.stdout
    assert "DATE_END_BEFORE_START doc=b.md" in result.stdout
    assert "DATE_DOWNTIME_MISSING doc=c.md" in result.stdout
    assert "Dates (information):" in result.stdout
    assert "DATE_NOT_STANDARD doc=a.md" in result.stdout
    assert "TIMEZONE_UNSET" in result.stdout


def test_verify_config_problems_are_warnings(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-11-02")},
                     theme_path=str(mini_theme(tmp_path / "mini")), timezone="Mars/Base",
                     dates={"Date": {"group": "start"}})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "TIMEZONE_INVALID value=Mars/Base" in result.stdout
    assert "DATES_BLOCK_INVALID key=Date reason=reserved" in result.stdout
