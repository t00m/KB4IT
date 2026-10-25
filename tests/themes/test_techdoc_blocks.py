"""techdoc techdoc_blocks.py: code bars, folded code, table wrappers and author tab labels."""

import importlib.util

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo

spec = importlib.util.spec_from_file_location(
    "techdoc_blocks", ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic" / "techdoc_blocks.py")
blocks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blocks)


def code_block(language=None, lines=1):
    cls = f' class="language-{language}"' if language else ""
    body = "\n".join(f"line {i}" for i in range(lines))
    return f"<pre><code{cls}>{body}\n</code></pre>"


def table(rows):
    head = "<thead><tr><th>A</th></tr></thead>"
    body = "".join(f"<tr><td>{i}</td></tr>" for i in range(rows))
    return f"<table>{head}<tbody>{body}</tbody></table>"


def test_plain_html_is_returned_unchanged():
    body = "<p>Text.</p>"
    assert blocks.enhance_blocks(body) == body


def test_code_block_gets_a_bar_a_language_and_a_copy_button():
    html = blocks.enhance_blocks(code_block("python"))
    assert '<div class="kb-code">' in html
    assert '<div class="kb-code-bar">' in html
    assert '<span class="kb-code-lang">python</span>' in html
    assert 'class="kb-code-copy kb-noprint"' in html
    assert 'aria-label="Copy code"' in html
    assert ">Copy</span>" in html
    assert "<pre><code class=\"language-python\">" in html


def test_code_without_a_language_has_no_label():
    html = blocks.enhance_blocks(code_block())
    assert "kb-code-lang" not in html
    assert "kb-code-copy" in html


def test_mermaid_diagrams_are_left_alone():
    body = '<pre class="mermaid">graph TD;\nA-->B;</pre>'
    assert blocks.enhance_blocks(body) == body


def test_long_code_is_folded_and_gets_a_show_button():
    html = blocks.enhance_blocks(code_block("bash", 42))
    assert "kb-code kb-code-long" in html
    assert 'class="kb-code-show kb-noprint" data-lines="42"' in html
    assert ">Show all 42 lines</button>" in html


def test_short_code_is_not_folded():
    html = blocks.enhance_blocks(code_block("bash", 30))
    assert "kb-code-long" not in html
    assert "kb-code-show" not in html


def test_tables_are_wrapped_for_sideways_scrolling():
    html = blocks.enhance_blocks(table(2))
    assert '<div class="kb-table uk-overflow-auto"><table>' in html
    assert "kb-table-sticky" not in html


def test_long_tables_get_a_sticky_header():
    assert "kb-table-sticky" in blocks.enhance_blocks(table(16))
    assert "kb-table-sticky" not in blocks.enhance_blocks(table(15))


def test_author_tabs_get_a_print_label_per_panel():
    body = ('<div class="tabbed-set tabbed-alternate" data-tabs="1:2">'
            '<input checked="checked" id="t1" name="t" type="radio"><input id="t2" name="t" type="radio">'
            '<div class="tabbed-labels"><label for="t1">Linux</label><label for="t2">Windows</label></div>'
            '<div class="tabbed-content"><div class="tabbed-block"><p>dnf</p></div>'
            '<div class="tabbed-block"><p>winget</p></div></div></div>')
    html = blocks.enhance_blocks(body)
    assert html.count('class="kb-tab-print"') == 2
    assert '<p class="kb-tab-print">Linux</p><p>dnf</p>' in html
    assert '<p class="kb-tab-print">Windows</p><p>winget</p>' in html


def test_text_around_a_block_keeps_its_place():
    html = blocks.enhance_blocks(f"before{code_block('sh')}after")
    assert html.startswith("before<div class=\"kb-code\">")
    assert html.endswith("</div>after")


def test_a_wrapped_block_is_not_wrapped_again():
    html = blocks.enhance_blocks(code_block("python"))
    assert blocks.enhance_blocks(html).count('class="kb-code"') == 1


LONG_CODE = "\n".join(f"echo line {i}" for i in range(40))
TABLE_16 = "\n".join(f"| {i} | value {i} |" for i in range(16))
BLOCKS_BODY = f"""## Code

```python
print("hi")
```

```bash
{LONG_CODE}
```

## Tables

| A | B |
|---|---|
| 1 | 2 |

| A | B |
|---|---|
{TABLE_16}

## Tabs

=== "Linux"

    Run `dnf`.

=== "Windows"

    Run `winget`.

## Note

??? note "Read this"

    A collapsible note.
"""


@pytest.fixture(scope="module")
def blocks_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-blocks")
    home = base / "home"
    home.mkdir()
    docs = {"blocks.md": page("Content blocks", BLOCKS_BODY, Category="Note")}
    cfg = write_repo(base / "repo", "techdoc", docs, markdown={
        "extensions": ["pymdownx.tabbed", "pymdownx.details"],
        "extension_configs": {"pymdownx.tabbed": {"alternate_style": True}},
    })
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return base / "repo" / "target"


def test_built_page_has_code_bars_and_folded_long_code(blocks_site):
    html = (blocks_site / "blocks.html").read_text(encoding="utf-8")
    assert html.count('class="kb-code-bar"') == 2
    assert '<span class="kb-code-lang">python</span>' in html
    assert 'data-lines="40">Show all 40 lines</button>' in html


def test_built_page_has_scrolling_and_sticky_tables(blocks_site):
    html = (blocks_site / "blocks.html").read_text(encoding="utf-8")
    assert html.count('class="kb-table uk-overflow-auto"') == 1
    assert 'class="kb-table uk-overflow-auto kb-table-sticky"' in html


def test_built_page_has_author_tabs_and_collapsible_notes(blocks_site):
    html = (blocks_site / "blocks.html").read_text(encoding="utf-8")
    assert '<div class="tabbed-set' in html
    assert html.count('class="kb-tab-print"') == 2
    assert '<p class="kb-tab-print">Linux</p>' in html
    assert '<details class="note">' in html
