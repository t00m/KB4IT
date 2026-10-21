"""Core Markdown extension: mermaid fences and dollar formulas become marked elements."""

import pytest

from kb4it.core.mdconfig import MarkdownSettings, sanitize_html
from kb4it.core.mdrich import RichContentExtension

DIAGRAM = '<pre class="mermaid">graph LR\n  A--&gt;B</pre>'
MERMAID_SOURCE = "```mermaid\ngraph LR\n  A-->B\n```\n"


def _html(text, **settings):
    return MarkdownSettings(**settings).new_markdown().convert(text)


def test_mermaid_fence_becomes_diagram():
    assert DIAGRAM in _html(MERMAID_SOURCE)


@pytest.mark.parametrize("highlight", ["client", "pygments", "none"])
def test_mermaid_in_every_highlight_mode(highlight):
    html = _html(MERMAID_SOURCE, highlight=highlight)
    assert DIAGRAM in html
    assert "highlight" not in html


def test_mermaid_with_superfences():
    pytest.importorskip("pymdownx")
    html = _html(MERMAID_SOURCE, extensions=["pymdownx.superfences"])
    assert DIAGRAM in html
    assert "highlight" not in html


def test_mermaid_fence_inside_longer_fence_stays_code():
    html = _html("````markdown\n```mermaid\nA\n```\n````\n")
    assert 'class="mermaid"' not in html
    assert "```mermaid" in html


def test_inline_math():
    assert '<span class="kb4it-math">A = \\pi r^2</span>' in _html("The area is $A = \\pi r^2$.")


def test_display_math_multiline():
    html = _html("$$\nE = mc^2\n$$\n")
    assert '<div class="kb4it-math kb4it-math-display">E = mc^2</div>' in html
    assert "<p>" not in html


def test_display_math_single_line():
    assert '<div class="kb4it-math kb4it-math-display">E = mc^2</div>' in _html("$$E = mc^2$$\n")


def test_math_protects_emphasis_chars():
    html = _html("$a_1 * b_2$ and $c_3$")
    assert "<em>" not in html
    assert '<span class="kb4it-math">a_1 * b_2</span>' in html
    assert '<span class="kb4it-math">c_3</span>' in html


def test_tex_backslash_escapes_survive():
    assert '<span class="kb4it-math">\\{x\\} \\\\ y</span>' in _html("$\\{x\\} \\\\ y$")


def test_escaped_dollar_is_literal():
    html = _html("Price \\$5.")
    assert html == "<p>Price $5.</p>"


def test_dollars_in_code_untouched():
    html = _html("Use `$HOME` here.\n\n```bash\necho $A $B\n```\n\n    $x$\n")
    assert "kb4it-math" not in html
    assert "<code>$HOME</code>" in html
    assert "echo $A $B" in html
    assert "$x$" in html


def test_inline_code_inside_dollars_is_kept():
    html = _html("from $a `b` c$ on")
    assert "kb4it-math" not in html
    assert "<code>b</code>" in html


def test_space_after_opening_dollar_is_not_math():
    assert "kb4it-math" not in _html("5 $ each and 6 $ more")


def test_prices_with_spaces_are_not_math():
    assert "kb4it-math" not in _html("costs $5 and $10")


def test_dollar_pair_without_spaces_is_math():
    assert '<span class="kb4it-math">5/</span>' in _html("Pay $5/$10 now.")


def test_dollar_in_link_url_is_not_math():
    html = _html("[pay](https://x.org/?a=$1&b=$2)")
    assert 'href="https://x.org/?a=$1&amp;b=$2"' in html
    assert "kb4it-math" not in html


@pytest.mark.parametrize("text", ["$$\nE = mc^2\n", "a $ b"])
def test_unclosed_display_math_is_text(text):
    html = _html(text)
    assert "kb4it-math" not in html
    assert "$" in html


def test_math_source_is_escaped():
    assert '<span class="kb4it-math">a&lt;b \\&amp; c</span>' in _html("$a<b \\& c$")
    assert '<div class="kb4it-math kb4it-math-display">a &lt; b &amp; c</div>' in _html("$$\na < b & c\n$$\n")


def test_user_math_extension_disables_core():
    default = MarkdownSettings().all_extensions()
    assert any(isinstance(e, RichContentExtension) for e in default)
    for name in ("markdown_katex", "pymdownx.arithmatex"):
        names = MarkdownSettings(extensions=[name]).all_extensions()
        assert not any(isinstance(e, RichContentExtension) for e in names)


@pytest.mark.parametrize("markup", [
    '<pre class="mermaid">graph LR\n  A--&gt;B</pre>',
    '<span class="kb4it-math">a&lt;b</span>',
    '<div class="kb4it-math kb4it-math-display">E = mc^2</div>',
])
def test_sanitize_keeps_rich_markup(markup):
    pytest.importorskip("nh3")
    assert sanitize_html(markup) == markup
