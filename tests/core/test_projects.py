"""The project list in projects.json: ids, add, update, remove and resolve."""

import json
import os

import pytest

from kb4it.core import projects
from kb4it.core.projects import ProjectError


@pytest.fixture(autouse=True)
def registry(tmp_path, monkeypatch):
    path = tmp_path / "projects.json"
    monkeypatch.setattr(projects, "PROJECTS_FILE", path)
    return path


def make_repo(base, title="Test", source="source"):
    (base / "config").mkdir(parents=True)
    (base / "source").mkdir()
    conf = {"theme": "techdoc", "source": source, "target": "target"}
    if title is not None:
        conf["title"] = title
    config = base / "config" / "repo.json"
    config.write_text(json.dumps(conf), encoding="utf-8")
    return str(config)


@pytest.mark.parametrize("pid", ["sapblog", "a", "a-1", "a" * 32])
def test_valid_ids(pid):
    assert projects.id_problem(pid, []) is None


@pytest.mark.parametrize("pid", ["Sap", "1abc", "-a", "a.b", "a/b", "", "a" * 33])
def test_invalid_ids(pid):
    assert projects.id_problem(pid, [])


def test_id_taken_and_own_id():
    ps = [{"id": "x", "name": "X", "config": "/a/config/repo.json"}]
    assert projects.id_problem("x", ps)
    assert projects.id_problem("x", ps, "/a/config/repo.json") is None


def test_register_adds_then_updates(tmp_path):
    config = make_repo(tmp_path / "kb")
    entry, changes = projects.register(config)
    assert changes == ["added"]
    assert entry["config"] == os.path.realpath(config)
    entry, changes = projects.register(config, pid="kb1")
    assert changes == ["id"]
    assert entry["id"] == "kb1"
    assert len(projects.load()) == 1


def test_register_new_with_id(tmp_path):
    _entry, changes = projects.register(make_repo(tmp_path / "kb"), pid="kb1")
    assert changes == ["added", "id"]


def test_register_dedups_by_realpath(tmp_path):
    config = make_repo(tmp_path / "kb")
    (tmp_path / "link").symlink_to(tmp_path / "kb")
    projects.register(config)
    _entry, changes = projects.register(str(tmp_path / "link" / "config" / "repo.json"))
    assert changes == []
    assert len(projects.load()) == 1


def test_register_rejects_taken_id(tmp_path):
    projects.register(make_repo(tmp_path / "a"), pid="kb1")
    with pytest.raises(ProjectError):
        projects.register(make_repo(tmp_path / "b"), pid="kb1")
    assert len(projects.load()) == 1


def test_name_defaults(tmp_path):
    entry, _ = projects.register(make_repo(tmp_path / "a", title="My KB"))
    assert entry["name"] == "My KB"
    entry, _ = projects.register(make_repo(tmp_path / "folder", title=None))
    assert entry["name"] == "folder"
    entry, changes = projects.register(make_repo(tmp_path / "c"), name="Given")
    assert entry["name"] == "Given"


def test_legacy_entries_without_id(registry, tmp_path):
    config = make_repo(tmp_path / "kb")
    registry.write_text(json.dumps({"projects": [{"name": "Old", "config": config}]}), encoding="utf-8")
    assert projects.load() == [{"name": "Old", "config": config}]
    assert projects.find(config)["name"] == "Old"


def test_find_by_id(tmp_path):
    projects.register(make_repo(tmp_path / "kb"), pid="kb1")
    assert projects.find("kb1")["id"] == "kb1"
    assert projects.find("nosuch") is None


def test_set_id_removes_with_empty(tmp_path):
    config = make_repo(tmp_path / "kb")
    projects.register(config, pid="kb1")
    assert projects.set_id(config, "kb2")["id"] == "kb2"
    assert "id" not in projects.set_id(config, "")
    assert "id" not in projects.load()[0]


def test_set_id_rejects_bad_id(tmp_path):
    config = make_repo(tmp_path / "kb")
    projects.register(config)
    with pytest.raises(ProjectError):
        projects.set_id(config, "Bad")


def test_remove(tmp_path):
    config = make_repo(tmp_path / "kb")
    projects.register(config, pid="kb1")
    assert projects.remove(config)["id"] == "kb1"
    assert projects.load() == []
    assert projects.remove(config) is None


def test_corrupt_file_is_quarantined(registry):
    registry.write_text("{bad", encoding="utf-8")
    assert projects.load() == []
    assert list(registry.parent.glob("projects.json.corrupt-*"))


def test_resolve_prefers_an_existing_file(tmp_path, monkeypatch):
    config = make_repo(tmp_path / "kb")
    projects.register(make_repo(tmp_path / "other"), pid="config")
    monkeypatch.chdir(tmp_path / "kb")
    assert projects.resolve("config/repo.json") == "config/repo.json"


def test_resolve_by_id(tmp_path):
    config = make_repo(tmp_path / "kb")
    projects.register(config, pid="kb1")
    assert projects.resolve("kb1") == os.path.realpath(config)


def test_resolve_unknown():
    with pytest.raises(ProjectError) as error:
        projects.resolve("nosuch")
    assert str(error.value) == ("No project with id 'nosuch' and no file 'nosuch'. "
                                "Run 'kb4it projects' to see the ids.")


def test_resolve_missing_config(tmp_path):
    config = make_repo(tmp_path / "kb")
    projects.register(config, pid="kb1")
    os.remove(config)
    with pytest.raises(ProjectError) as error:
        projects.resolve("kb1")
    assert os.path.realpath(config) in str(error.value)


def test_root_and_source_dir(tmp_path):
    config = make_repo(tmp_path / "kb")
    assert projects.root_of(config) == (tmp_path / "kb").resolve()
    assert projects.source_dir(config) == (tmp_path / "kb").resolve() / "source"
    absolute = make_repo(tmp_path / "abs", source=str(tmp_path / "elsewhere"))
    assert projects.source_dir(absolute) == tmp_path / "elsewhere"


def test_resolve_passes_through_a_missing_path():
    # Not an id and not a file: the build reports CONFIG_MISSING as before.
    assert projects.resolve("/x/nope/repo.json") == "/x/nope/repo.json"
