"""collect_stats() on a small database: what the stats page shows."""

from kb4it.services.themekit.stats import LIST_LIMIT, collect_stats


class FakeDB:
    """The part of the Database service collect_stats reads."""

    def __init__(self, docs):
        self.db = docs

    def get_documents(self):
        return list(self.db)

    def is_system(self, doc):
        return "SystemPage" in self.db[doc]

    def get_values(self, doc, key):
        return self.db[doc].get(key, [""])

    def get_doc_timestamp(self, doc):
        return self.db[doc].get("Date", [None])[0]

    def get_doc_keys(self, doc):
        return sorted(self.db[doc])


def make_db():
    return FakeDB({
        "a.md": {"Title": ["Alpha"], "Date": ["2025-03-02"], "Tag": ["linux", "backup"], "OS": ["Linux"],
                 "Bookmark": ["Yes"]},
        "b.md": {"Title": ["Beta"], "Date": ["2025-01-10"], "Tag": ["Linux"], "OS": ["Linux"]},
        "c.md": {"Title": ["Gamma"], "Date": ["2023-07-01"], "Tag": ["backup"], "Team": ["Basis"]},
        "d.md": {"Title": ["Delta"], "Tag": ["SAP  basis", "sap basis"]},
        "stats.md": {"Title": ["Stats"], "SystemPage": ["Yes"], "Tag": ["x"]},
    })


def test_totals_leave_out_system_pages():
    s = collect_stats(make_db(), ["OS", "Tag", "Team"], {})
    assert (s.documents, s.properties, s.bookmarks, s.links) == (4, 3, 1, 0)
    assert s.values == 1 + 5 + 1  # OS: Linux; Tag: linux, Linux, backup, SAP  basis, sap basis; Team: Basis
    assert s.dated_pct == 75 and s.undated == 1


def test_activity_by_year_and_month():
    s = collect_stats(make_db(), ["Tag"], {}, events={2025: {3: {}}})
    assert (s.oldest, s.newest) == ("2023-07-01", "2025-03-02")
    assert [(b.label, b.count, b.url) for b in s.years] == [("2025", 2, "events_2025.html"), ("2023", 1, "")]
    assert len(s.months) == 12 and s.months[-1].label == "2025-03" and s.months[0].label == "2024-04"
    assert s.months[-1].url == "events_202503.html" and s.months[-3].url == ""
    assert [b.count for b in s.months[-3:]] == [1, 0, 1]  # January, an empty February, March
    assert s.months[-2].pct == 0 and s.months[-1].pct == 100


def test_coverage_sorted_by_documents_with_top_values():
    s = collect_stats(make_db(), ["OS", "Tag", "Team", "Missing"], {})
    assert [(r.key, r.docs, r.pct, r.values) for r in s.coverage] == [
        ("Tag", 4, 100, 5), ("OS", 2, 50, 1), ("Team", 1, 25, 1)]
    top = s.coverage[0].top
    assert [(v.value, v.count) for v in top] == [("backup", 2), ("Linux", 1), ("linux", 1)]
    assert top[0].url == "Tag_backup.html"


def test_metadata_health():
    s = collect_stats(make_db(), ["OS", "Tag", "Team"], {})
    groups = {(g.key, tuple(v.value for v in g.values)) for g in s.duplicates.items}
    assert groups == {("Tag", ("Linux", "linux")), ("Tag", ("SAP  basis", "sap basis"))}
    assert [(r.key, r.doc.title) for r in s.rare_keys.items] == [("Team", "Gamma")]
    assert [(d.title, d.count) for d in s.sparse_docs.items] == [("Delta", 1)]  # the others have three or more


def test_links():
    backlinks = {"a.md": [["Beta", "b.md"], ["Gamma", "c.md"]], "b.md": [["Alpha", "a.md"]],
                 "c.md": [["Stats", "stats.md"]], "gone.md": [["Alpha", "a.md"]]}
    s = collect_stats(make_db(), ["Tag"], backlinks)
    assert s.links == 3  # the system page and the missing target do not count
    assert [(d.title, d.count) for d in s.most_linked] == [("Alpha", 2), ("Beta", 1)]
    assert [d.title for d in s.orphans.items] == ["Delta", "Gamma"]
    assert s.no_outgoing == 1  # Delta


def test_long_lists_are_capped():
    docs = {f"d{n:02d}.md": {"Title": [f"Doc {n:02d}"], f"Key{n:02d}": ["v"]} for n in range(LIST_LIMIT + 3)}
    s = collect_stats(FakeDB(docs), [f"Key{n:02d}" for n in range(LIST_LIMIT + 3)], {})
    assert len(s.rare_keys.items) == LIST_LIMIT and s.rare_keys.more == 3
    assert len(s.sparse_docs.items) == LIST_LIMIT and s.sparse_docs.more == 3
    assert s.years == [] and s.months == [] and s.undated == LIST_LIMIT + 3
