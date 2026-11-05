"""Project settings in the TUI: the settings reference, the repo.json editor and its check."""

import asyncio
import json

import pytest
from textual.widgets import Button, DataTable, Input, ListView, TextArea

from kb4it.core.repocheck import check_repo
from kb4it.tui import app as tui
from kb4it.tui import projects, repo_options
from kb4it.tui.repo_options import current_value, theme_options
from kb4it.tui.screens.confirm import ConfirmScreen
from kb4it.tui.screens.settings import RepoEditorScreen, SettingsReferenceScreen
from tests.helpers import write_repo


@pytest.fixture
def repo(tmp_path):
    """A techdoc repository, not built."""
    return write_repo(tmp_path / "repo", "techdoc", {}, seo={"lang": "es"})


def text_of(config, **changes):
    data = json.loads(config.read_text(encoding="utf-8"))
    data.update(changes)
    return json.dumps(data, indent=2)


# check_repo

def test_check_passes_a_good_repo(repo):
    assert check_repo(repo.read_text(encoding="utf-8"), repo) == []


def test_check_reports_broken_json_with_its_place(repo):
    problems = check_repo('{\n  "title": "x"\n  "theme": "techdoc"\n}', repo)
    assert len(problems) == 1
    assert "Not valid JSON" in problems[0] and "line 3" in problems[0]


def test_check_needs_an_object(repo):
    assert check_repo("[1, 2]", repo) == ["repo.json must be a JSON object, between { and }"]


def test_check_needs_the_required_keys(repo):
    problems = check_repo(json.dumps({"title": "x", "theme": "techdoc", "source": ""}), repo)
    assert problems == ["'source' is required and must be a non-empty text",
                        "'target' is required and must be a non-empty text"]


@pytest.mark.parametrize("changes, words", [
    ({"theme": "nosuchtheme"}, "Theme 'nosuchtheme' not found"),
    ({"source": "missing"}, "does not exist"),
    ({"target": "."}, "holds the repository root"),
    ({"editor": "yes"}, "'editor' must be true or false"),
    ({"seo": {"lang": "not a language"}}, "language tag"),
    ({"markdown": {"highlight": "fancy"}}, "markdown.highlight"),
    ({"site_url": "example.org"}, "http"),
    ({"overrides": ""}, "'overrides' must be a folder path"),
    ({"hooks": "hooks/missing.py"}, "Hooks file not found"),
    ({"theme_path": "nowhere"}, "theme.json"),
])
def test_check_reports_what_the_build_rejects(repo, changes, words):
    problems = check_repo(text_of(repo, **changes), repo)
    assert any(words in problem for problem in problems), problems


def test_check_does_not_run_the_hooks_file(repo):
    hooks = repo.parent.parent / "hooks.py"
    hooks.write_text("raise SystemExit('ran')\n", encoding="utf-8")
    assert check_repo(text_of(repo, hooks="hooks.py"), repo) == []


# Settings taken from the help pages

def test_techdoc_settings_come_from_the_help():
    options, has_page = theme_options("techdoc")
    keys = {option.key: option for option in options}
    assert has_page
    for key in ("title", "site_url", "markdown.highlight", "seo.index", "feed.limit", "toc_sidebar", "datatable"):
        assert key in keys, key
    assert "header_keys" not in keys  # a theme.json key, not a repo.json one
    assert keys["editor"].group == "techdoc"  # the theme's row replaces the common one
    assert keys["markdown.highlight"].default == "client"
    assert len(keys) == len(options)


def test_apphelp_block_and_its_top_level_key():
    keys = {option.key for option in theme_options("apphelp")[0]}
    assert {"apphelp.strict", "apphelp.lang", "editor"} <= keys
    assert "apphelp.editor" not in keys


def test_every_setting_has_its_values_and_default():
    """The help tables carry a Values column; the reference reads it next to the Default column."""
    for theme in ("techdoc", "blog", "bookshelf", "apphelp"):
        options = theme_options(theme)[0]
        missing = [option.key for option in options if not option.values]
        assert not missing, (theme, missing)
    keys = {option.key: option for option in theme_options("techdoc")[0]}
    assert keys["markdown.highlight"].values == "client, pygments, none"
    assert keys["markdown.highlight"].default == "client"
    assert keys["quality"].values == "true, false" and keys["quality"].default == "true"
    apphelp = {option.key: option for option in theme_options("apphelp")[0]}
    assert apphelp["apphelp.versions.enabled"].default == "false"
    assert apphelp["apphelp.accent"].default == "#3584e4"


def test_theme_without_a_help_page_gets_the_common_settings():
    options, has_page = theme_options("mytheme")
    assert not has_page
    assert {option.group for option in options} == {"Common"}


def test_help_sources_stand_in_for_unbuilt_help(tmp_path, monkeypatch):
    """A checkout without the offline help (CI) reads help/source; both give the same settings."""
    monkeypatch.setattr(repo_options, "help_dir", lambda: tmp_path)
    from_sources = theme_options("techdoc")
    assert from_sources[1] and len(from_sources[0]) > 50
    monkeypatch.undo()
    if not (repo_options.help_dir() / "reference-repo-json.html").exists():
        pytest.skip("offline help not built")
    assert theme_options("techdoc") == from_sources


def test_current_value_reads_dotted_keys():
    repo = {"title": "Docs", "seo": {"index": False}}
    assert current_value(repo, "title") == '"Docs"'
    assert current_value(repo, "seo.index") == "false"
    assert current_value(repo, "seo.lang") is None
    assert current_value(repo, "profiles.<Property>.type") is None


# Screens

def run(config, registry, scenario):
    projects.save_projects([{"name": "P", "config": str(config)}])

    async def main():
        app = tui.KB4ITTUI()
        async with app.run_test(size=(140, 60)) as pilot:
            await pilot.pause()
            await scenario(app, pilot)
    asyncio.run(main())


@pytest.fixture
def registry(tmp_path, monkeypatch):
    path = tmp_path / "projects.json"
    monkeypatch.setattr(projects, "PROJECTS_FILE", path)
    return path


async def open_project_button(app, pilot, button):
    app.screen.query_one("#proj-list", ListView).index = 0
    await pilot.pause()
    app.screen.action_open_project()
    await pilot.pause()
    app.screen.query_one(button, Button).press()
    await pilot.pause()


def test_settings_reference_screen(repo, registry):
    async def scenario(app, pilot):
        await open_project_button(app, pilot, "#settings-ref")
        screen = app.screen
        assert isinstance(screen, SettingsReferenceScreen)
        table = screen.query_one(DataTable)
        assert table.row_count == len(theme_options("techdoc")[0])
        assert "set in this project" in str(screen.query_one("#summary").render())
        screen.query_one("#filter", Input).value = "toc_sidebar"
        await pilot.pause()
        assert table.row_count == 1
        assert "toc_sidebar" in str(screen.query_one("#detail").render())
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, SettingsReferenceScreen)

    run(repo, registry, scenario)


def test_editor_saves_only_after_a_passing_check(repo, registry):
    original = repo.read_text(encoding="utf-8")

    async def scenario(app, pilot):
        await open_project_button(app, pilot, "#edit-repo")
        screen = app.screen
        assert isinstance(screen, RepoEditorScreen)
        editor = screen.query_one(TextArea)
        save = screen.query_one("#save", Button)
        assert editor.text == original and save.disabled

        editor.load_text(text_of(repo, editor="yes"))
        await pilot.pause()
        screen.action_check()
        await pilot.pause()
        assert save.disabled
        assert "'editor' must be true or false" in str(screen.query_one("#result").render())
        screen.action_save()
        assert repo.read_text(encoding="utf-8") == original

        good = text_of(repo, tagline="Notes of the team")
        editor.load_text(good)
        await pilot.pause()
        screen.action_check()
        await pilot.pause()
        assert not save.disabled

        editor.insert(" ")  # any edit after the check needs a new check
        await pilot.pause()
        assert save.disabled
        editor.load_text(good)
        await pilot.pause()
        screen.action_check()
        await pilot.pause()
        screen.action_save()
        await pilot.pause()
        assert repo.read_text(encoding="utf-8") == good
        assert save.disabled

    run(repo, registry, scenario)


def test_editor_asks_before_dropping_changes(repo, registry):
    async def scenario(app, pilot):
        await open_project_button(app, pilot, "#edit-repo")
        screen = app.screen
        screen.query_one(TextArea).load_text("{}")
        await pilot.pause()
        screen.action_back()
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.click("#no")
        await pilot.pause()
        assert app.screen is screen
        screen.action_back()
        await pilot.pause()
        await pilot.click("#yes")
        await pilot.pause()
        assert not isinstance(app.screen, (RepoEditorScreen, ConfirmScreen))

    run(repo, registry, scenario)
