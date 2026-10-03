"""Textual TUI: drive every screen with the Textual pilot against throwaway repositories."""

import asyncio
import json
import time
import urllib.request

import pytest
from textual.widgets import Button, DataTable, Input, Label, ListView, RichLog

from kb4it.tui import app as tui
from tests.helpers import mini_theme, page, run_kb4it, write_repo

SIZE = (140, 60)


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """Point the TUI project registry at a fresh file."""
    path = tmp_path / "projects.json"
    monkeypatch.setattr(tui, "PROJECTS_FILE", path)
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
    app.screen.query_one("#proj-list", ListView).index = 0
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
    assert tui._resolve_repo_path(cfg, "/abs") == tui.Path("/abs")
    assert tui._log_path(cfg) is None and tui._kbdict_path(cfg) is None
    assert tui._parse_level("   ERROR | x") == "ERROR"
    assert tui._parse_level("plain line") == "INFO"


def test_copy_to_clipboard_falls_back_to_osc52(monkeypatch):
    copied = []

    class FakeApp:
        def copy_to_clipboard(self, text):
            copied.append(text)

    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert tui._copy_to_clipboard(FakeApp(), "hello") == (True, "OSC52")
    assert copied == ["hello"]


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
    monkeypatch.setattr(tui.webbrowser, "open", opened.append)
    monkeypatch.setattr(tui, "_copy_to_clipboard", lambda _app, text: (True, "test"))
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
        assert isinstance(app.screen, tui.MainScreen), create.query_one("#error-banner", Label).render()
    run(scenario)
    assert json.loads((path / "config" / "repo.json").read_text())["theme"] == "blog"
    assert tui.load_projects() == [{"name": "New blog", "config": str(path / "config" / "repo.json")}]


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

        app.screen.query_one("#proj-list", ListView).index = 0
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
