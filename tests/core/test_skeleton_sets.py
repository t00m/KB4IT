"""Skeleton sets are looked up in overrides, theme and common templates (ET-05)."""

import json
import logging
import re

import pytest

from kb4it.core.env import ENV
from kb4it.core.exceptions import ThemeError
from kb4it.services.addpage import AddPageMixin
from tests.helpers import ROOT

TECHDOC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "templates"


class _Srvbes:
    def __init__(self, overrides, templates):
        self.overrides_dir = overrides
        self._runtime = {"theme": {"templates": str(templates)}}

    def get_dict(self, name):
        return self._runtime if name == "runtime" else {}


class _Builder(AddPageMixin):
    def __init__(self, overrides, templates, log):
        self.srvbes = _Srvbes(overrides, templates)
        self.log = log


@pytest.fixture
def make(tmp_path, caplog):
    caplog.set_level(logging.INFO)

    def _make(overrides=None, templates=TECHDOC):
        return _Builder(str(overrides) if overrides else None, templates, logging.getLogger("test"))
    return _make


def _folder(base, files, listing=None):
    folder = base / "skeletons"
    folder.mkdir(parents=True)
    for name, text in files.items():
        (folder / name).write_text(text, encoding="utf-8")
    if listing is not None:
        text = listing if isinstance(listing, str) else json.dumps(listing)
        (folder / "skeletons.json").write_text(text, encoding="utf-8")
    return folder


def test_theme_set_with_json(make):
    source, cats = make().skeleton_set()
    assert source == "theme"
    assert [c["id"] for c in cats] == ["change", "incident", "meeting", "note", "post", "procedure", "report", "task"]
    tpl = (TECHDOC / "PAGE_ADD.tpl").read_text(encoding="utf-8")
    for c in cats:
        m = re.search(r"\{'id': '%s',\s+'name': '([^']*)',\s+'icon': '([^']*)',\s+'color': '([^']*)',\s+'desc': '([^']*)'" % c["id"], tpl)
        assert (c["name"], c["icon"], c["color"], c["description"]) == m.groups()
        assert c["text"].strip()


def test_set_without_json(make, tmp_path):
    _folder(tmp_path / "tpl", {"B-SKELETON.md": "b", "A-SKELETON.md": "a"})
    source, cats = make(templates=tmp_path / "tpl").skeleton_set()
    assert source == "theme"
    assert [(c["id"], c["name"], c["description"], c["text"]) for c in cats] == [("a", "A", "", "a"), ("b", "B", "", "b")]
    assert cats[0]["color"] == "" and cats[0]["icon"] == ""


def test_overrides_win_and_do_not_merge(make, tmp_path):
    _folder(tmp_path / "ov" / "templates", {"ONLY-SKELETON.md": "x"})
    source, cats = make(overrides=tmp_path / "ov").skeleton_set()
    assert source == "overrides"
    assert [c["id"] for c in cats] == ["only"]


def test_empty_overrides_fall_through(make, tmp_path):
    (tmp_path / "ov" / "templates" / "skeletons").mkdir(parents=True)
    source, cats = make(overrides=tmp_path / "ov").skeleton_set()
    assert source == "theme" and len(cats) == 8


def test_common_fallback(make, tmp_path):
    (tmp_path / "tpl").mkdir()
    source, cats = make(templates=tmp_path / "tpl").skeleton_set()
    assert source == "common"
    assert [c["id"] for c in cats] == ["document"]
    assert (ROOT / "kb4it/resources/common/templates/skeletons/DOCUMENT-SKELETON.md").is_file()
    assert ENV["GPATH"]["TEMPLATES"]


def test_bad_id(make, tmp_path):
    folder = _folder(tmp_path / "tpl", {"BAD_ID-SKELETON.md": "x"}, [{"id": "Bad_Id"}])
    with pytest.raises(ThemeError, match=re.escape(str(folder / "skeletons.json"))):
        make(templates=tmp_path / "tpl").skeleton_set()


def test_listed_file_missing(make, tmp_path):
    folder = _folder(tmp_path / "tpl", {"A-SKELETON.md": "x"}, [{"id": "a"}, {"id": "gone"}])
    with pytest.raises(ThemeError, match=re.escape(str(folder / "skeletons.json"))):
        make(templates=tmp_path / "tpl").skeleton_set()


def test_invalid_json(make, tmp_path):
    folder = _folder(tmp_path / "tpl", {"A-SKELETON.md": "x"}, "{not json")
    with pytest.raises(ThemeError, match=re.escape(str(folder / "skeletons.json"))):
        make(templates=tmp_path / "tpl").skeleton_set()


def test_unlisted_file_logged(make, tmp_path, caplog):
    _folder(tmp_path / "tpl", {"A-SKELETON.md": "x", "EXTRA-SKELETON.md": "y"}, [{"id": "a"}])
    _, cats = make(templates=tmp_path / "tpl").skeleton_set()
    assert [c["id"] for c in cats] == ["a"]
    assert "[BUILDER] SKELETON_UNLISTED file=EXTRA-SKELETON.md" in caplog.text


def test_skeleton_text_utf8(make, tmp_path):
    text = "# ñandú 日本\n"
    _folder(tmp_path / "tpl", {"A-SKELETON.md": text})
    _, cats = make(templates=tmp_path / "tpl").skeleton_set()
    assert cats[0]["text"] == text
