"""Theme settings (P5): dataclass defaults, then theme.json, then the repo.json block named after the theme."""

from dataclasses import dataclass, field

import pytest

from kb4it.core.exceptions import ThemeError
from kb4it.core.themeconfig import ThemeSettings, build_config


@dataclass
class Small:
    toc_sidebar: bool = False
    depth: int = 2
    title: str = "x"
    groups: list = field(default_factory=list)
    tabs: dict = field(default_factory=dict)


def test_merge_order():
    config, unknown = build_config(Small, {"depth": 3, "title": "theme"}, {"small": {"title": "repo"}}, "small")
    assert (config.toc_sidebar, config.depth, config.title) == (False, 3, "repo")
    assert unknown == []


def test_theme_json_keys_that_are_not_fields_are_ignored():
    config, unknown = build_config(Small, {"id": "small", "version": "1.0.0"}, {}, "small")
    assert config == Small()
    assert unknown == []


def test_wrong_type_names_key():
    with pytest.raises(ThemeError, match="toc_sidebar"):
        build_config(Small, {}, {"small": {"toc_sidebar": "yes"}}, "small")


def test_bool_is_not_an_int():
    with pytest.raises(ThemeError, match="depth"):
        build_config(Small, {}, {"small": {"depth": True}}, "small")


def test_wrong_type_in_theme_json_names_key():
    with pytest.raises(ThemeError, match="groups"):
        build_config(Small, {"groups": "a"}, {}, "small")


def test_unknown_key_reported():
    config, unknown = build_config(Small, {}, {"small": {"tocsidebar": True, "toc_sidebar": True}}, "small")
    assert config.toc_sidebar is True
    assert unknown == ["tocsidebar"]


def test_block_that_is_not_an_object_raises():
    with pytest.raises(ThemeError, match="small"):
        build_config(Small, {}, {"small": ["toc_sidebar"]}, "small")


def test_from_settings_skips_the_type_check():
    @dataclass
    class Own:
        versions: bool = False
        SETTINGS_KEYS = ("versions", "labels")

        @classmethod
        def from_settings(cls, merged, repo):
            return cls(versions=bool((merged.get("versions") or {}).get("enabled")))

    config, unknown = build_config(Own, {}, {"own": {"versions": {"enabled": True}, "labels": {}, "x": 1}}, "own")
    assert config.versions is True
    assert unknown == ["x"]


def test_plain_settings_get():
    settings = ThemeSettings({"search": True, "quality": {"enabled": False}})
    assert settings.get("search") is True
    assert settings.get("missing", 5) == 5
    assert settings["quality"] == {"enabled": False}
    assert "search" in settings and "missing" not in settings
