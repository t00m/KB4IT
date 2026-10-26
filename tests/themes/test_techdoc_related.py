"""techdoc techdoc_related.py: related documents by shared, rare property values."""

import importlib.util

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location(
    "techdoc_related", ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic" / "techdoc_related.py")
related = importlib.util.module_from_spec(spec)
spec.loader.exec_module(related)

META = {"a.md": {"SID": ["BWP"], "Tag": ["x"]}, "b.md": {"SID": ["BWP"]}, "c.md": {"Tag": ["x"]},
        "d.md": {"Tag": ["x"]}, "e.md": {"Tag": ["y"], "Author": ["Ana"]}}


def test_a_rare_shared_value_ranks_first():
    found = related.related("a.md", META)
    assert [r["doc"] for r in found] == ["b.md", "c.md", "d.md"]
    assert found[0]["shared"] == ["SID: BWP"]


def test_no_shared_value_gives_nothing_and_other_keys_do_not_count():
    assert related.related("e.md", META) == []


def test_limit():
    meta = {f"{i}.md": {"Tag": ["x"]} for i in range(9)}
    assert len(related.related("0.md", meta)) == 5


def test_shared_values_are_grouped_by_key():
    meta = {"a.md": {"Tag": ["form", "pdf"], "SID": ["BJP"]}, "b.md": {"Tag": ["form", "pdf"], "SID": ["BJP"]}}
    assert related.related("a.md", meta)[0]["shared"] == ["SID: BJP", "Tag: form, pdf"]
