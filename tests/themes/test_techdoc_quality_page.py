"""techdoc techdoc_quality_page.py: quick wins, possible duplicates and the tier mix."""

import importlib.util
import sys

from tests.helpers import ROOT

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
sys.path.insert(0, str(LOGIC))
_spec = importlib.util.spec_from_file_location("techdoc_quality_page", LOGIC / "techdoc_quality_page.py")
qpage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qpage)
import techdoc_quality as quality

DIMS = {k: 0 for k in quality.DIMENSIONS}


def check(points, maximum, todo):
    return quality.Check("findable", todo, todo, points, maximum, "check-summary", "tip")


def test_quick_wins_need_one_check_that_reaches_the_next_tier():
    prof = quality.profile({})
    a = {"near.md": quality.Assessment(57, "basic", DIMS, [check(0, 3, "Add a Summary key"), check(0, 1, "Add the Tag key")], "Reference"),
         "short.md": quality.Assessment(57, "basic", DIMS, [check(0, 1, "Add the Tag key")], "Reference"),
         "far.md": quality.Assessment(50, "basic", DIMS, [check(0, 25, "Write more")], "Reference"),
         "top.md": quality.Assessment(90, "exemplary", DIMS, [], "Reference")}
    wins = qpage.quick_wins(a, prof)
    assert [(w["doc"], w["check"], w["missing"], w["next"]) for w in wins] == [("near.md", "Add a Summary key", 3, "complete")]


def test_duplicates_skip_journal_series():
    titles = {"a.md": "Renew the ReaderRights credential in ADS", "b.md": "Renew the ReaderRights credential in ADS now",
              "c.md": "SAP Basis notes on Friday, July 02, 2021", "d.md": "SAP Basis notes on Friday, July 09, 2021",
              "e.md": "Something else entirely"}
    pairs = qpage.duplicates(titles)
    assert [(p[0], p[1]) for p in pairs] == [("a.md", "b.md")]


def test_tier_mix_counts_live_documents_per_peer():
    a = {"1.md": quality.Assessment(80, "exemplary", DIMS, [], "Reference"),
         "2.md": quality.Assessment(50, "basic", DIMS, [], "Reference"),
         "3.md": quality.Assessment(0, "retired", DIMS, [], "Reference")}
    mix = qpage.tier_mix(a)
    assert mix == [{"peer": "Reference", "total": 2, "counts": {"exemplary": 1, "complete": 0, "basic": 1, "stub": 0},
                    "pct": {"exemplary": 50.0, "complete": 0.0, "basic": 50.0, "stub": 0.0}}]
