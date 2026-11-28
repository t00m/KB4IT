"""Project ids as shortcuts for config paths, the projects listing and create --id."""

import json

from kb4it.core.projects import format_projects
from tests.helpers import page, run_kb4it, write_repo


def listed(home, *entries):
    (home / ".kb4it").mkdir(exist_ok=True)
    (home / ".kb4it" / "projects.json").write_text(json.dumps({"projects": list(entries)}), encoding="utf-8")


def repo(tmp_path, name="kb", title="My KB"):
    return write_repo(tmp_path / name, "techdoc", {"a.md": page("A", Tag="x")}, title=title)


def test_info_by_id(tmp_path, home):
    config = repo(tmp_path)
    listed(home, {"id": "kb1", "name": "My KB", "config": str(config)})
    result = run_kb4it("info", "kb1", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "My KB" in result.stdout


def test_relative_path_still_works(tmp_path, home):
    config = repo(tmp_path)
    other = repo(tmp_path, "other", title="Other KB")
    listed(home, {"id": "config", "name": "Other KB", "config": str(other)})
    result = run_kb4it("info", "config/repo.json", cwd=config.parent.parent, home=home)
    assert result.returncode == 0, result.stdout
    assert "My KB" in result.stdout
    assert "Other KB" not in result.stdout


def test_unknown_reference(tmp_path, home):
    result = run_kb4it("info", "nosuch", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert ("No project with id 'nosuch' and no file 'nosuch'. "
            "Run 'kb4it projects' to see the ids.") in result.stdout


def test_missing_config_of_listed_id(tmp_path, home):
    missing = tmp_path / "gone" / "config" / "repo.json"
    listed(home, {"id": "kb1", "name": "Gone", "config": str(missing)})
    result = run_kb4it("build", "kb1", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert str(missing) in result.stdout


def test_projects_table_shows_ids():
    lines = format_projects([{"id": "kb1", "name": "First", "config": "/a/config/repo.json"},
                             {"name": "Legacy", "config": "/b/config/repo.json"}], table=True)
    assert lines[0].split() == ["ID", "Name", "Config"]
    legacy = next(line for line in lines if "Legacy" in line)
    assert legacy.split()[0] == "-"
    assert lines[2].index("First") == lines[3].index("Legacy")


def test_projects_tab_separated_when_piped(tmp_path, home):
    listed(home, {"id": "kb1", "name": "First KB", "config": "/a/config/repo.json"},
           {"name": "Legacy", "config": "/b/config/repo.json"})
    result = run_kb4it("projects", cwd=tmp_path, home=home, split_streams=True)
    assert result.stdout.splitlines() == ["kb1\tFirst KB\t/a/config/repo.json", "\tLegacy\t/b/config/repo.json"]


def test_create_with_id(tmp_path, home):
    result = run_kb4it("create", "techdoc", "default", "newkb", "--id", "kb2", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "kb4it serve kb2" in result.stdout
    data = json.loads((home / ".kb4it" / "projects.json").read_text(encoding="utf-8"))
    assert data["projects"][0]["id"] == "kb2"


def test_create_with_bad_or_taken_id_leaves_no_folder(tmp_path, home):
    result = run_kb4it("create", "techdoc", "default", "bad", "--id", "Bad", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert not (tmp_path / "bad").exists()
    listed(home, {"id": "kb1", "name": "First", "config": str(repo(tmp_path))})
    result = run_kb4it("create", "techdoc", "default", "taken", "--id", "kb1", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "already used" in result.stdout
    assert not (tmp_path / "taken").exists()
