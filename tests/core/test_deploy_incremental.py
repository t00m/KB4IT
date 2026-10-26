"""The deploy copies only new or changed files and deletes what the repository or the theme no longer has."""

import json
import os

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def _repo(tmp_path, **config):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    pages = {"a.md": page("A", Date="2026-01-01"), "b.md": page("B", Date="2026-01-02"),
             "resources/images/x.png": "png", "resources/images/y.png": "png"}
    cfg = write_repo(repo, "mini", pages, theme_path=str(theme), **config)
    return cfg, repo, theme


def _build(cfg, repo, home, *args):
    result = run_kb4it("-L", "DEBUG", "build", *args, cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    return result


def _stamps(folder):
    return {p: os.stat(p).st_mtime_ns for p in folder.rglob("*") if p.is_file()}


def test_unchanged_build_copies_nothing(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    _build(cfg, repo, home)
    before = _stamps(repo / "target")
    result = _build(cfg, repo, home)
    # The mini theme rebuilds its two "about" pages every time and the build writes documents.json;
    # the documents and every resource stay as they are.
    assert "HTML_TO_TARGET copied=2 unchanged=2 deleted=0" in result.stdout
    assert "COPIED_GLOBAL_RESOURCES copied=0 deleted=0" in result.stdout
    assert "COPIED_HTML_BACK_TO_CACHE copied=0" in result.stdout
    after = _stamps(repo / "target")
    assert after.keys() == before.keys()
    kept = [p for p in before if not p.name.startswith("about_") and p.name != "documents.json"]
    changed = sorted(p.relative_to(repo).as_posix() for p in kept if after[p] != before[p])
    assert len(kept) > 10 and changed == []


def test_changed_document_is_copied(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    _build(cfg, repo, home)
    (repo / "source" / "a.md").write_text(page("A", "New text.", Date="2026-01-01"), encoding="utf-8")
    result = _build(cfg, repo, home)
    assert "New text." in (repo / "target" / "a.html").read_text(encoding="utf-8")
    assert "HTML_TO_TARGET copied=0 " not in result.stdout


def test_removed_repository_resource_is_deleted(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    _build(cfg, repo, home)
    images = repo / "target" / "resources" / "images"
    assert (images / "y.png").exists()
    (repo / "source" / "resources" / "images" / "y.png").unlink()
    result = _build(cfg, repo, home)
    assert not (images / "y.png").exists()
    assert (images / "x.png").exists()
    assert "STALE_STATIC_DELETED file=resources/images/y.png" in result.stdout


def test_removed_resource_is_deleted_after_a_forced_build(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    _build(cfg, repo, home)
    (repo / "source" / "resources" / "images" / "y.png").unlink()
    _build(cfg, repo, home, "--force")
    assert not (repo / "target" / "resources" / "images" / "y.png").exists()


def test_user_files_in_the_target_survive(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    _build(cfg, repo, home)
    mine = repo / "target" / "resources" / "mine.txt"
    mine.write_text("mine", encoding="utf-8")
    page_mine = repo / "target" / "notes.txt"
    page_mine.write_text("notes", encoding="utf-8")
    _build(cfg, repo, home)
    assert mine.exists() and page_mine.exists()


def test_removed_theme_file_is_deleted(tmp_path, home):
    cfg, repo, theme = _repo(tmp_path)
    (theme / "framework" / "extra.css").write_text("x", encoding="utf-8")
    _build(cfg, repo, home)
    deployed = repo / "target" / "resources" / "themes" / "mini" / "framework"
    assert (deployed / "extra.css").exists()
    (theme / "framework" / "extra.css").unlink()
    _build(cfg, repo, home)
    assert not (deployed / "extra.css").exists()
    assert (deployed / "mini.css").exists()


def test_removed_overrides_static_file_is_deleted(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    static = repo / "overrides" / "static"
    static.mkdir(parents=True)
    (static / "CNAME").write_text("example.org", encoding="utf-8")
    _build(cfg, repo, home)
    assert (repo / "target" / "CNAME").exists()
    (static / "CNAME").unlink()
    _build(cfg, repo, home)
    assert not (repo / "target" / "CNAME").exists()


def test_repository_resource_inside_a_mirrored_folder_is_not_churned(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    (repo / "source" / "resources" / "common" / "site.css").parent.mkdir(parents=True)
    (repo / "source" / "resources" / "common" / "site.css").write_text("body{}", encoding="utf-8")
    _build(cfg, repo, home)
    css = repo / "target" / "resources" / "common" / "site.css"
    stamp = os.stat(css).st_mtime_ns
    result = _build(cfg, repo, home)
    assert css.exists() and os.stat(css).st_mtime_ns == stamp
    assert "COPIED_GLOBAL_RESOURCES copied=0 deleted=0" in result.stdout


def test_deploy_record_is_saved(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    _build(cfg, repo, home)
    kbdict = json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))
    assert kbdict["deployed_static"] == ["resources/images/x.png", "resources/images/y.png"]


def test_removed_override_of_a_theme_file_brings_the_theme_file_back(tmp_path, home):
    cfg, repo, theme = _repo(tmp_path)
    override = repo / "source" / "resources" / "themes" / "mini" / "framework" / "mini.css"
    override.parent.mkdir(parents=True)
    override.write_text("/* mine */", encoding="utf-8")
    _build(cfg, repo, home)
    deployed = repo / "target" / "resources" / "themes" / "mini" / "framework" / "mini.css"
    assert deployed.read_text(encoding="utf-8") == "/* mine */"
    result = _build(cfg, repo, home)
    assert "COPIED_GLOBAL_RESOURCES copied=0 deleted=0" in result.stdout
    override.unlink()
    _build(cfg, repo, home)
    assert deployed.read_text(encoding="utf-8") == (theme / "framework" / "mini.css").read_text(encoding="utf-8")
