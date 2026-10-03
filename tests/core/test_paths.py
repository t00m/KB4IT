import json

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_relative_paths_resolve_against_repo_root(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    result = run_kb4it("build", cfg, cwd=elsewhere, home=home)
    assert result.returncode == 0, result.stdout
    assert (repo / "target" / "a.html").exists()
    assert not (elsewhere / "target").exists()


def test_cwd_relative_paths_still_work_with_a_warning(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme),
                     source="repo/source", target="repo/target")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "PATH_CWD_RELATIVE key=source" in result.stdout
    assert (repo / "target" / "a.html").exists()


def test_create_writes_root_relative_paths(tmp_path, home):
    result = run_kb4it("create", "techdoc", "newrepo", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    conf = json.loads((tmp_path / "newrepo" / "config" / "repo.json").read_text())
    assert conf["source"] == "source"
    assert conf["target"] == "target"
    build = run_kb4it("build", tmp_path / "newrepo" / "config" / "repo.json", cwd=home, home=home)
    assert build.returncode == 0, build.stdout


def test_blog_create_then_build_from_another_cwd(tmp_path, home):
    result = run_kb4it("create", "blog", "newblog", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    build = run_kb4it("build", tmp_path / "newblog" / "config" / "repo.json", cwd=home, home=home)
    assert build.returncode == 0, build.stdout
    assert "CONFIG_FAIL" not in build.stdout


def test_create_makes_source_and_target_when_the_app_has_none(tmp_path, home):
    # Git cannot store empty folders, so a theme's sample app may ship only its config.
    theme = mini_theme(home / ".kb4it" / "opt" / "resources" / "themes" / "mini")
    (theme / "apps" / "default" / "config").mkdir(parents=True)
    (theme / "apps" / "default" / "config" / "repo.json").write_text(
        json.dumps({"title": "T", "theme": "mini", "source": "source", "target": "target"}))
    result = run_kb4it("create", "mini", "newrepo", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "newrepo" / "source").is_dir()
    build = run_kb4it("build", tmp_path / "newrepo" / "config" / "repo.json", cwd=tmp_path, home=home)
    assert build.returncode == 0, build.stdout
