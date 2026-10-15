"""markdown.sanitize: raw HTML in documents is cleaned with nh3, Markdown output is kept (SC-02, SEC-02)."""

import sys

import pytest
from lxml import html as lxml_html

from kb4it.core.exceptions import ConfigError
from kb4it.core.mdconfig import load_settings
from tests.helpers import FIXTURES, page, run_kb4it, write_repo

nh3 = pytest.importorskip("nh3")

HOSTILE_BODY = """[raw](javascript:alert(1))

<script>alert("body")</script>

<div onclick="alert(2)">x</div>

<img src="data:text/html;base64,PHNjcmlwdD4=" onerror="alert(3)">

| A | B |
|:--|--:|
| 1 | 2 |

!!! note
    An admonition.

```python
print("hello")
```
"""


def _dom(fragment):
    """Comparable tree of an HTML fragment: serialisation details ("<br>" or "<br />") do not count."""
    boolean = {"checked", "disabled", "open", "reversed"}  # "disabled" and disabled="" are the same

    def walk(element):
        attrib = sorted((k, "" if k in boolean else v) for k, v in element.attrib.items())
        return (element.tag, attrib, (element.text or "").strip(),
                [walk(child) for child in element if isinstance(child.tag, str)], (element.tail or "").strip())
    return walk(lxml_html.fragment_fromstring(fragment, create_parent="div"))


def _convert(text, **block):
    settings = load_settings({"markdown": block})
    html = settings.new_markdown().convert(text)
    if settings.sanitize:
        from kb4it.core.mdconfig import sanitize_html
        html = sanitize_html(html)
    return html


@pytest.mark.parametrize("extensions", [[], ["pymdownx.superfences", "pymdownx.tasklist", "pymdownx.details"]])
def test_markdown_output_survives_cleaning(extensions):
    if extensions:
        pytest.importorskip("pymdownx")
    text = (FIXTURES / "audit" / "rich.md").read_text(encoding="utf-8").split("\n---\n", 1)[1]
    text += "\nFoot[^1].\n\n[^1]: Note.\n\n![pic](data:image/png;base64,AAAA)\n"
    assert _dom(_convert(text, extensions=extensions, sanitize=True)) == _dom(_convert(text, extensions=extensions))


def test_hostile_html_is_removed():
    html = _convert(HOSTILE_BODY, sanitize=True)
    for gone in ("<script", "onclick", "onerror", "javascript:", "data:text/html"):
        assert gone not in html, gone
    assert "<table>" in html and 'class="admonition note"' in html and "language-python" in html
    assert 'style="text-align: left;"' in html or 'style="text-align:left"' in html


def test_sanitize_off_keeps_raw_html():
    html = _convert(HOSTILE_BODY)
    assert '<script>alert("body")</script>' in html and 'onclick="alert(2)"' in html


def test_sanitized_site(tmp_path, home):
    """The audit reproduction of SEC-02, with sanitize on."""
    cfg = write_repo(tmp_path / "repo", "techdoc", {"dot.md": page("Dot", HOSTILE_BODY, Tag="x")},
                     markdown={"sanitize": True})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    page_html = (tmp_path / "repo" / "target" / "dot.html").read_bytes()
    tree = lxml_html.fromstring(page_html)
    # The page still shows the document source under "Source", as text; none of it is live markup.
    assert not [s for s in tree.iter("script") if "alert(" in (s.text or "")]
    assert not [e for e in tree.iter() if isinstance(e.tag, str) and any(a.startswith("on") for a in e.attrib)
                and "alert(" in str(dict(e.attrib))]
    assert not [a for a in tree.iter("a") if a.get("href", "").startswith("javascript:alert")]  # theme buttons use javascript:
    assert b"An admonition." in page_html and b"print(" in page_html


def test_verify_lists_raw_scripts_when_sanitize_is_off(tmp_path, home):
    docs = {"dot.md": page("Dot", HOSTILE_BODY, Tag="x"),
            "code.md": page("Code", "Use `<script>` here.\n\n```html\n<script>x()</script>\n```\n", Tag="x")}
    cfg = write_repo(tmp_path / "repo", "techdoc", docs)
    result = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout  # information, not a failure
    assert "DOC_RAW_SCRIPT doc=dot.md" in result.stdout
    assert "doc=code.md" not in result.stdout  # code is shown, not run
    cfg2 = write_repo(tmp_path / "repo2", "techdoc", {"dot.md": page("Dot", HOSTILE_BODY, Tag="x")},
                      markdown={"sanitize": True})
    assert "DOC_RAW_SCRIPT" not in run_kb4it("verify", cfg2, cwd=tmp_path, home=home).stdout


def test_missing_nh3_is_a_clear_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "nh3", None)
    with pytest.raises(ConfigError, match="nh3"):
        load_settings({"markdown": {"sanitize": True}})


def test_sanitize_must_be_a_boolean():
    with pytest.raises(ConfigError, match="sanitize"):
        load_settings({"markdown": {"sanitize": "yes"}})
