from apphelp_config import DEFAULT_LABELS, load_config

from kb4it.core.env import ENV


def test_defaults():
    config = load_config({"title": "X"})
    assert config.strict is True
    assert config.lang == "en"
    assert config.accent == "#3584e4"
    assert config.about is False
    assert config.contract == "config/contract.txt"
    assert config.vocabulary == {}
    assert config.labels == DEFAULT_LABELS
    assert config.version == ""


def test_overrides():
    config = load_config({"version": "0.5", "apphelp": {
        "strict": False, "lang": "es", "accent": "#26a269", "about": True,
        "contract": "help/ids.txt", "vocabulary": {"Feature": ["Backup"]},
        "labels": {"search": "Buscar", "unknown_label": "ignored"},
    }})
    assert (config.strict, config.lang, config.accent, config.about) == (False, "es", "#26a269", True)
    assert config.contract == "help/ids.txt"
    assert config.vocabulary == {"Feature": ["Backup"]}
    assert config.labels["search"] == "Buscar"
    assert "unknown_label" not in config.labels
    assert config.version == "0.5"


def test_bad_accent_falls_back():
    assert load_config({"apphelp": {"accent": "red; } body { display:none"}}).accent == "#3584e4"


def test_accent_accepts_only_exact_hex_forms():
    for bad in ("#12345", "#fff\n", "#1234567", "#ggg"):
        assert load_config({"apphelp": {"accent": bad}}).accent == "#3584e4"
    for good in ("#fff", "#ffff", "#ffffff", "#ffffffff"):
        assert load_config({"apphelp": {"accent": good}}).accent == good


def test_missing_or_null_version_is_empty():
    assert load_config({}).version == ""
    assert load_config({"version": None}).version == ""


def test_version_token_is_the_kb4it_version():
    assert load_config({"version": "kb4it"}).version == ENV["APP"]["version"]


def test_plain_version_is_kept():
    assert load_config({"version": "2.1"}).version == "2.1"


def test_helpconfig_is_the_theme_config_class():
    from kb4it.core.themeconfig import build_config
    from kb4it.core.themeload import load_module
    from tests.helpers import ROOT
    module = load_module(str(ROOT / "kb4it" / "resources" / "themes" / "apphelp" / "logic"), "apphelp")
    assert module.Theme.config_class.__name__ == "HelpConfig"
    HelpConfig = module.Theme.config_class
    repo = {"version": "0.5", "apphelp": {"strict": False, "versions": {"enabled": True}, "bogus": 1}}
    config, unknown = build_config(HelpConfig, {}, repo, "apphelp")
    assert unknown == ["bogus"]
    from dataclasses import asdict
    assert asdict(config) == asdict(load_config(repo))
    assert config.versions is True and config.strict is False and config.contract_explicit is False


def test_unknown_apphelp_key_is_logged(tmp_path, home):
    from tests.helpers import page, run_kb4it, write_repo
    pages = {"start.md": page("Start", "Text.", DocType="Tutorial", HelpId="start")}
    cfg = write_repo(tmp_path / "help", "apphelp", pages, apphelp={"strict": False, "bogus": 1})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "[FRONTEND] THEME_SETTING_UNKNOWN theme=apphelp key=bogus" in result.stdout
