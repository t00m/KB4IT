"""The deployer deletes only the pages KB4IT wrote into the target (FS-01)."""

import json

from tests.helpers import page, run_kb4it, write_repo


def _build(cfg, tmp_path, home, *extra):
    result = run_kb4it("build", cfg, *extra, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return result


def _site(tmp_path):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="x")})
    return cfg, repo, repo / "target"


def test_user_page_survives_and_deleted_document_page_goes(tmp_path, home):
    cfg, repo, target = _site(tmp_path)
    _build(cfg, tmp_path, home)
    (target / "notes.html").write_text("mine", encoding="utf-8")
    (repo / "source" / "b.md").unlink()
    _build(cfg, tmp_path, home)
    assert (target / "notes.html").read_text(encoding="utf-8") == "mine"
    assert (target / "a.html").is_file()
    assert not (target / "b.html").exists()


def test_forced_build_still_sweeps_deleted_pages(tmp_path, home):
    cfg, repo, target = _site(tmp_path)
    _build(cfg, tmp_path, home)
    (target / "notes.html").write_text("mine", encoding="utf-8")
    (repo / "source" / "b.md").unlink()
    _build(cfg, tmp_path, home, "--force")
    assert not (target / "b.html").exists()
    assert (target / "notes.html").is_file()


def test_first_build_after_upgrade_deletes_nothing(tmp_path, home):
    cfg, repo, target = _site(tmp_path)
    _build(cfg, tmp_path, home)
    kbdict_file = repo / "var" / "db" / "kbdict.json"
    kbdict = json.loads(kbdict_file.read_text(encoding="utf-8"))
    assert "b.html" in kbdict["deployed"]
    del kbdict["deployed"]  # as written by KB4IT 0.8
    kbdict_file.write_text(json.dumps(kbdict), encoding="utf-8")
    (target / "notes.html").write_text("mine", encoding="utf-8")
    (repo / "source" / "b.md").unlink()
    _build(cfg, tmp_path, home)
    assert (target / "notes.html").is_file()
    assert (target / "b.html").is_file()  # unknown owner: kept once, swept from now on
    assert "b.html" not in json.loads(kbdict_file.read_text(encoding="utf-8"))["deployed"]


def test_record_never_reaches_outside_the_target(tmp_path, home):
    cfg, repo, target = _site(tmp_path)
    _build(cfg, tmp_path, home)
    outside = repo / "keep.html"
    outside.write_text("mine", encoding="utf-8")
    kbdict_file = repo / "var" / "db" / "kbdict.json"
    kbdict = json.loads(kbdict_file.read_text(encoding="utf-8"))
    kbdict["deployed"] += ["../keep.html", "notes.txt"]
    kbdict_file.write_text(json.dumps(kbdict), encoding="utf-8")
    (target / "notes.txt").write_text("mine", encoding="utf-8")
    _build(cfg, tmp_path, home)
    assert outside.is_file() and (target / "notes.txt").is_file()
