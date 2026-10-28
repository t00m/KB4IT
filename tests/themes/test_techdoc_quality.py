"""techdoc techdoc_quality.py: the score of one document and the peer statistics."""

import importlib.util
import re
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
    body = "# T\n\n## Introduction\n\n## Steps\n\n1. Describe the first step.\n2. b\n3. c\n"
    total = sum(c.points for c in quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons))
    # Procedure skeleton: Introduction, Prerequisites, Steps, Verification (2 of 4 found); one empty section; skeleton text.
    assert total == pytest.approx(max(0, 5 + 4 + 8 + 8 * 2 / 4 - 3 - 6))


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


def test_peer_stats_ranks_within_peers_and_skips_retired():
    A = quality.Assessment
    dims = lambda v: {k: v for k in ("findable", "structured", "complete", "connected", "current")}
    stats = quality.peer_stats({"a.md": A(80, "exemplary", dims(16), [], "Reference"),
                                "b.md": A(50, "basic", dims(10), [], "Reference"),
                                "c.md": A(0, "retired", dims(0), [], "Reference"),
                                "d.md": A(62, "complete", dims(12), [], "Change")})
    assert stats["peers"]["Reference"]["count"] == 2 and stats["peers"]["Change"]["count"] == 1
    assert stats["docs"]["a.html"]["rank"] == 1 and stats["docs"]["b.html"]["rank"] == 2
    assert stats["docs"]["d.html"]["rank"] == 1 and stats["peers"]["Change"]["median"]["findable"] == 12
    assert "c.html" not in stats["docs"]
    assert quality.index_js(stats).startswith("window.KB_QUALITY = {")


def test_every_check_has_a_guide_entry_and_a_tip(prof, skeletons, doc):
    sys.path.insert(0, str(LOGIC))
    import techdoc_quality_guide as guide
    body = "# T\n\n## Summary\n\nX.\n\n## Empty\n\n## Root Cause\n\nY [gone](gone.md) ![i](resources/images/none.png)\n"
    docs = [doc(body, work_type="Incident", Status="Open"), doc(body, DocType="Tutorial", Category="Note", Date="soon"),
            doc("# T\n", DocType="Reference", Category="Procedure", Status="Released", Date="2010-01-01")]
    for d in docs:
        for check in quality.assess(d, prof, skeletons, date(2026, 10, 24)).checks:
            assert check.key in guide.CHECKS, check.name
            assert check.tip, check.name


def test_skeleton_section_tip_shows_the_markdown(prof, skeletons, doc):
    checks = quality.structured(doc("# T\n\n## Summary\n\nX.\n", work_type="Incident"), prof, skeletons)
    timeline = next(c for c in checks if c.name == "Timeline section")
    assert timeline.key == "check-skeleton-section" and "## Timeline" in timeline.tip and "incident" in timeline.tip.lower()


def _filled(name, text, skeleton):
    # The skeleton as an author would finish it: keys set, example lines replaced, a final status.
    sentence = " ".join(["The service account renews the certificate and the team checks the log afterwards."] * 6)
    for line in skeleton.placeholders:
        text = text.replace(line, sentence)
    record = "\nWorkType:" in text
    keys = {"Author": "Ana", "Date": "2026-10-20", "Tag": "renewal", "Topic": "Security", "Scope": "Infrastructure",
            "Product": "ADS", "Summary": "Renew the certificate.", "Status": "Completed" if record else "Released"}
    for key, value in keys.items():
        text = re.sub(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.MULTILINE)
    meta = {}
    for line in text.split("\n---", 1)[0].splitlines()[1:]:
        key, _, value = line.partition(":")
        if value.strip():
            meta[key.strip()] = [v.strip() for v in value.split(",")]
    work = (meta.get("WorkType") or [""])[0]
    return quality.DocInput(text=text, meta=meta, backlinks=0, known_docs=set(), source_dir="/nonexistent", work_type=work)


@pytest.mark.parametrize("name", ["CHANGE", "INCIDENT", "MEETING", "NOTE", "POST", "PROCEDURE", "REPORT", "TASK"])
def test_a_filled_skeleton_meets_the_quality_standard(prof, skeletons, name):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    a = quality.assess(_filled(name, text, skeletons[name]), prof, skeletons, date(2026, 10, 24))
    missing = [c.todo for c in a.checks if not c.passed and c.dim in ("findable", "structured")]
    assert a.dims["findable"] == 15 and a.dims["structured"] == 25, missing
    assert a.tier == "exemplary", (a.score, a.dims)


@pytest.mark.parametrize("name", ["CHANGE", "INCIDENT", "MEETING", "NOTE", "POST", "PROCEDURE", "REPORT", "TASK"])
def test_an_untouched_skeleton_is_flagged(prof, skeletons, name, doc):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    checks = quality.structured(doc(text, work_type="Incident" if name == "INCIDENT" else "", Category=name.capitalize()),
                                prof, skeletons)
    assert any(c.key == "check-skeleton-text" for c in checks)


def test_a_references_heading_in_a_skeleton_is_scored_under_connected_only(prof, doc, tmp_path):
    (tmp_path / "X-SKELETON.md").write_text("---\nCategory: X\n---\n\n# T\n\n## Overview\n\nA b c d.\n\n## References\n\n- link\n",
                                            encoding="utf-8")
    checks = quality.structured(doc("# T\n\n## Overview\n\nText.\n", Category="X"), prof, quality.load_skeletons(str(tmp_path)))
    assert not any(c.name == "References section" for c in checks)


def test_a_link_to_a_profile_is_neither_broken_nor_a_related_document(prof, tmp_path):
    body = "# T\n\nAsk [Jane](PERSON-JANE.md).\n"
    profile_link = quality.DocInput(text=body, meta={}, backlinks=0, known_docs={"a.md"}, source_dir=str(tmp_path),
                                    profile_docs={"PERSON-JANE.md"})
    checks = quality.connected(profile_link, prof)
    assert not [c for c in checks if c.key == "check-broken-link"]
    assert next(c for c in checks if c.key == "check-internal-link").points == 0
