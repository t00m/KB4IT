"""kb4it import and kb4it delete."""

import json
import os

import pytest

from kb4it.core import projects
from kb4it.core.env import ENV
from kb4it.core.lock import FileLock, repo_lock_path
from kb4it.core.projectcli import run_delete
from tests.helpers import page, run_kb4it, write_repo


def registry(home):
    path = home / ".kb4it" / "projects.json"
    return json.loads(path.read_text(encoding="utf-8"))["projects"] if path.exists() else []


def repo(tmp_path, name="kb", **config):
    config.setdefault("title", "My KB")
    return write_repo(tmp_path / name, "techdoc", {"a.md": page("A", Tag="x")}, **config)


def test_import_new(tmp_path, home):
    config = repo(tmp_path)
    result = run_kb4it("import", config, "--id", "kb1", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert f"Imported kb1: My KB ({config})" in result.stdout
    assert registry(home) == [{"id": "kb1", "name": "My KB", "config": str(config)}]


def test_import_again_sets_id(tmp_path, home):
    config = repo(tmp_path)
    run_kb4it("import", config, cwd=tmp_path, home=home)
    result = run_kb4it("import", config, "--id", "kb1", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "Updated kb1: id" in result.stdout
    assert [p.get("id") for p in registry(home)] == ["kb1"]


def test_import_again_without_changes(tmp_path, home):
    config = repo(tmp_path)
    run_kb4it("import", config, "--id", "kb1", cwd=tmp_path, home=home)
    result = run_kb4it("import", config, cwd=tmp_path, home=home)
    assert result.returncode == 0
    assert "Already in the list as kb1" in result.stdout
    assert len(registry(home)) == 1


def test_import_name_override(tmp_path, home):
    config = repo(tmp_path)
    run_kb4it("import", config, "--name", "Ops notes", cwd=tmp_path, home=home)
    assert registry(home)[0]["name"] == "Ops notes"


def test_import_taken_id_exits_1(tmp_path, home):
    run_kb4it("import", repo(tmp_path, "a"), "--id", "kb1", cwd=tmp_path, home=home)
    result = run_kb4it("import", repo(tmp_path, "b"), "--id", "kb1", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "already used" in result.stdout
    assert len(registry(home)) == 1


def test_import_invalid_config_exits_1(tmp_path, home):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = run_kb4it("import", bad, cwd=tmp_path, home=home)
    assert result.returncode == 1
    result = run_kb4it("import", tmp_path / "missing.json", cwd=tmp_path, home=home)
    assert result.returncode == 1
    nottheme = tmp_path / "other.json"
    nottheme.write_text("{}", encoding="utf-8")
    assert run_kb4it("import", nottheme, cwd=tmp_path, home=home).returncode == 1
    assert registry(home) == []


# kb4it delete, called in-process so the confirmation can be answered.


@pytest.fixture
def listing(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_FILE", tmp_path / "projects.json")
    kb4it_home = tmp_path / "kb4it-home"
    kb4it_home.mkdir()
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(kb4it_home))
    return tmp_path


def delete(ref, files=False, yes=False, answer=None, interactive=False):
    return run_delete({"project": ref, "files": files, "yes": yes},
                      ask=lambda _prompt: answer, interactive=interactive)


def test_delete_keeps_files(listing, capsys):
    config = repo(listing)
    projects.register(config, pid="kb1")
    assert delete("kb1") == 0
    assert projects.load() == []
    assert config.exists()
    assert "files kept in" in capsys.readouterr().out


def test_delete_by_config_path(listing):
    config = repo(listing)
    projects.register(config)
    assert delete(str(config)) == 0
    assert projects.load() == []


def test_delete_unlisted_exits_1(listing, capsys):
    config = repo(listing)
    assert delete(str(config)) == 1
    assert "Not in the list" in capsys.readouterr().err
    assert delete("nosuch") == 1


def test_delete_files_after_typing_the_id(listing):
    config = repo(listing)
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, answer="kb1", interactive=True) == 0
    assert not (listing / "kb").exists()
    assert projects.load() == []


def test_delete_files_wrong_answer_cancels(listing):
    config = repo(listing)
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, answer="kb", interactive=True) == 1
    assert config.exists()
    assert len(projects.load()) == 1


def test_delete_files_without_tty_needs_yes(listing, capsys):
    config = repo(listing)
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True) == 1
    assert "--yes" in capsys.readouterr().err
    assert config.exists()
    assert delete("kb1", files=True, yes=True) == 0
    assert not (listing / "kb").exists()


def test_delete_files_legacy_entry_asks_folder_name(listing):
    config = repo(listing, "oldkb")
    projects.register(config)
    assert delete(str(config), files=True, answer="oldkb", interactive=True) == 0
    assert not (listing / "oldkb").exists()


def test_delete_refuses_without_config_folder(listing, capsys):
    base = listing / "loose"
    base.mkdir()
    config = base / "repo.json"
    config.write_text(json.dumps({"theme": "techdoc"}), encoding="utf-8")
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, yes=True) == 1
    assert config.exists()
    assert len(projects.load()) == 1


def test_delete_refuses_home_folder(listing, monkeypatch):
    home = listing / "user"
    config = write_repo(home, "techdoc", {"a.md": page("A", Tag="x")})
    monkeypatch.setenv("HOME", str(home))
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, yes=True) == 1
    assert config.exists()


def test_delete_refuses_kb4it_home_and_parents(listing):
    kb4it_home = listing / "kb4it-home"
    config = write_repo(kb4it_home, "techdoc", {"a.md": page("A", Tag="x")})
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, yes=True) == 1
    assert config.exists()
    # A project folder that contains KB4IT_HOME is refused too.
    outer = write_repo(listing, "techdoc", {"a.md": page("A", Tag="x")})
    projects.register(outer, pid="kb2")
    assert delete("kb2", files=True, yes=True) == 1
    assert kb4it_home.exists()


def test_delete_refuses_while_locked(listing, capsys):
    config = repo(listing)
    projects.register(config, pid="kb1")
    lock = FileLock(repo_lock_path(config)).acquire()
    try:
        assert delete("kb1", files=True, yes=True) == 1
    finally:
        lock.release()
    assert str(os.getpid()) in capsys.readouterr().err
    assert config.exists()


def test_delete_keeps_outside_target_and_prints_it(listing, capsys):
    target = listing / "site"
    target.mkdir()
    config = repo(listing, target=str(target))
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, yes=True) == 0
    assert target.exists()
    assert str(target) in capsys.readouterr().out


def test_delete_failure_keeps_entry(listing, monkeypatch):
    config = repo(listing)
    projects.register(config, pid="kb1")

    def broken(_path):
        raise OSError("disk says no")
    monkeypatch.setattr("kb4it.core.projectcli.shutil.rmtree", broken)
    assert delete("kb1", files=True, yes=True) == 1
    assert len(projects.load()) == 1


def test_delete_from_the_command_line(tmp_path, home):
    config = repo(tmp_path)
    run_kb4it("import", config, "--id", "kb1", cwd=tmp_path, home=home)
    result = run_kb4it("delete", "kb1", "--files", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert config.exists()
    result = run_kb4it("delete", "kb1", "--files", "--yes", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert not config.exists()
    assert registry(home) == []


def test_delete_refuses_a_symlinked_config(listing):
    real = repo(listing, "elsewhere")
    (listing / "other" / "config").mkdir(parents=True)
    link = listing / "other" / "config" / "repo.json"
    link.symlink_to(real)
    projects.register(link, pid="sym")
    assert delete("sym", files=True, yes=True) == 1
    assert real.exists()
    assert link.exists()


def test_delete_stale_entry_by_path(listing):
    config = repo(listing)
    projects.register(config)
    import shutil
    shutil.rmtree(listing / "kb")
    assert delete(str(config)) == 0
    assert projects.load() == []


def test_delete_refuses_when_a_build_starts_during_the_prompt(listing):
    config = repo(listing)
    projects.register(config, pid="kb1")
    other = FileLock(repo_lock_path(config))

    def answer_while_a_build_starts(_prompt):
        other.acquire()
        return "kb1"
    try:
        status = run_delete({"project": "kb1", "files": True, "yes": False},
                            ask=answer_while_a_build_starts, interactive=True)
    finally:
        other.release()
    assert status == 1
    assert config.exists()
    assert len(projects.load()) == 1


def test_delete_cancelled_leaves_no_lock_file(listing):
    config = repo(listing)
    projects.register(config, pid="kb1")
    assert delete("kb1", files=True, answer="no", interactive=True) == 1
    assert not (listing / "kb" / "var").exists()
