import json

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def _build(repo, home):
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=repo, home=home)
    assert result.returncode == 0, result.stdout


def test_whole_theme_is_deployed_by_default(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    _build(repo, home)
    res = repo / "target" / "resources"
    assert (res / "themes" / "mini" / "logic" / "theme.py").exists()
    assert (res / "common").is_dir()


def test_deploy_dirs_limits_theme_files(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", deploy_dirs=["framework"])
    repo = tmp_path / "repo"
    write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    _build(repo, home)
    res = repo / "target" / "resources"
    assert (res / "themes" / "mini" / "framework" / "mini.css").exists()
    assert not (res / "themes" / "mini" / "logic").exists()
    assert not (res / "themes" / "default").exists()
    assert not (res / "common").exists()


def test_publish_sources_false_removes_sources(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    _build(repo, home)
    assert (repo / "target" / "sources" / "a.md").exists()
    conf = json.loads(cfg.read_text())
    conf["publish_sources"] = False
    cfg.write_text(json.dumps(conf))
    _build(repo, home)
    assert not (repo / "target" / "sources").exists()


def test_deploy_dirs_rejects_path_escape(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", deploy_dirs=["../logic"])
    repo = tmp_path / "repo"
    write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=repo, home=home)
    assert result.returncode != 0
    assert (theme / "logic" / "theme.py").exists()
    assert not (repo / "target" / "resources" / "logic").exists()


def test_dir_removed_from_deploy_dirs_disappears(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", deploy_dirs=["framework", "logic"])
    repo = tmp_path / "repo"
    write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    _build(repo, home)
    dest = repo / "target" / "resources" / "themes" / "mini"
    assert (dest / "logic").is_dir()
    conf = json.loads((theme / "theme.json").read_text())
    conf["deploy_dirs"] = ["framework"]
    (theme / "theme.json").write_text(json.dumps(conf))
    _build(repo, home)
    assert (dest / "framework").is_dir()
    assert not (dest / "logic").exists()


def test_user_resources_survive_deploy_dirs(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", deploy_dirs=["framework"])
    repo = tmp_path / "repo"
    write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01"),
                              "resources/x.txt": "keep"}, theme_path=str(theme))
    _build(repo, home)
    assert (repo / "target" / "resources" / "x.txt").read_text() == "keep"


def test_failed_build_leaves_no_stale_tmp_for_link_check(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", "[b](b.md)", Date="2026-01-01"),
                                    "b.md": page("B", Date="2026-01-02"),
                                    "boom.md": page("Boom", Date="2026-01-03")}, theme_path=str(theme))
    failed = run_kb4it("build", cfg, cwd=repo, home=home)
    assert failed.returncode != 0
    (repo / "source" / "b.md").unlink()
    (repo / "source" / "boom.md").unlink()
    (repo / "source" / "a.md").write_text(page("A", "[b](b.md) again", Date="2026-01-04"), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "LINK_BROKEN from=a.md to=b.md" in result.stdout


def test_deploy_dirs_rejects_theme_id_dotdot(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", deploy_dirs=["framework"], id="..")
    repo = tmp_path / "repo"
    write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=repo, home=home)
    assert result.returncode != 0
    assert "not a plain name" in result.stdout
    assert (repo / "source" / "a.md").exists()
