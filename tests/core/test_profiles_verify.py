"""kb4it verify: profile migration notices, profiles of any key, values without a profile."""

from tests.helpers import page, run_kb4it, write_repo


def test_verify_reports_profile_migration_and_missing_values(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {
        "a.md": page("A", Author="Jane Doe", Team="SAP Basis", Tag="x"),
        "PERSON-JANE.md": page("Jane Doe", Email="j@example.org"),
        "PROFILE-NET.md": page("Network", ProfileOf="Team")},
        profiles={"Author": {"type": "Person", "contact_keys": ["Email"], "missing": "penalty"},
                  "Team": {"type": "Organization", "missing": "notice"}})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert "PROFILE_PERSON_PREFIX doc=PERSON-JANE.md" in result.stdout
    assert "VALUE_NO_PROFILE key=Team value=SAP Basis docs=1" in result.stdout
    assert "PROFILE_UNUSED person=Network doc=PROFILE-NET.md" in result.stdout


def test_verify_fails_on_a_profile_without_profileof(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x"), "PROFILE-X.md": page("X", Role="r")})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert result.returncode != 0 and "PROFILE_INVALID doc=PROFILE-X.md" in result.stdout


def test_verify_reports_the_people_block(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x")}, people={"keys": ["Author"]})
    assert "PEOPLE_BLOCK_DEPRECATED" in run_kb4it("verify", cfg, cwd=repo, home=home).stdout


def test_verify_refuses_a_date_key_as_profile_target(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x"), "PROFILE-D.md": page("D", ProfileOf="DueDate")})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert "PROFILE_INVALID doc=PROFILE-D.md detail=ProfileOf names DueDate" in result.stdout
