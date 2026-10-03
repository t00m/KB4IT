from apphelp_checks import (check_anchors, check_contract, check_helpids, helpid_map, load_contract,
                            render_helpids_js)
from apphelp_meta import Page


def write(target, name, body):
    (target / name).write_text(f"<html><body>{body}</body></html>", encoding="utf-8")


def site(tmp_path):
    write(tmp_path, "a.html", '<h2 id="x">X</h2><a href="b.html#y">ok</a><a href="b.html#nope">bad</a>'
                              '<a href="#x">self</a><a href="gone.html">gone</a><a href="https://x.org/#z">ext</a>'
                              '<a href="resources/a.css">css</a><a href="search.html?q=a">q</a>')
    write(tmp_path, "b.html", '<details id="y"><summary>Y</summary></details>')
    write(tmp_path, "search.html", "<p>search</p>")
    return tmp_path


def test_check_anchors(tmp_path):
    target = site(tmp_path)
    assert check_anchors(target, ["a.html", "b.html", "search.html"]) == [
        ("a.html", "b.html#nope"), ("a.html", "gone.html")]


def test_helpids(tmp_path):
    target = site(tmp_path)
    pages = [Page(doc_id="a.md", title="A", doctype="howto", section="S", order=1, summary="",
                  helpids=[("intro", ""), ("ex", "x"), ("broken", "missing")])]
    mapping = helpid_map(pages)
    assert mapping == {"broken": "a.html#missing", "ex": "a.html#x", "intro": "a.html"}
    assert render_helpids_js(mapping).startswith('window.APPHELP_HELPIDS = {"broken"')
    assert check_helpids(target, mapping) == ["broken"]


def test_contract(tmp_path):
    target = site(tmp_path)
    contract = tmp_path / "contract.txt"
    contract.write_text("# comment\n\nintro\nunknown-id\na.html#x\nb.html#nope\nmissing.html\n")
    entries = load_contract(contract)
    assert entries == ["intro", "unknown-id", "a.html#x", "b.html#nope", "missing.html"]
    assert check_contract(entries, {"intro": "a.html"}, target) == ["unknown-id", "b.html#nope", "missing.html"]
    assert load_contract(tmp_path / "absent.txt") == []
