"""Textual TUI: drive every screen with the Textual pilot against throwaway repositories."""

import asyncio
import json
import pathlib
import time
import urllib.request

import pytest
from textual.widgets import Button, DataTable, Input, Label, ListView, RadioButton, RichLog

from kb4it.tui import app as tui
from kb4it.core import projects as core_projects
from kb4it.tui import clipboard
from kb4it.tui import projects as tui_projects
from kb4it.tui.screens import project as project_screens
from kb4it.tui.screens.edit_id import EditIdScreen
from tests.helpers import mini_theme, page, run_kb4it, write_repo

SIZE = (140, 60)


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """Point the TUI project registry at a fresh file."""
    path = tmp_path / "projects.json"
    monkeypatch.setattr(core_projects, "PROJECTS_FILE", path)
    return path


@pytest.fixture
def mini_repo(tmp_path):
    """A mini theme repository with two pages, not built yet."""
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x", Topic="t"), "b.md": page("B", Tag="y")},
                     theme_path=str(theme))
    return cfg


@pytest.fixture
def built_repo(mini_repo, tmp_path, home):
    (mini_repo.parent.parent / "source" / "index.md").write_text(page("Home", Tag="x"), encoding="utf-8")
    result = run_kb4it("build", mini_repo, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return mini_repo


def register(registry, *configs):
    tui.save_projects([{"name": f"P{i}", "config": str(cfg)} for i, cfg in enumerate(configs)])


def run(scenario):
    """Run an async pilot scenario against a fresh KB4ITTUI."""
    async def main():
        app = tui.KB4ITTUI()
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await scenario(app, pilot)
    asyncio.run(main())


async def wait_for(pilot, condition, timeout=60):
    end = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < end, "timed out"
        await pilot.pause(0.1)


async def open_first_project(app, pilot):
    app.screen.query_one("#proj-list", DataTable).move_cursor(row=0)
    await pilot.pause()
    app.screen.action_open_project()
    await pilot.pause()
    assert isinstance(app.screen, tui.ProjectScreen)


def test_registry_round_trip(registry):
    assert tui.load_projects() == []
    tui.save_projects([{"name": "A", "config": "/x/config/repo.json"}])
    assert tui.load_projects() == [{"name": "A", "config": "/x/config/repo.json"}]
    registry.write_text("{broken", encoding="utf-8")
    assert tui.load_projects() == []


def test_helpers(tmp_path):
    ids = {t["id"] for t in tui.get_themes()}
    assert {"apphelp", "blog", "bookshelf", "techdoc"} <= ids
    assert "default" in tui.get_apps("techdoc")
    assert tui.get_apps("nosuchtheme") == []
    cfg = str(tmp_path / "repo" / "config" / "repo.json")
    assert tui._resolve_repo_path(cfg, "target") == tmp_path / "repo" / "target"
    absolute = str(tmp_path / "abs")  # "/abs" is not absolute on Windows
    assert tui._resolve_repo_path(cfg, absolute) == pathlib.Path(absolute)
    assert tui._log_path(cfg) is None and tui._kbdict_path(cfg) is None
    assert tui._parse_level("   ERROR | x") == "ERROR"
    assert tui._parse_level("plain line") == "INFO"
    assert tui._parse_level("2026-11-03 21:00:00 |    WARNING | MainThread | Backend | backend:1 | x") == "WARNING"


@pytest.fixture
def user_themes(tmp_path, monkeypatch):
    """Point the user's themes folder and var folder at fresh ones; return the themes folder."""
    from kb4it.core.env import ENV
    root = tmp_path / "kbhome"
    monkeypatch.setitem(ENV["LPATH"], "VAR", str(root / "var"))
    monkeypatch.setitem(ENV["LPATH"], "THEMES", str(root / "themes"))
    return root / "themes"


def test_get_themes_lists_every_copy_and_marks_the_active_one(tmp_path, user_themes):
    from kb4it.core import themeinstall
    from tests.core.test_themeinstall import mini_zip
    themeinstall.install_zip(mini_zip(tmp_path, top="techdoc", id="techdoc"))
    techdoc = [t for t in tui.get_themes() if t["id"] == "techdoc"]
    assert len(techdoc) == 2
    assert [t["_scope"] for t in techdoc if t["_active"]] == ["local"]
    active = [t for t in tui_projects.active_themes() if t["id"] == "techdoc"]
    assert len(active) == 1 and active[0]["_scope"] == "local"
    assert all(t["_active"] for t in tui_projects.active_themes())


def theme_rows(table):
    return [table.get_row_at(index) for index in range(table.row_count)]


def test_themes_screen_shows_active_column(tmp_path, registry, user_themes):
    from kb4it.core import themeinstall
    from tests.core.test_themeinstall import mini_zip
    themeinstall.install_zip(mini_zip(tmp_path, top="techdoc", id="techdoc"))

    async def scenario(app, pilot):
        app.push_screen(tui.ThemesScreen())
        await pilot.pause()
        table = app.screen.query_one("#tbl", DataTable)
        columns = [str(column.label) for column in table.columns.values()]
        assert columns[:5] == ["ID", "Name", "Version", "Active", "Scope"]
        techdoc = sorted((row[3], row[4]) for row in theme_rows(table) if row[0] == "techdoc")
        assert techdoc == [("no", "global"), ("yes", "local")]
    run(scenario)


def test_themes_screen_installs_from_a_path(tmp_path, registry, user_themes):
    from tests.core.test_themeinstall import mini_zip
    zip_path = mini_zip(tmp_path)

    async def scenario(app, pilot):
        app.push_screen(tui.ThemesScreen())
        await pilot.pause()
        app.screen.query_one("#install", Button).press()
        await pilot.pause()
        app.screen.query_one("#inp-source", Input).value = str(zip_path)
        app.screen.query_one("#do-install", Button).press()
        table = None

        def installed():
            nonlocal table
            if not isinstance(app.screen, tui.ThemesScreen):
                return False
            table = app.screen.query_one("#tbl", DataTable)
            return any(row[0] == "mini" for row in theme_rows(table))
        await wait_for(pilot, installed, timeout=20)
        assert (user_themes / "mini" / "theme.json").is_file()
    run(scenario)


def test_unexpected_install_error_is_a_notification(tmp_path, registry, user_themes, monkeypatch):
    from kb4it.core import themeinstall

    def broken(source):
        raise RuntimeError("File theme.json is encrypted, password required")
    monkeypatch.setattr(themeinstall, "install", broken)
    notes = []

    async def scenario(app, pilot):
        monkeypatch.setattr(app, "notify", lambda message, **kw: notes.append(message))
        app.push_screen(tui.ThemesScreen())
        await pilot.pause()
        app.screen.query_one("#install", Button).press()
        await pilot.pause()
        app.screen.query_one("#inp-source", Input).value = str(tmp_path / "x.zip")
        app.screen.query_one("#do-install", Button).press()
        await wait_for(pilot, lambda: any("encrypted" in note for note in notes), timeout=10)
        assert isinstance(app.screen, tui.ThemesScreen)
    run(scenario)


def test_uninstall_enabled_only_for_local_rows(tmp_path, registry, user_themes):
    from kb4it.core import themeinstall
    from tests.core.test_themeinstall import mini_zip
    themeinstall.install_zip(mini_zip(tmp_path))

    async def scenario(app, pilot):
        app.push_screen(tui.ThemesScreen())
        await pilot.pause()
        table = app.screen.query_one("#tbl", DataTable)
        uninstall = app.screen.query_one("#uninstall", Button)
        rows = theme_rows(table)
        global_row = next(i for i, row in enumerate(rows) if row[4] == "global")
        local_row = next(i for i, row in enumerate(rows) if row[0] == "mini")
        table.move_cursor(row=global_row)
        await pilot.pause()
        assert uninstall.disabled
        table.move_cursor(row=local_row)
        await pilot.pause()
        assert not uninstall.disabled
        uninstall.press()
        await pilot.pause()
        assert isinstance(app.screen, tui.ConfirmScreen)
        app.screen.query_one("#yes", Button).press()
        await pilot.pause()
        await wait_for(pilot, lambda: not (user_themes / "mini").exists(), timeout=10)
        assert isinstance(app.screen, tui.ThemesScreen)
        assert not any(row[0] == "mini" for row in theme_rows(app.screen.query_one("#tbl", DataTable)))
    run(scenario)


def test_copy_to_clipboard_falls_back_to_osc52(monkeypatch):
    copied = []

    class FakeApp:
        def copy_to_clipboard(self, text):
            copied.append(text)

    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert tui._copy_to_clipboard(FakeApp(), "hello") == (True, "OSC52")
    assert copied == ["hello"]


@pytest.mark.parametrize("family, expected", [
    ("linux", ["wl-copy", "xclip", "xsel"]),
    ("darwin", ["pbcopy"]),
    ("windows", ["clip.exe"]),
])
def test_clipboard_tools_per_platform(monkeypatch, family, expected):
    monkeypatch.setattr("shutil.which", lambda name: f"/bin/{name}")
    assert [cmd[0] for cmd, _enc in tui.clipboard_commands(family)] == expected


def test_clipboard_skips_tools_not_on_path(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/xsel" if name == "xsel" else None)
    assert [cmd[0] for cmd, _enc in tui.clipboard_commands("linux")] == ["xsel"]


def test_windows_clipboard_gets_utf16(monkeypatch):
    sent = []
    monkeypatch.setattr(clipboard, "clipboard_commands", lambda family=None: [(["clip.exe"], "utf-16")])
    monkeypatch.setattr("subprocess.run", lambda cmd, input, check, timeout: sent.append(input))
    assert tui._copy_to_clipboard(object(), "Tomás") == (True, "clip.exe")
    assert sent[0].decode("utf-16") == "Tomás"


def test_main_screen_without_projects(registry):
    async def scenario(app, pilot):
        assert isinstance(app.screen, tui.MainScreen)
        assert "(none)" in str(app.screen.query_one("#list-label", Label).render())
        await pilot.click("#delete")
        await pilot.pause()
        assert isinstance(app.screen, tui.MainScreen)
        await pilot.click("#themes")
        await pilot.pause()
        assert isinstance(app.screen, tui.ThemesScreen)
        assert app.screen.query_one(DataTable).row_count >= 4
        await pilot.click("#back")
        await pilot.click("#apps")
        await pilot.pause()
        assert isinstance(app.screen, tui.AppsScreen)
        app.screen.query_one("#themes-list", ListView).index = 0
        await pilot.pause()
        assert app.screen.query_one("#apps-tbl", DataTable).row_count >= 1
        await pilot.click("#back")
        await pilot.press("q")
    run(scenario)


def test_project_screens_after_a_build(registry, built_repo, monkeypatch):
    opened = []
    monkeypatch.setattr(project_screens.webbrowser, "open", opened.append)
    monkeypatch.setattr(clipboard, "_copy_to_clipboard", lambda _app, text: (True, "test"))
    register(registry, built_repo)

    async def scenario(app, pilot):
        await open_first_project(app, pilot)
        screen = app.screen
        for button in ("#explore", "#log", "#browse-local", "#browse-server"):
            assert not screen.query_one(button, Button).disabled, button

        await pilot.click("#info")
        await pilot.pause()
        assert isinstance(app.screen, tui.ProjectInfoScreen)
        assert app.screen.query_one(DataTable).row_count > 4
        await pilot.click("#back")

        await pilot.click("#files")
        await pilot.pause()
        assert isinstance(app.screen, tui.FileListScreen)
        assert app.screen.query_one(DataTable).row_count == 3
        await pilot.click("#back")

        await pilot.click("#log")
        await pilot.pause()
        assert isinstance(app.screen, tui.LogViewerScreen)
        all_lines = len(app.screen.query_one(RichLog).lines)
        assert all_lines > 0
        await pilot.click("#f-err")
        await pilot.pause()
        assert len(app.screen.query_one(RichLog).lines) < all_lines
        for button in ("#f-info", "#f-warn", "#f-all", "#copy"):
            await pilot.click(button)
        await pilot.click("#back")

        await pilot.click("#explore")
        await pilot.pause()
        explorer = app.screen
        assert isinstance(explorer, tui.ExplorerScreen)
        keys = explorer.query_one("#keys-pane", ListView)
        keys.index = sorted(explorer._metadata).index("Tag")
        await pilot.pause()
        explorer.query_one("#vals-pane", ListView).index = 0
        await pilot.pause()
        explorer.query_one("#docs-pane", ListView).index = 0
        await pilot.pause()
        assert explorer._selected_doc == "a.md"
        await pilot.click("#btn-view")
        await pilot.pause()
        assert isinstance(app.screen, tui.DocumentViewerScreen)
        assert app.screen.query_one("#meta", DataTable).row_count >= 2
        await pilot.click("#copy")
        await pilot.click("#back")
        await pilot.click("#back")

        await pilot.click("#browse-local")
        await pilot.click("#browse-server")
        await pilot.pause()
        assert opened[0].startswith("file://") and opened[0].endswith("/index.html")
        assert opened[1].startswith("http://127.0.0.1:")
        status = await asyncio.to_thread(lambda: urllib.request.urlopen(opened[1], timeout=5).status)
        assert status == 200
        page = await asyncio.to_thread(lambda: urllib.request.urlopen(opened[1], timeout=5).read().decode("utf-8"))
        assert "kb4it-live-reload" in page, "the TUI web server reloads pages after a rebuild"
        live = await asyncio.to_thread(
            lambda: urllib.request.urlopen(opened[1] + "__kb4it/status", timeout=5).read().decode("utf-8"))
        assert '"build"' in live
        await pilot.click("#back")
        assert isinstance(app.screen, tui.MainScreen)
    run(scenario)
    httpd, _port = tui._WEB_SERVERS.pop(str(built_repo))
    httpd.shutdown()


def test_compile_and_force_compile(registry, mini_repo):
    register(registry, mini_repo)

    async def scenario(app, pilot):
        await open_first_project(app, pilot)
        assert app.screen.query_one("#explore", Button).disabled
        for button in ("#compile", "#force-compile"):
            await pilot.click(button)
            await pilot.pause()
            build = app.screen
            assert isinstance(build, tui.BuildScreen)
            await wait_for(pilot, lambda screen=build: not screen.query_one("#close", Button).disabled)
            status = str(build.query_one("#status", Label).render())
            assert status.startswith("Done"), status
            await pilot.click("#close")
            await pilot.pause()
        assert not app.screen.query_one("#explore", Button).disabled
    run(scenario)
    target = mini_repo.parent.parent / "target"
    assert (target / "a.html").exists() and (target / "b.html").exists()


def test_failed_build_is_reported(registry, tmp_path):
    cfg = write_repo(tmp_path / "broken", "nosuchtheme", {"a.md": page("A", Tag="x")})
    register(registry, cfg)

    async def scenario(app, pilot):
        await open_first_project(app, pilot)
        await pilot.click("#compile")
        await pilot.pause()
        build = app.screen
        await wait_for(pilot, lambda: not build.query_one("#close", Button).disabled)
        assert str(build.query_one("#status", Label).render()).startswith("FAILED")
    run(scenario)


def test_create_project(registry, tmp_path):
    path = tmp_path / "newblog"

    async def scenario(app, pilot):
        await pilot.click("#new")
        await pilot.pause()
        create = app.screen
        assert isinstance(create, tui.CreateProjectScreen)
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert create.query_one("#error-banner", Label).display     # empty name
        ids = [t["id"] for t in create._themes]
        create.query_one("#themes-list", ListView).index = ids.index("blog")
        await pilot.pause()
        create.query_one("#inp-name", Input).value = "New blog"
        create.query_one("#inp-path", Input).value = str(tmp_path / "missing" / "x")
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert "does not exist" in str(create.query_one("#error-banner", Label).render())
        create.query_one("#inp-path", Input).value = str(path)
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert "search engines" in str(create.query_one("#error-banner", Label).render())   # no choice yet
        assert not path.exists()
        create.query_one("#index-no", RadioButton).value = True
        await pilot.pause()
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, tui.MainScreen), create.query_one("#error-banner", Label).render()
    run(scenario)
    conf = json.loads((path / "config" / "repo.json").read_text(encoding="utf-8"))
    assert conf["theme"] == "blog"
    assert conf["seo"]["index"] is False, "the same path as kb4it create --index no"
    assert tui.load_projects() == [{"name": "New blog", "config": str(path / "config" / "repo.json")}]


def test_create_project_shows_next_steps(registry, tmp_path):
    path = tmp_path / "steps"
    seen = []

    async def scenario(app, pilot):
        app.notify = lambda message, **kwargs: seen.append(message)
        await pilot.click("#new")
        await pilot.pause()
        create = app.screen
        ids = [t["id"] for t in create._themes]
        create.query_one("#themes-list", ListView).index = ids.index("blog")
        await pilot.pause()
        create.query_one("#inp-name", Input).value = "Steps"
        create.query_one("#index-yes", RadioButton).value = True
        await pilot.pause()
        create.query_one("#inp-path", Input).value = str(path)
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, tui.MainScreen)
    run(scenario)
    assert any("Preview the site with: kb4it serve" in message for message in seen)
    assert any("Write documents in" in message for message in seen)


def test_create_failure_shows_no_next_steps(registry, tmp_path):
    blocked = tmp_path / "blocked"
    blocked.write_text("a file, not a folder", encoding="utf-8")
    seen = []

    async def scenario(app, pilot):
        app.notify = lambda message, **kwargs: seen.append(message)
        await pilot.click("#new")
        await pilot.pause()
        create = app.screen
        ids = [t["id"] for t in create._themes]
        create.query_one("#themes-list", ListView).index = ids.index("blog")
        await pilot.pause()
        create.query_one("#inp-name", Input).value = "Blocked"
        create.query_one("#index-yes", RadioButton).value = True
        await pilot.pause()
        create.query_one("#inp-path", Input).value = str(blocked)
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert create.query_one("#error-banner", Label).display
        assert not isinstance(app.screen, tui.MainScreen)
    run(scenario)
    assert not any("Preview the site with: kb4it serve" in message for message in seen)


def test_import_and_delete_project(registry, mini_repo):
    async def scenario(app, pilot):
        await pilot.click("#import")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, tui.ImportProjectScreen)
        screen.query_one("#inp-path", Input).focus()
        screen.query_one("#inp-path", Input).value = str(mini_repo)
        await pilot.press("enter")
        await pilot.pause()
        assert screen.query_one("#inp-name", Input).value == "Test"
        assert screen.query_one("#preview", DataTable).row_count == 5   # title, theme, source, target, config
        await pilot.click("#import")
        await pilot.pause()
        assert tui.load_projects() == [{"name": "Test", "config": str(mini_repo)}]

        app.screen.query_one("#proj-list", DataTable).move_cursor(row=0)
        await pilot.click("#delete")
        await pilot.pause()
        assert isinstance(app.screen, tui.ConfirmScreen)
        await pilot.click("#no")
        await pilot.pause()
        assert len(tui.load_projects()) == 1
        await pilot.click("#delete")
        await pilot.pause()
        await pilot.click("#yes")
        await pilot.pause()
        assert tui.load_projects() == []
    run(scenario)


def test_tui_shows_the_help_banner_until_dismissed(registry, tmp_path, monkeypatch):
    from kb4it.core.env import ENV
    from kb4it.core.notice import help_notice_dismissed
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(tmp_path / "home"))
    monkeypatch.delenv("CI", raising=False)

    async def scenario(app, pilot):
        banner = app.screen.query_one("#help-banner")
        assert banner.display
        assert not help_notice_dismissed()
        await pilot.press("d")
        await pilot.pause()
        assert not banner.display
        assert help_notice_dismissed()
    run(scenario)


def test_tui_drops_the_dismiss_key_once_the_banner_is_gone(registry, tmp_path, monkeypatch):
    from kb4it.core.env import ENV
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(tmp_path / "home"))
    monkeypatch.delenv("CI", raising=False)

    def dismiss_offered(app):
        active = app.screen.active_bindings.get("d")
        return active is not None and active.enabled

    async def scenario(app, pilot):
        assert dismiss_offered(app)
        await pilot.press("d")
        await pilot.pause()
        assert not dismiss_offered(app)
    run(scenario)


def test_tui_hides_the_help_banner_in_ci(registry, tmp_path, monkeypatch):
    from kb4it.core.env import ENV
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(tmp_path / "home"))
    monkeypatch.setenv("CI", "true")

    async def scenario(app, pilot):
        assert not app.screen.query_one("#help-banner").display
    run(scenario)


def test_log_viewer_keeps_a_traceback_with_its_error(registry, tmp_path):
    log = tmp_path / "repo" / "var" / "log" / "kb4it.log"
    log.parent.mkdir(parents=True)
    log.write_text(
        "2026-11-03 21:00:00 |       INFO | MainThread | Backend | backend:1 | [BACKEND] START\n"
        "2026-11-03 21:00:01 |      ERROR | compile_0 | Compiler | compiler:2 | [COMPILER] ERROR doc=a.md\n"
        "Traceback (most recent call last):\n"
        "KeyError: 'Date'\n"
        "2026-11-03 21:00:02 |       INFO | MainThread | Workflow | workflow:3 | [WORKFLOW] END\n",
        encoding="utf-8")
    screen = tui.LogViewerScreen(str(tmp_path / "repo" / "config" / "repo.json"))

    class _Log:
        def write(self, _):
            pass

        def clear(self):
            pass
    screen.query_one = lambda *_: _Log()
    screen._load()
    levels = [level for _, level in screen._lines]
    assert levels == ["INFO", "ERROR", "ERROR", "ERROR", "INFO"]


async def fill_create(app, pilot, path, name, pid):
    await pilot.click("#new")
    await pilot.pause()
    create = app.screen
    ids = [t["id"] for t in create._themes]
    create.query_one("#themes-list", ListView).index = ids.index("blog")
    await pilot.pause()
    create.query_one("#inp-name", Input).value = name
    create.query_one("#inp-id", Input).value = pid
    create.query_one("#inp-path", Input).value = str(path)
    create.query_one("#index-no", RadioButton).value = True
    await pilot.pause()
    return create


def test_create_project_with_id(registry, tmp_path):
    path = tmp_path / "withid"

    async def scenario(app, pilot):
        create = await fill_create(app, pilot, path, "With id", "kb3")
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, tui.MainScreen), create.query_one("#error-banner", Label).render()
    run(scenario)
    assert tui.load_projects() == [{"id": "kb3", "name": "With id", "config": str(path / "config" / "repo.json")}]


def test_create_with_taken_id_shows_error_and_creates_nothing(registry, tmp_path, mini_repo):
    core_projects.register(str(mini_repo), pid="kb3")
    path = tmp_path / "taken"

    async def scenario(app, pilot):
        create = await fill_create(app, pilot, path, "Taken", "kb3")
        assert "already used" in str(create.query_one("#id-error", Label).render())
        create.query_one("#create", Button).press()
        await pilot.pause()
        assert "already used" in str(create.query_one("#error-banner", Label).render())
        assert not isinstance(app.screen, tui.MainScreen)
    run(scenario)
    assert not path.exists()


def test_import_project_with_id(registry, mini_repo):
    async def scenario(app, pilot):
        await pilot.click("#import")
        await pilot.pause()
        screen = app.screen
        screen.query_one("#inp-path", Input).focus()
        screen.query_one("#inp-path", Input).value = str(mini_repo)
        await pilot.press("enter")
        await pilot.pause()
        screen.query_one("#inp-id", Input).value = "Bad Id"
        await pilot.pause()
        assert "Invalid id" in str(screen.query_one("#id-error", Label).render())
        await pilot.click("#import")
        await pilot.pause()
        assert tui.load_projects() == []
        screen.query_one("#inp-id", Input).value = "mini"
        await pilot.pause()
        screen.query_one("#import", Button).press()   # the error toast may cover the button
        await pilot.pause()
        assert isinstance(app.screen, tui.MainScreen)
        assert app.screen.query_one("#proj-list", DataTable).get_row_at(0)[0] == "mini"
    run(scenario)
    assert tui.load_projects() == [{"id": "mini", "name": "Test", "config": str(mini_repo)}]


def test_edit_id_sets_changes_and_removes(registry, mini_repo):
    core_projects.register(str(mini_repo))

    async def edit(app, pilot, value):
        app.screen.query_one("#edit-id", Button).press()
        await pilot.pause()
        dialog = app.screen
        assert isinstance(dialog, EditIdScreen)
        dialog.query_one("#inp-id", Input).value = value
        await pilot.pause()
        dialog.query_one("#save", Button).press()
        await pilot.pause()

    async def scenario(app, pilot):
        await open_first_project(app, pilot)
        await edit(app, pilot, "kb5")
        assert core_projects.load()[0]["id"] == "kb5"
        app.screen.query_one("#edit-id", Button).press()
        await pilot.pause()
        assert app.screen.query_one("#inp-id", Input).value == "kb5"
        app.screen.query_one("#cancel", Button).press()
        await pilot.pause()
        await edit(app, pilot, "kb6")
        assert core_projects.load()[0]["id"] == "kb6"
        await edit(app, pilot, "")
        assert "id" not in core_projects.load()[0]
    run(scenario)


def test_edit_id_rejects_taken_id(registry, mini_repo, tmp_path):
    other = write_repo(tmp_path / "other", "mini", {"a.md": page("A", Tag="x")})
    core_projects.register(str(mini_repo))
    core_projects.register(str(other), pid="taken")

    async def scenario(app, pilot):
        await open_first_project(app, pilot)
        app.screen.query_one("#edit-id", Button).press()
        await pilot.pause()
        dialog = app.screen
        dialog.query_one("#inp-id", Input).value = "taken"
        await pilot.pause()
        assert "already used" in str(dialog.query_one("#id-error", Label).render())
        dialog.query_one("#save", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, EditIdScreen)
    run(scenario)
    assert "id" not in core_projects.load()[0]


def test_main_list_is_a_table_of_id_name_and_config(registry, mini_repo, tmp_path):
    other = write_repo(tmp_path / "other", "mini", {"a.md": page("A", Tag="x")}, title="Other")
    core_projects.register(str(mini_repo), pid="kb1")
    core_projects.register(str(other))

    async def scenario(app, pilot):
        table = app.screen.query_one("#proj-list", DataTable)
        assert [str(column.label) for column in table.columns.values()] == ["ID", "Name", "Config"]
        assert table.get_row_at(0) == ["kb1", "Test", str(mini_repo)]
        assert table.get_row_at(1) == ["-", "Other", str(other)]
        table.move_cursor(row=1)
        await pilot.pause()
        app.screen.action_open_project()
        await pilot.pause()
        assert isinstance(app.screen, tui.ProjectScreen)
        assert app.screen.title.startswith("Other")
    run(scenario)


def test_project_screen_shows_the_id(registry, mini_repo):
    core_projects.register(str(mini_repo), pid="kb1")

    async def scenario(app, pilot):
        await open_first_project(app, pilot)
        screen = app.screen
        assert screen.title == "Test (kb1)"
        assert "Id: kb1" in str(screen.query_one("#info-panel").render())
        screen.query_one("#edit-id", Button).press()
        await pilot.pause()
        app.screen.query_one("#inp-id", Input).value = "kb7"
        await pilot.pause()
        app.screen.query_one("#save", Button).press()
        await pilot.pause()
        assert screen.title == "Test (kb7)"
        assert "Id: kb7" in str(screen.query_one("#info-panel").render())
    run(scenario)
