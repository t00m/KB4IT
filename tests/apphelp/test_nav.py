from apphelp_meta import Page
from apphelp_nav import build_sections, flatten, neighbours, related_pages


def p(doc, section, order, features=(), keywords=(), tags=(), related=()):
    return Page(doc_id=doc, title=doc, kind="howto", section=section, order=order, summary="",
                features=list(features), keywords=list(keywords), tags=list(tags), related=list(related))


PAGES = [p("c.md", "How-to", 120), p("a.md", "Start", 10), p("b.md", "How-to", 110),
         p("d.md", "Start", 20), p("e.md", "Help", 410)]


def test_sections_ordered_by_lowest_order():
    sections = build_sections(PAGES)
    assert [(name, [x.doc_id for x in entries]) for name, entries in sections] == [
        ("Start", ["a.md", "d.md"]), ("How-to", ["b.md", "c.md"]), ("Help", ["e.md"])]


def test_neighbours_cross_sections():
    flat = flatten(build_sections(PAGES))
    prev, nxt = neighbours(flat, "d.md")
    assert (prev.doc_id, nxt.doc_id) == ("a.md", "b.md")
    assert neighbours(flat, "a.md")[0] is None
    assert neighbours(flat, "e.md")[1] is None
    assert neighbours(flat, "missing.md") == (None, None)


def test_related_scoring_and_forced_first():
    me = p("me.md", "How-to", 1, features=["Backup"], keywords=["copy"], related=["z.md"])
    others = [me,
              p("x.md", "Help", 5, features=["Backup"]),
              p("y.md", "How-to", 6, keywords=["copy"]),
              p("z.md", "Help", 7),
              p("w.md", "Help", 8)]
    assert [x.doc_id for x in related_pages(me, others)] == ["z.md", "x.md", "y.md"]


def test_related_limit():
    me = p("me.md", "S", 1, features=["F"])
    others = [me] + [p(f"{i}.md", "S", i, features=["F"]) for i in range(10)]
    assert len(related_pages(me, others)) == 5


def test_related_repeated_page_is_listed_once():
    me = p("me.md", "S", 1, related=["z.md", "z.md"])
    assert [x.doc_id for x in related_pages(me, [me, p("z.md", "S", 2)])] == ["z.md"]
