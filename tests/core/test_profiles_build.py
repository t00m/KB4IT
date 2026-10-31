"""Profiles of any key in a build: Team profiles, the PERSON- and people fallbacks, links and rebuilds."""

import json
import re

from tests.helpers import page, run_kb4it, write_repo


def _build(tmp_path, home, pages, *args, **config):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", pages, **config)
    result = run_kb4it(*args, "build", cfg, cwd=tmp_path, home=home)
    return repo, cfg, result


def test_team_profile_builds_and_is_recorded(tmp_path, home):
    pages = {"a.md": page("A", Team="SAP Basis", Tag="x"),
             "PROFILE-SAP-BASIS.md": page("SAP Basis", ProfileOf="Team", Lead="Jane Doe")}
    repo, _, result = _build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    kbdict = json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))
    assert kbdict["profiles"]["PROFILE-SAP-BASIS.md"]["keys"] == ["Team"]
    assert not (repo / "target" / "PROFILE-SAP-BASIS.html").exists()


def test_profile_without_profileof_is_left_out(tmp_path, home):
    _, _, result = _build(tmp_path, home, {"a.md": page("A", Tag="x"), "PROFILE-X.md": page("X", Role="r")})
    assert "PROFILE_INVALID doc=PROFILE-X.md detail=ProfileOf is missing" in result.stdout


def test_person_prefix_warns_and_still_works(tmp_path, home):
    repo, _, result = _build(tmp_path, home, {"a.md": page("A", Author="Jane Doe", Tag="x"),
                                              "PERSON-JANE.md": page("Jane Doe", Email="j@example.org")})
    assert result.returncode == 0 and "PROFILE_PERSON_PREFIX doc=PERSON-JANE.md" in result.stdout
    assert "j@example.org" in (repo / "target" / "Author_Jane_Doe.html").read_text(encoding="utf-8")


def test_link_to_a_team_profile_leads_to_the_team_page(tmp_path, home):
    pages = {"a.md": page("A", Team="SAP Basis", Tag="x", body="See [team](PROFILE-SAP-BASIS.md)."),
             "PROFILE-SAP-BASIS.md": page("SAP Basis", ProfileOf="Team")}
    repo, _, result = _build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "a.html").read_text(encoding="utf-8")
    assert re.search(r'href="Team_SAP_Basis\.html"[^>]*>team</a>', html), re.findall(r'<a [^>]*>team</a>', html)


def test_changed_team_profile_rebuilds_the_team_page(tmp_path, home):
    pages = {"a.md": page("A", Team="SAP Basis", Tag="x"),
             "PROFILE-SAP-BASIS.md": page("SAP Basis", ProfileOf="Team", Alias="Basis")}
    repo, cfg, result = _build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    (repo / "source" / "PROFILE-SAP-BASIS.md").write_text(
        page("SAP Basis", body="New text.", ProfileOf="Team", Alias="Basis"), encoding="utf-8")
    out = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home).stdout
    assert "[PROCESSOR] KV key=Team value=SAP Basis compile=True" in out


def test_people_block_is_reported(tmp_path, home):
    _, _, result = _build(tmp_path, home, {"a.md": page("A", Tag="x")}, people={"keys": ["Author"]})
    assert "PEOPLE_BLOCK_DEPRECATED" in result.stdout


def test_profiles_block_drives_the_people_keys(tmp_path, home):
    pages = {"a.md": page("A", Owner="Jane Doe", Tag="x"),
             "PROFILE-JANE.md": page("Jane Doe", ProfileOf="Owner", Email="j@example.org")}
    repo, _, result = _build(tmp_path, home, pages, profiles={"Owner": {"type": "Person", "contact_keys": ["Email"]}})
    assert result.returncode == 0, result.stdout
    assert "j@example.org" in (repo / "target" / "Owner_Jane_Doe.html").read_text(encoding="utf-8")


def test_profileof_naming_an_unused_key_warns(tmp_path, home):
    # ProfileOf holds the person's name instead of the key: the profile would describe a key nobody uses.
    pages = {"a.md": page("A", Author="Jane Doe", Tag="x"),
             "PROFILE-JANE.md": page("Jane Doe", ProfileOf="Jane Doe", Email="j@example.org")}
    _, _, result = _build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    assert "PROFILE_KEY_UNUSED doc=PROFILE-JANE.md key=Jane Doe" in result.stdout


def test_profileof_naming_a_used_or_configured_key_does_not_warn(tmp_path, home):
    pages = {"a.md": page("A", Team="SAP Basis", Tag="x"),
             "PROFILE-SAP-BASIS.md": page("SAP Basis", ProfileOf="Team"),
             "PROFILE-JANE.md": page("Jane Doe", ProfileOf="Author", Email="j@example.org")}
    _, _, result = _build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    assert "PROFILE_KEY_UNUSED" not in result.stdout
