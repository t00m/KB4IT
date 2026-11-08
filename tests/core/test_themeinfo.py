"""kb4it theme-info: what a theme is made of, without building a site."""

import json

import pytest

from kb4it.core.exceptions import ThemeError
from kb4it.core.themeinfo import collect, find_theme, render
from tests.helpers import run_kb4it


@pytest.fixture(scope="module")
def techdoc():
    return collect("techdoc")


LEGACY = """
from kb4it.services.themekit import DocumentTheme
from kb4it.services.themekit.filters import FilterMixin

from .helpers import LocalMixin


class Theme(LocalMixin, FilterMixin, DocumentTheme):
    add_page = True
    properties_cloud = False

    def event_documents(self):
        return []
"""


@pytest.fixture(scope="module")
def legacy(tmp_path_factory):
    folder = tmp_path_factory.mktemp("legacy") / "legacy"
    (folder / "logic").mkdir(parents=True)
    (folder / "templates").mkdir()
    (folder / "theme.json").write_text(json.dumps({"id": "legacy", "name": "Legacy", "version": "1.0.0",
                                                   "kb4it": ">=0.12.0", "search": True, "template_base": "uikit"}))
    (folder / "logic" / "helpers.py").write_text("class LocalMixin:\n    def post_deploy_activities(self):\n"
                                                 "        pass\n")
    (folder / "logic" / "theme.py").write_text(LEGACY)
    return collect(str(folder))


def test_legacy_theme_is_marked_deprecated(legacy):
    assert legacy["api"] == "legacy DocumentTheme (deprecated)"
    assert legacy["origin"] == "path"


def test_kits_map_to_feature_names(legacy):
    features = legacy["features"]
    for name in ("table", "events", "property_pages", "table_filter", "search", "editor"):
        assert name in features
    assert "LocalMixin (theme)" in features


def test_legacy_hooks_name_the_theme_file_and_the_feature(legacy):
    hooks = {h["hook"]: h for h in legacy["hooks"]}
    assert hooks["event_documents"]["feature"] == "events"
    assert hooks["event_documents"]["where"].startswith("logic/theme.py:")
    assert hooks["post_deploy_activities"]["class"] == "LocalMixin"


def test_public_theme_lists_its_own_features(techdoc):
    assert techdoc["api"] == "BaseTheme" and techdoc["origin"] == "builtin"
    features = techdoc["features"]
    for name in ("table", "events", "property_pages", "table_filter", "gallery", "search", "editor"):
        assert name in features
    assert features[-2:] == ["quality (theme)", "admin (theme)"]


def test_hooks_name_the_theme_file_and_the_feature(techdoc):
    hooks = {h["hook"]: h for h in techdoc["hooks"]}
    assert hooks["event_documents"]["feature"] == "events"
    assert hooks["event_documents"]["where"].startswith("logic/theme.py:")
    assert hooks["datatable_columns"]["feature"] == "table"
    assert "config_class" not in hooks  # a class attribute, not a hook


def test_options_and_settings(techdoc):
    assert techdoc["options"]["properties_cloud"] is False
    assert techdoc["settings"]["class"] == "TechdocConfig"
    assert "quality" in techdoc["settings"]["values"]


def test_templates_say_where_they_come_from(techdoc):
    origin = {t["name"]: t["origin"] for t in techdoc["templates"]}
    assert origin["HTML_BODY"] == "theme"
    assert origin["EVENTCAL_PAGE_EVENTS_DAYS"] == "base:uikit"
    assert "missing" not in origin.values()


def test_page_theme_does_not_need_property_templates():
    info = collect("apphelp")
    assert info["api"] == "BaseTheme"
    assert "PAGE_KEY" not in {t["name"] for t in info["templates"]}
    assert {"navigation", "search", "editor"} <= set(info["features"])


def test_render_has_one_line_per_section(techdoc):
    text = render(techdoc)
    for label in ("theme ", "api ", "features ", "hooks ", "options ", "templates ", "settings "):
        assert any(line.startswith(label) for line in text.splitlines()), label


def test_unknown_theme_is_an_error():
    with pytest.raises(ThemeError):
        find_theme("no-such-theme")


def test_repo_resolves_its_theme_and_overrides(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "blog", "default", str(tmp_path / "site"), cwd=tmp_path, home=home).returncode == 0
    config = tmp_path / "site" / "config" / "repo.json"
    overrides = tmp_path / "site" / "overrides" / "templates"
    overrides.mkdir(parents=True)
    (overrides / "HTML_FOOTER.tpl").write_text("<footer></footer>", encoding="utf-8")
    result = run_kb4it("theme-info", "--repo", str(config), "--json", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    info = json.loads(result.stdout[result.stdout.index("{"):])
    assert info["id"] == "blog"
    assert {t["name"]: t["origin"] for t in info["templates"]}["HTML_FOOTER"] == "repo"


def test_cli_refuses_without_a_theme(tmp_path):
    result = run_kb4it("theme-info", cwd=tmp_path, home=tmp_path)
    assert result.returncode == 1
