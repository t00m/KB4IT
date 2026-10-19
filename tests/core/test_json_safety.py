"""JSON files are written atomically, and an unreadable one is kept or rebuilt, never lost (FS-02)."""

import json
import os
from pathlib import Path

import pytest

from kb4it.core import util
from tests.helpers import page, run_kb4it, write_repo


def test_json_save_replaces_the_file_whole(tmp_path):
    path = tmp_path / "data.json"
    util.json_save(str(path), {"a": 1})
    util.json_save(str(path), {"b": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"b": 2}
    assert os.listdir(tmp_path) == ["data.json"]


def test_a_failed_write_leaves_the_old_file(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    util.json_save(str(path), {"old": True})

    def broken_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(util.os, "replace", broken_replace)
    with pytest.raises(OSError):
        util.json_save(str(path), {"new": True})
    assert json.loads(path.read_text(encoding="utf-8")) == {"old": True}
    assert os.listdir(tmp_path) == ["data.json"]


def test_quarantine_keeps_the_content(tmp_path):
    path = tmp_path / "projects.json"
    path.write_text("{broken", encoding="utf-8")
    first = util.quarantine(str(path))
    path.write_text("{again", encoding="utf-8")
    second = util.quarantine(str(path))
    assert first != second and not path.exists()
    assert Path(first).read_text(encoding="utf-8") == "{broken"


def test_truncated_projects_file_is_kept(tmp_path, home):
    """The audit reproduction of COR-04: the registry was replaced with only the new project."""
    registry = home / ".kb4it" / "projects.json"
    registry.parent.mkdir(parents=True)
    whole = json.dumps({"projects": [{"name": "A", "config": "/a/config/repo.json"},
                                     {"name": "B", "config": "/b/config/repo.json"}]})
    registry.write_text(whole[: len(whole) // 2], encoding="utf-8")
    result = run_kb4it("create", "techdoc", tmp_path / "new", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "PROJECTS_CORRUPT" in result.stdout
    kept = [p for p in registry.parent.iterdir() if p.name.startswith("projects.json.corrupt-")]
    assert len(kept) == 1
    assert kept[0].read_text(encoding="utf-8") == whole[: len(whole) // 2]
    assert len(json.loads(registry.read_text(encoding="utf-8"))["projects"]) == 1


def test_truncated_kbdict_gives_a_full_build(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    kbdict = repo / "var" / "db" / "kbdict.json"
    kbdict.write_text(kbdict.read_text(encoding="utf-8")[:40], encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "KBDICT_CORRUPT" in result.stdout
    assert "compiled=1" in result.stdout
    json.loads(kbdict.read_text(encoding="utf-8"))


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_json_save_keeps_the_usual_file_mode(tmp_path):
    path = tmp_path / "data.json"
    umask = os.umask(0o022)
    try:
        util.json_save(str(path), {"a": 1})
        assert path.stat().st_mode & 0o777 == 0o644
        path.chmod(0o600)
        util.json_save(str(path), {"a": 2})
        assert path.stat().st_mode & 0o777 == 0o600
    finally:
        os.umask(umask)
