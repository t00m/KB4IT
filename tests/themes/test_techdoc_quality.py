"""techdoc techdoc_quality.py: the score of one document and the peer statistics."""

import importlib.util
import sys
from datetime import date

import pytest

from tests.helpers import ROOT

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
SKELETONS = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "templates" / "skeletons"
sys.path.insert(0, str(LOGIC))  # techdoc_quality imports techdoc_media
_spec = importlib.util.spec_from_file_location("techdoc_quality", LOGIC / "techdoc_quality.py")
quality = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quality)


@pytest.fixture
def prof():
    return quality.profile({})


@pytest.fixture
def skeletons():
    return quality.load_skeletons(str(SKELETONS))


@pytest.fixture
def doc(tmp_path):
    def make(text, work_type="", backlinks=0, **meta):
        return quality.DocInput(text=text, meta={k: [v] for k, v in meta.items()}, backlinks=backlinks,
                                known_docs={"a.md", "b.md"}, source_dir=str(tmp_path), work_type=work_type)
    return make


def test_findable_counts_core_keys_known_values_and_summary(prof, doc):
    full = doc("# T\n", Author="A", Date="2026-01-01", DocType="How-to guide", Category="Procedure", Status="Released",
               Tag="x", Topic="y", Scope="z", Product="p", Summary="S")
    assert sum(c.points for c in quality.findable(full, prof)) == 15
    assert sum(c.points for c in quality.findable(doc("# T\n", Status="Whatever"), prof)) == 1


def test_structured_how_to_with_skeleton_sections(prof, skeletons, doc):
    body = "# T\n\n## Introduction\n\nWhy.\n\n## Prerequisites\n\nA.\n\n## Steps\n\n1. a\n2. b\n3. c\n\n## Verification\n\nOk.\n"
    checks = quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons)
    assert sum(c.points for c in checks) == 25


def test_structured_record_uses_worktype_skeleton_times_16(prof, skeletons, doc):
    body = "# T\n\n## Overview\n\nX.\n\n## Impact\n\nY.\n\n## Rollback\n\nZ.\n"
    checks = quality.structured(doc(body, work_type="Change", Category="Record"), prof, skeletons)
    assert sum(c.points for c in checks) == 25 and not any(c.name.startswith("Fits") for c in checks)


def test_empty_sections_and_placeholders_cost_points(prof, skeletons, doc):
    body = "# T\n\n## Introduction\n\n## Steps\n\n1. Step one\n2. Step two\n3. Step three\n"
    total = sum(c.points for c in quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons))
    assert total == pytest.approx(max(0, 5 + 4 + 8 + 8 * 1 / 3 - 3 - 6))


def test_almost_empty_document_does_not_raise(prof, skeletons, doc):
    d = doc("# T\n", Category="Note")
    assert quality.findable(d, prof) and quality.structured(d, prof, skeletons)


def test_complete_is_capped_for_short_documents(prof, doc):
    words = lambda n: "# T\n\n" + " ".join(["w"] * n) + "\n"
    assert sum(c.points for c in quality.complete(doc(words(40), DocType="How-to guide"), prof)) == 3
    assert sum(c.points for c in quality.complete(doc(words(75), DocType="How-to guide"), prof)) == 12.5
    assert sum(c.points for c in quality.complete(doc(words(300), DocType="How-to guide"), prof)) == 25
    assert sum(c.points for c in quality.complete(doc(words(30), work_type="Change"), prof)) == 12.5


def test_connected_rewards_links_and_penalises_broken_ones(prof, doc):
    body = "# T\n\nSee [b](b.md), [gone](gone.md), [web](https://x.org) and ![i](resources/images/none.png).\n\n## References\n\nx\n"
    points = sum(c.points for c in quality.connected(doc(body, backlinks=2), prof))
    assert points == max(0, 4 + 3 + 3 + 3 + 2 - 3 - 3)


def test_current_decays_with_age_and_tolerates_bad_dates(prof, doc):
    today = date(2026, 10, 24)
    fresh = quality.current(doc("# T\n", DocType="Reference", Status="Released", Date="2026-10-24"), prof, today)
    old = quality.current(doc("# T\n", DocType="Reference", Status="Released", Date="2018-10-24"), prof, today)
    bad = quality.current(doc("# T\n", DocType="Reference", Status="Draft", Date="soon"), prof, today)
    assert sum(c.points for c in fresh) == 20
    assert round(sum(c.points for c in old), 1) == 11.0          # 8 + 12 * 0.5 ** 2
    assert sum(c.points for c in bad) == 3
    assert sum(c.points for c in quality.current(doc("# T\n", work_type="Incident", Status="Open"), prof, today)) == 10


def test_assess_gives_tier_and_peer(prof, skeletons, doc):
    a = quality.assess(doc("# T\n", Status="Obsolete", DocType="Reference"), prof, skeletons, date(2026, 10, 24))
    assert a.tier == "retired" and a.peer == "Reference"
    assert quality.assess(doc("# T\n", work_type="Change"), prof, skeletons, date(2026, 10, 24)).peer == "Change"
    assert quality.tier_of(75, [], prof) == "exemplary" and quality.tier_of(74, [], prof) == "complete"
    assert quality.tier_of(40, [], prof) == "basic" and quality.tier_of(39, [], prof) == "stub"
