"""Shell completion: the completers and the argcomplete protocol."""

import argparse
import sys

from kb4it.core import completion
from kb4it.core.main import build_parser
from tests.helpers import run_kb4it

TRACKED_THEMES = ("apphelp", "blog", "bookshelf", "techdoc")


def test_installed_themes_lists_every_tracked_theme():
    assert set(TRACKED_THEMES) <= set(completion.installed_themes())


def test_apps_of_a_bundled_theme():
    assert "default" in completion.apps_of("techdoc")


def test_theme_completer_filters_by_prefix():
    assert completion.theme_completer("te") == ["techdoc"]
    assert completion.theme_completer("nosuch") == []


def test_app_completer_uses_the_theme_already_typed():
    parsed = argparse.Namespace(theme="techdoc")
    assert "default" in completion.app_completer("d", parsed_args=parsed)


def test_app_completer_without_a_theme_lists_every_app():
    assert "default" in completion.app_completer("d", parsed_args=argparse.Namespace())


def test_parser_attaches_the_completers():
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "action")
    apps = {action.dest: action for action in subparsers.choices["apps"]._actions}
    assert apps["theme"].completer is completion.theme_completer
    create = {action.dest: action for action in subparsers.choices["create"]._actions}
    assert create["theme"].completer is completion.theme_completer
    assert create["app"].completer is completion.app_completer


def test_enable_without_argcomplete_does_nothing(monkeypatch):
    monkeypatch.setitem(sys.modules, "argcomplete", None)
    assert completion.enable(build_parser()) is None


def _complete(tmp_path, home, line):
    out = tmp_path / "completions"
    point = str(len(line))
    result = run_kb4it(cwd=tmp_path, home=home, env={
        "COMP_LINE": line,
        "COMP_POINT": point,
        "_ARGCOMPLETE": "1",
        "_ARGCOMPLETE_SHELL": "bash",
        "_ARGCOMPLETE_SUPPRESS_SPACE": "1",
        "_ARGCOMPLETE_STDOUT_FILENAME": str(out),
    })
    assert result.returncode == 0, result.stdout
    return out.read_text(encoding="utf-8").split("\x0b")


def test_argcomplete_completes_a_theme(tmp_path, home):
    assert "techdoc" in _complete(tmp_path, home, "kb4it apps te")


def test_argcomplete_completes_an_app_of_the_typed_theme(tmp_path, home):
    assert "default" in _complete(tmp_path, home, "kb4it create techdoc ")


def test_argcomplete_completes_a_command(tmp_path, home):
    assert "build" in _complete(tmp_path, home, "kb4it bu")


def test_app_completer_stops_once_the_app_is_typed():
    # While completing `kb4it create techdoc default <Tab>`, argparse binds the typed app to repo_path.
    parsed = argparse.Namespace(theme="techdoc", app="default", repo_path="default")
    assert completion.app_completer("", parsed_args=parsed) == []


def test_argcomplete_completes_the_path_after_the_app(tmp_path, home):
    (tmp_path / "mykb").mkdir()
    words = _complete(tmp_path, home, "kb4it create techdoc default ")
    assert "mykb/" in words
    assert "sapbasis" not in words


def _listed_kb(tmp_path, home):
    import json as _json
    from tests.helpers import page, write_repo
    config = write_repo(tmp_path / "kbdir", "techdoc", {"a.md": page("A", Tag="backup, linux", Status="Open")})
    (home / ".kb4it").mkdir(exist_ok=True)
    (home / ".kb4it" / "projects.json").write_text(_json.dumps(
        {"projects": [{"id": "kb1", "name": "KB", "config": str(config)}]}), encoding="utf-8")
    return config


def test_argcomplete_completes_ids_and_paths(tmp_path, home):
    _listed_kb(tmp_path, home)
    words = _complete(tmp_path, home, "kb4it build k")
    assert "kb1" in words
    assert "kbdir/" in words


def test_argcomplete_completes_only_ids_after_p(tmp_path, home):
    _listed_kb(tmp_path, home)
    words = _complete(tmp_path, home, "kb4it search x -p ")
    assert "kb1" in words
    assert "kbdir/" not in words


def test_argcomplete_completes_keys_and_values(tmp_path, home):
    _listed_kb(tmp_path, home)
    assert "Tag" in _complete(tmp_path, home, "kb4it keys kb1 T")
    assert "backup" in _complete(tmp_path, home, "kb4it keys kb1 Tag b")


def test_argcomplete_completes_where(tmp_path, home):
    _listed_kb(tmp_path, home)
    assert "Tag=" in _complete(tmp_path, home, "kb4it search x --where Ta")
    assert any(word.endswith("backup") for word in _complete(tmp_path, home, "kb4it search x --where Tag=b"))


def test_completers_on_a_broken_project_return_nothing():
    parsed = argparse.Namespace(project="nosuch-project", key="Tag", projects=["nosuch-project"])
    assert completion.key_completer("", parsed_args=parsed) == []
    assert completion.value_completer("", parsed_args=parsed) == []
    assert completion.where_completer("", parsed_args=parsed) == []
