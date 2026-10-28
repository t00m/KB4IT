"""ET-08, ET-09: blog and bookshelf get the Add page when the editor is on."""

import json
import re
from pathlib import Path

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo

THEMES = Path(__file__).resolve().parents[2] / "kb4it" / "resources" / "themes"
DOCS = {"note.md": page("Note", Category="Post", Date="2026-10-01")}
DIALOG = {"blog": "modal-add-post", "bookshelf": "modal-add-chapter"}
SKELETON = {
    "blog": ("POST", ["Author", "Category: Post", "Date", "Tag", "Topic"]),
    "bookshelf": ("CHAPTER", ["Author", "Book", "Part", "Chapter", "Date", "Status"]),
}


@pytest.fixture()
def home(tmp_path):
    path = tmp_path / "home"
    path.mkdir()
    return path


def build(base, home, theme, **conf):
    cfg = write_repo(base, theme, DOCS, **{**_app_conf(theme), **conf})
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return base / "target"


@pytest.mark.parametrize("theme", ["blog", "bookshelf"])
def test_on_builds_page_and_link(tmp_path, home, theme):
    target = build(tmp_path, home, theme, editor=True)
    add = (target / "add.html").read_text(encoding="utf-8")
    assert len(re.findall(r'<dialog[^>]*id="modal-add-(?!_edit")', add)) == 2  # one card and the Person profile, plus the Edit dialog
    assert 'id="modal-add-_edit"' in add
    assert f'id="{DIALOG[theme]}"' in add
    assert 'href="add.html"' in (target / "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("theme", ["blog", "bookshelf"])
def test_off_by_default(tmp_path, home, theme):
    target = build(tmp_path, home, theme)
    assert not (target / "add.html").exists()
    assert 'href="add.html"' not in (target / "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("theme", ["blog", "bookshelf"])
def test_skeleton_keys(theme):
    prefix, keys = SKELETON[theme]
    text = (THEMES / theme / "templates" / "skeletons" / f"{prefix}-SKELETON.md").read_text(encoding="utf-8")
    front = text.split("---")[1]
    names = [line.split(":")[0] for line in front.splitlines() if line.strip()]
    for key in keys:
        assert key.split(":")[0] in names
    if theme == "blog":
        assert "Category: Post" in front
    assert re.search(r"^Date: YYYY-MM-DD$", front, re.M)


def test_kb4it_floor():
    paths = sorted(THEMES.glob("*/theme.json"))
    assert len(paths) == 4
    for path in paths:
        assert json.loads(path.read_text(encoding="utf-8"))["kb4it"] == ">=0.10.0", path
