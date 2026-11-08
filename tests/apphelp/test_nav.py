from apphelp_meta import Page
import apphelp_nav
from apphelp_nav import build_sections, flatten, related_pages


def p(doc, section, order, features=(), keywords=(), tags=(), related=()):
    return Page(doc_id=doc, title=doc, doctype="howto", section=section, order=order, summary="",
                features=list(features), keywords=list(keywords), tags=list(tags), related=list(related))


PAGES = [p("c.md", "How-to", 120), p("a.md", "Start", 10), p("b.md", "How-to", 110),
         p("d.md", "Start", 20), p("e.md", "Help", 410)]


def test_sections_ordered_by_lowest_order():
    sections = build_sections(PAGES)
    assert [(name, [x.doc_id for x in entries]) for name, entries in sections] == [
        ("Start", ["a.md", "d.md"]), ("How-to", ["b.md", "c.md"]), ("Help", ["e.md"])]


def test_neighbours_cross_sections():
    """apphelp's reading order is every page, section by section, through the navigation kit."""
    from tests.apphelp.test_search_index import _apphelp_theme_class
    theme_class = _apphelp_theme_class()
    theme = theme_class.__new__(theme_class)
    theme.flat = flatten(build_sections(PAGES))
    assert theme.neighbours("d.md") == ("a.md", "b.md")
    assert theme.neighbours("a.md")[0] is None
    assert theme.neighbours("e.md")[1] is None
    assert theme.neighbours("missing.md") == (None, None)
    assert not hasattr(apphelp_nav, "neighbours")


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
