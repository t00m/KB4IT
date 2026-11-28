"""Related kit (themekit/related.py): related documents by shared, rare property values."""

from kb4it.services.themekit import related

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


def test_related_docs_use_the_theme_candidates():
    from types import SimpleNamespace

    class _Db:
        values = {"a.md": {"SID": ["BWP"]}, "b.md": {"SID": ["BWP"]}, "c.md": {"SID": ["BWP"]}}

        def get_documents(self):
            return list(self.values)

        def is_system(self, doc):
            return False

        def get_values(self, doc, key):
            return self.values[doc].get(key, [])

    class _Theme(related.RelatedMixin):
        def related_candidates(self):
            return [d for d in super().related_candidates() if d != "c.md"]

    theme = _Theme()
    theme.srvdtb, theme.srvbes = _Db(), SimpleNamespace(get_plan=lambda: "plan")
    assert [r["doc"] for r in theme.related_docs("a.md")] == ["b.md"]
    assert theme.related_docs("c.md") == []
