"""repo.json hidden_properties: properties left out of the properties page only."""

import json

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.repocheck import _loaders
from kb4it.services.database import hidden_properties
from kb4it.services.themekit import DocumentTheme


class _Db:
    VALUES = {"Tag": ["a"], "Ticket": ["T-1", "T-2"], "Team": ["Linux"]}

    def __init__(self, ignored, hidden):
        self.ignored, self.hidden = ignored, hidden
        self.added = []

    def get_ignored_keys(self):
        return self.ignored

    def get_hidden_keys(self):
        return self.hidden

    def get_all_keys(self):
        return sorted(self.VALUES)

    def get_all_values_for_key(self, key):
        return self.VALUES[key]

    def get_docs_by_key_value(self, key, value):
        return [f"{key}-{value}.md"]

    def add_document(self, doc):
        self.added.append(doc)

    def add_document_key(self, doc, key, value):
        pass


class _Template:
    def render(self, var):
        return json.dumps(var)


class _Theme(DocumentTheme):
    properties_cloud = False

    def __init__(self, ignored=(), hidden=()):  # no services: only what build_page_properties uses
        self.srvdtb = _Db(list(ignored), list(hidden))
        self.pages = {}

    def template(self, name):
        return _Template()

    def get_theme_var(self):
        return {}

    def distribute_md(self, name, content, listing=False):
        self.pages[name] = json.loads(content)


def _listed(theme):
    theme.build_page_properties()
    return [item["key"] for item in theme.pages["properties"]["keys"]]


def test_every_property_is_listed_by_default():
    assert _listed(_Theme()) == ["Tag", "Team", "Ticket"]


def test_hidden_and_ignored_properties_are_left_out():
    assert _listed(_Theme(hidden=["Ticket"])) == ["Tag", "Team"]
    assert _listed(_Theme(ignored=["Team"], hidden=["Ticket"])) == ["Tag"]


def test_hidden_properties_setting():
    assert hidden_properties({}) == []
    assert hidden_properties({"hidden_properties": ["Ticket"]}) == ["Ticket"]


@pytest.mark.parametrize("value", ["Ticket", [1], {"Ticket": True}])
def test_hidden_properties_must_be_a_list_of_names(value):
    with pytest.raises(ConfigError, match="hidden_properties"):
        hidden_properties({"hidden_properties": value})
    assert any("hidden_properties" in problem for problem in _loaders({"hidden_properties": value}))
