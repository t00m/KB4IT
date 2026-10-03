"""The kb4it command line: list commands, info, create and the error exits."""

import fcntl
import json

import pytest

from tests.helpers import mini_theme, page, run_kb4it, write_repo

TRACKED_THEMES = ("apphelp", "blog", "bookshelf", "techdoc")


def test_version(tmp_path, home):
    result = run_kb4it("--version", cwd=tmp_path, home=home)
    assert result.returncode == 0
    assert result.stdout.startswith("KB4IT ")


def test_themes_lists_every_tracked_theme(tmp_path, home):
    result = run_kb4it("themes", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    for theme in TRACKED_THEMES:
        assert f"id={theme} " in result.stdout
    assert "THEME_INVALID" not in result.stdout
    assert "ERROR |" not in result.stdout


def test_apps_lists_the_sample_apps(tmp_path, home):
    result = run_kb4it("apps", "techdoc", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "APP name=default" in result.stdout


def test_apps_of_unknown_theme(tmp_path, home):
    result = run_kb4it("apps", "nosuchtheme", cwd=tmp_path, home=home)
    assert "THEME_NOT_FOUND name=nosuchtheme" in result.stdout


def test_projects_registry(tmp_path, home):
    result = run_kb4it("projects", cwd=tmp_path, home=home)
    assert result.returncode == 0
    assert "No projects found." in result.stdout
    result = run_kb4it("create", "blog", "myblog", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    result = run_kb4it("projects", cwd=tmp_path, home=home)
    config = tmp_path / "myblog" / "config" / "repo.json"
    assert str(config) in result.stdout


def test_projects_registry_unreadable(tmp_path, home):
    (home / ".kb4it").mkdir()
    (home / ".kb4it" / "projects.json").write_text("{not json", encoding="utf-8")
    result = run_kb4it("projects", cwd=tmp_path, home=home)
    assert "Error loading projects" in result.stdout


def test_create_writes_relative_paths_and_compile_script(tmp_path, home):
    result = run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    repo = tmp_path / "repo"
    conf = json.loads((repo / "config" / "repo.json").read_text())
    assert (conf["source"], conf["target"]) == ("source", "target")
    script = repo / "bin" / "compile.sh"
    assert script.read_text().startswith("kb4it -L INFO build ")
    assert script.stat().st_mode & 0o100


def test_create_with_unknown_theme_fails(tmp_path, home):
    result = run_kb4it("create", "nosuchtheme", "repo", cwd=tmp_path, home=home)
    assert result.returncode == 1, result.stdout
    assert "THEME_NOT_FOUND name=nosuchtheme" in result.stdout
    assert not (tmp_path / "repo").exists()


def test_info_prints_the_configuration(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, tagline="Line", workers=2)
    result = run_kb4it("info", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "Title: Test" in result.stdout
    assert "Tagline: Line" in result.stdout
    assert "Number of workers: 2" in result.stdout


def test_missing_config_file(tmp_path, home):
    result = run_kb4it("build", tmp_path / "nope" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "CONFIG_MISSING" in result.stdout


def test_invalid_json_config(tmp_path, home):
    cfg = tmp_path / "config" / "repo.json"
    cfg.parent.mkdir()
    cfg.write_text("{ broken", encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "CONFIG_ERROR" in result.stdout


def test_config_missing_keys(tmp_path, home):
    cfg = tmp_path / "config" / "repo.json"
    cfg.parent.mkdir()
    cfg.write_text(json.dumps({"title": "T"}), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    for key in ("source", "target", "theme"):
        assert f"CONFIG_KEY_MISSING key={key}" in result.stdout


def test_unknown_theme(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "nosuchtheme", {"a.md": page("A", Tag="x")})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 1
    assert "THEME_NOT_FOUND name=nosuchtheme" in result.stdout


def test_missing_source_directory(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {}, theme_path=str(theme), source="nosource")
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 1
    assert "SOURCE_MISSING" in result.stdout


def test_empty_theme_path(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, theme_path=" ")
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 1
    assert "theme_path" in result.stdout


def test_force_rebuilds_everything_and_keeps_sources(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="y")},
                     theme_path=str(theme))
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    again = run_kb4it("build", cfg, cwd=repo, home=home)
    assert "compiled=0" in again.stdout
    forced = run_kb4it("build", "--force", cfg, cwd=repo, home=home)
    assert forced.returncode == 0, forced.stdout
    assert "compiled=2" in forced.stdout
    assert (repo / "source" / "a.md").exists()


def test_debug_log_level(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    result = run_kb4it("-L", "DEBUG", "build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "[CONTROLLER] ACTION name=build" in result.stdout
    assert (repo / "var" / "log" / "kb4it.log").exists()


def test_local_themes_are_listed_and_used(tmp_path, home):
    local = home / ".kb4it" / "opt" / "resources" / "themes"
    mini_theme(local / "mini")
    broken = local / "broken"
    broken.mkdir()
    (broken / "theme.json").write_text("{not json", encoding="utf-8")
    result = run_kb4it("themes", cwd=tmp_path, home=home)
    assert "THEME scope=local id=mini" in result.stdout
    assert "THEME_CONF_INVALID" in result.stdout
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert (repo / "target" / "documents.json").exists()


def test_theme_inside_the_sources_wins(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x")})
    logic = mini_theme(repo / "source" / "resources" / "themes" / "techdoc", id="techdoc") / "logic" / "theme.py"
    logic.write_text(logic.read_text(encoding="utf-8").replace("documents.json", "own.json"), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert (repo / "target" / "own.json").exists()


@pytest.mark.parametrize("make, reason", [
    (lambda path: path.write_text("x", encoding="utf-8"), "not_a_directory"),
    (lambda path: path.mkdir(), "missing_theme_json"),
])
def test_bad_theme_path(tmp_path, home, make, reason):
    make(tmp_path / "theme")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, theme_path=str(tmp_path / "theme"))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 1
    assert f"THEME_PATH_INVALID path={tmp_path / 'theme'} reason={reason}" in result.stdout


def test_theme_without_requirement_loads_with_a_warning(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    conf = json.loads((theme / "theme.json").read_text())
    del conf["kb4it"]
    (theme / "theme.json").write_text(json.dumps(conf), encoding="utf-8")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "THEME_REQUIREMENT_MISSING id=mini" in result.stdout


def test_second_instance_is_refused(tmp_path, home):
    lock = home / ".kb4it" / "var" / "kb4it.lock"
    lock.parent.mkdir(parents=True)
    with open(lock, "w", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fh.write("4242")
        fh.flush()
        result = run_kb4it("themes", cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "KB4IT is already running (PID 4242)" in result.stdout
