"""Turn mermaid fences and dollar formulas into marked elements for the browser scripts."""

import html
import re
import xml.etree.ElementTree as etree

from markdown import util
from markdown.extensions import Extension
from markdown.inlinepatterns import AUTOLINK_RE, AUTOMAIL_RE, HTML_RE, InlineProcessor
from markdown.preprocessors import Preprocessor

# Pages whose HTML contains these need the Mermaid or KaTeX scripts; inline code escapes the "<", so it never matches.
MERMAID_MARK = '<pre class="mermaid">'
MATH_MARKS = ('<span class="kb4it-math', '<div class="kb4it-math')
# User extensions that render formulas themselves; the core math processors then stay off.
MATH_EXTENSIONS = ("pymdownx.arithmatex", "markdown_katex")

FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
# A whole line $$...$$; no bare $ inside, so "$$a$$ text $$b$$" is left to the inline processors.
DISPLAY_LINE_RE = re.compile(r"^\$\$((?:\\.|[^$\\])+)\$\$\s*$")
# Escaped dollars are stashed before these run, so a bare $ never belongs to the formula.
INLINE_DISPLAY_RE = r"(?<!\$)\$\$([^$]+)\$\$(?!\$)"
INLINE_MATH_RE = r"(?<!\$)\$(?![\s$])([^$]+?)(?<!\s)\$(?!\$)"
# Spans owned by inline patterns that run after the math ones: raw HTML tags, autolinks, image destinations.
PROTECTED_RES = [re.compile(r, re.DOTALL) for r in (HTML_RE, AUTOLINK_RE, AUTOMAIL_RE)]
IMAGE_DEST_RE = re.compile(r"!\[[^\]]*\](\([^)]*\))")
# What the escape processor stashes for a backslash escape: STX + code point + ETX.
ESCAPED_RE = re.compile(f"^{util.STX}([0-9]+){util.ETX}$")


def _protected(data, pos):
    """True when position pos of data is inside a raw HTML tag, an autolink or an image destination."""
    spans = [m.span() for regex in PROTECTED_RES for m in regex.finditer(data)]
    spans += [m.span(1) for m in IMAGE_DEST_RE.finditer(data)]
    return any(start < pos < end for start, end in spans)


def _closing_fence(lines, start, fence):
    """Index of the line closing `fence` (same character, at least as long), or None."""
    char = fence[0]
    for index in range(start, len(lines)):
        line = lines[index].rstrip()
        if len(line) >= len(fence) and line == char * len(line):
            return index
    return None


class _MermaidPreprocessor(Preprocessor):
    def run(self, lines):
        out, index = [], 0
        while index < len(lines):
            match = FENCE_RE.match(lines[index])
            end = _closing_fence(lines, index + 1, match.group(1)) if match else None
            if end is None:
                out.append(lines[index])
                index += 1
                continue
            if match.group(2).strip() == "mermaid":
                source = html.escape("\n".join(lines[index + 1:end]), quote=False)
                out += ["", self.md.htmlStash.store(f'<pre class="mermaid">{source}</pre>'), ""]
            else:
                # Any other fence passes through whole, so a mermaid fence inside it stays code.
                out += lines[index:end + 1]
            index = end + 1
        return out


class _DisplayMathPreprocessor(Preprocessor):
    def run(self, lines):
        out, index = [], 0
        while index < len(lines):
            line = lines[index].rstrip()
            single = DISPLAY_LINE_RE.match(line)
            if single and single.group(1).strip():
                out += self._stash(single.group(1).strip())
                index += 1
                continue
            end = None
            if line == "$$":
                end = next((i for i in range(index + 1, len(lines)) if lines[i].rstrip() == "$$"), None)
            if end is None:
                out.append(lines[index])
                index += 1
                continue
            out += self._stash("\n".join(lines[index + 1:end]))
            index = end + 1
        return out

    def _stash(self, tex):
        markup = f'<div class="kb4it-math kb4it-math-display">{html.escape(tex, quote=False)}</div>'
        return ["", self.md.htmlStash.store(markup), ""]


class _MathProcessor(InlineProcessor):
    """A formula in paragraph text, as a span with the class below."""

    css_class = "kb4it-math"

    def handleMatch(self, m, data):
        if _protected(data, m.start(0)):
            return None, None, None
        stashed = self.md.treeprocessors["inline"].stashed_nodes

        def unescape(placeholder):
            # The escape processor stashed \{, \\ or \$ as STX + code point + ETX; TeX needs the backslash back.
            node = stashed.get(placeholder.group(1))
            escaped = ESCAPED_RE.match(node) if isinstance(node, str) else None
            if escaped is None:
                raise LookupError  # inline code or a link inside the dollars
            return "\\" + chr(int(escaped.group(1)))

        try:
            tex = util.INLINE_PLACEHOLDER_RE.sub(unescape, m.group(1)).strip()
        except LookupError:
            return None, None, None
        if not tex:
            return None, None, None
        element = etree.Element("span", {"class": self.css_class})
        element.text = util.AtomicString(tex)
        return element, m.start(0), m.end(0)


class _InlineDisplayMathProcessor(_MathProcessor):
    # A span, not a div, so the HTML stays valid inside <p>.
    css_class = "kb4it-math kb4it-math-display"


class RichContentExtension(Extension):
    """python-markdown extension: mermaid fences and $...$ / $$...$$ formulas as marked elements."""

    def __init__(self, **kwargs):
        self.config = {"math": [True, "Turn $...$ and $$...$$ into formulas; off when a user extension does it"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # 30: after normalize_whitespace (also 30, registered earlier), before the fences (25).
        md.preprocessors.register(_MermaidPreprocessor(md), "kb4it_mermaid", 30)
        if not self.getConfig("math"):
            return
        md.ESCAPED_CHARS.append("$")
        # 20: after the fences (25) and the raw HTML blocks (also 20, registered earlier).
        md.preprocessors.register(_DisplayMathPreprocessor(md), "kb4it_display_math", 20)
        # 156 and 155: after backticks (190), escapes (180) and links (160), before emphasis (60);
        # $$...$$ first, so a single $ never starts on half of a $$ pair.
        # Image links (150), autolinks (120) and raw HTML (90) come later, so _protected() guards them.
        md.inlinePatterns.register(_InlineDisplayMathProcessor(INLINE_DISPLAY_RE, md), "kb4it_inline_display_math", 156)
        md.inlinePatterns.register(_MathProcessor(INLINE_MATH_RE, md), "kb4it_inline_math", 155)
