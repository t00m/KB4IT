"""Author profiles: the repo.json "people" block, the profile registry and its rules."""

import json
import re

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.people import PeopleSettings, load_people
from tests.helpers import page, run_kb4it, write_repo


def test_defaults():
    assert load_people({}) == PeopleSettings()
    assert PeopleSettings().keys == ("Author",)
    assert PeopleSettings().contact_keys == ("Email", "Phone", "Chat", "Url")
    assert PeopleSettings().private == ()


def test_values_are_read():
    settings = load_people({"people": {"keys": ["Author", "Owner"], "private": ["Phone"]}})
    assert settings.keys == ("Author", "Owner") and settings.private == ("Phone",)


@pytest.mark.parametrize("block, words", [
    ([], "must be an object"),
    ({"map": {}}, "unknown key 'map'"),
    ({"keys": "Author"}, "'people.keys' must be a list"),
    ({"keys": []}, "'people.keys' must name at least one key"),
    ({"keys": ["Title"]}, "Title is a KB4IT key"),
    ({"keys": ["Person"]}, "Person is reserved"),
    ({"contact_keys": [""]}, "'people.contact_keys' must be a list of key names"),
    ({"private": ["Person"]}, "Person is reserved"),
])
def test_bad_values(block, words):
    with pytest.raises(ConfigError, match=re.escape(words)):
        load_people({"people": block})


def test_people_setting_rebuilds_every_page(tmp_path, home):
    pages = {"a.md": page("Alpha", Author="Jane Doe", Category="Note", DocType="Reference", Tag="x")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["people"] = {"keys": ["Author", "Owner"]}
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "CORE_SIGNATURE_CHANGED" in result.stdout
