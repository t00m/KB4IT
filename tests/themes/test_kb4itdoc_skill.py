"""The kb4itdoc skill shipped with KB4IT says what the techdoc skeletons and quality score do."""

import importlib.util
import json
import re
import sys

import pytest

from tests.helpers import ROOT

SKILL = ROOT / "kb4it" / "resources" / "skills" / "kb4itdoc" / "SKILL.md"
TECHDOC = ROOT / "kb4it" / "resources" / "themes" / "techdoc"
SKELETONS = TECHDOC / "templates" / "skeletons"
sys.path.insert(0, str(TECHDOC / "logic"))  # techdoc_quality imports techdoc_media
_spec = importlib.util.spec_from_file_location("techdoc_quality", TECHDOC / "logic" / "techdoc_quality.py")
quality = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quality)


def _text():
    return SKILL.read_text(encoding="utf-8")


def _rows(heading):
    # The cells of the first table after a heading, header and rule left out.
    section = _text().split(heading, 1)[1]
    table = re.search(r"((?:^\|.*\|\n)+)", section, re.MULTILINE).group(1).splitlines()[2:]
    return [[cell.strip().strip("`") for cell in row.strip("|").split("|")] for row in table]


def _front(name):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    front = dict(line.split(":", 1) for line in text.split("---")[1].strip().splitlines())
    sections = re.findall(r"^## +(.+?)\s*$", text, re.MULTILINE)
    return {k: v.strip() for k, v in front.items()}, sections


def test_skill_has_a_name_and_no_em_dash():
    text = _text()
    assert text.startswith("---\nname: kb4itdoc\n")
    assert "—" not in text


@pytest.mark.parametrize("row", _rows("### Skeleton overview"), ids=lambda row: row[0])
def test_skeleton_overview_matches_the_skeleton_files(row):
    name, category, worktype, doctype, status, priority, sections = row
    front, headings = _front(name.upper())
    assert (front["Category"], front["WorkType"], front["DocType"], front["Status"]) == (category, worktype, doctype, status)
    assert front.get("Priority", "none") == priority
    assert [s.strip() for s in sections.split(",")] == headings


def test_category_pairs_match_the_quality_profile():
    pairs = quality.DEFAULTS["work_categories"]
    for category, _use, worktypes in _rows("## 5. Category: Form of the Document"):
        for worktype in re.findall(r"`?(\w+)`?", worktypes.replace(" or ", ",")):
            assert category in pairs[worktype], (category, worktype)


def test_theme_json_lists_the_same_values_as_the_defaults():
    conf = json.loads((TECHDOC / "theme.json").read_text(encoding="utf-8"))["quality"]
    assert conf["known_values"] == quality.DEFAULTS["known_values"]
    assert conf["work_categories"] == quality.DEFAULTS["work_categories"]


def test_quality_section_names_every_core_key():
    section = _text().split("## 17. Quality Score", 1)[1]
    listed = re.search(r"The core keys are (.+?)\. ", section, re.DOTALL).group(1)
    assert sorted(re.findall(r"`(\w+)`", listed)) == sorted(quality.CORE_KEYS)
