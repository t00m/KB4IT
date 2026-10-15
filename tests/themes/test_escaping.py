"""Hostile titles, property names and values show as text in every bundled theme (SC-01, SEC-01)."""

import json
import shutil

import pytest
from lxml import html as lxml_html

from tests.helpers import FIXTURES, run_kb4it

# Every payload calls alert(); a page is safe when no alert( reaches a script, an element made
# from a payload, or an event handler attribute.
APPHELP_DOC = """---
DocType: How-to guide
Feature: Documents
HelpId: hostile
Keyword: <script>alert("keyword")</script>
Level: basic
Order: 999
Section: <img src=x onerror=alert("section")>
Summary: Eve" onmouseover="alert('summary')
---

# Title <svg onload=alert("title")>

Body text.
"""


def _offences(page):
    tree = lxml_html.fromstring(page.read_bytes())
    found = []
    for element in tree.iter():
        if not isinstance(element.tag, str):
            continue
        if element.tag == "script" and element.get("type") == "application/json":
            continue  # data, never run; a value that closed it would show up as a script of its own
        if element.tag in ("script", "svg", "img") and "alert(" in (element.text or "") + str(dict(element.attrib)):
            found.append(f"<{element.tag}> {dict(element.attrib)} {element.text!r:.60}")
        for name, value in element.attrib.items():
            if name.startswith("on") and "alert(" in value:
                found.append(f"{name}={value!r}")
    return found


def _site(tmp_path, home, theme):
    repo = tmp_path / theme
    assert run_kb4it("create", theme, repo, cwd=tmp_path, home=home).returncode == 0
    if theme == "apphelp":
        (repo / "source" / "hostile.md").write_text(APPHELP_DOC, encoding="utf-8")
    else:
        shutil.copy(FIXTURES / "audit" / "hostile.md", repo / "source" / "hostile.md")
    if theme == "techdoc":
        # Make the hostile document an event, so the calendar and archive pages show it too.
        cfg = repo / "config" / "repo.json"
        conf = json.loads(cfg.read_text(encoding="utf-8"))
        conf["events"] = [*conf.get("events", []), '<img src=x onerror=alert("cat")>']
        cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return repo / "target"


@pytest.mark.parametrize("theme", ["apphelp", "techdoc", "blog"])
def test_hostile_values_are_text(tmp_path, home, theme):
    target = _site(tmp_path, home, theme)
    pages = sorted(target.rglob("*.html"))
    assert pages
    offences = {p.name: o for p in pages if (o := _offences(p))}
    assert offences == {}
    # The payloads did reach the pages, as text.
    text = "".join(p.read_text(encoding="utf-8") for p in pages)
    assert "&lt;svg onload=alert(" in text
    if theme == "techdoc":
        assert (target / "events_2026.html").is_file()
