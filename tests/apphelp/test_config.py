from apphelp_config import DEFAULT_LABELS, load_config


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
