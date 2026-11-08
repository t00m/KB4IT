"""Feature diagrams: the Mermaid diagrams of every document, shown by the properties chosen in a filter panel."""

from __future__ import annotations

import os
import re
from html import unescape
from typing import TYPE_CHECKING, Any

from kb4it.core import trace
from kb4it.core.documents import strip_first_heading
from kb4it.core.mdconfig import load_settings
from kb4it.core.util import html_id_for
from kb4it.theme.feature import Feature
from kb4it.theme.media import media_data, render_media_page

if TYPE_CHECKING:
    from kb4it.theme.site import Site

# A document is converted only when a line opens a mermaid fence.
MERMAID_FENCE = re.compile(r'^(`{3,}|~{3,})[ \t]*mermaid[ \t]*$', re.MULTILINE)

# A heading or a diagram of a document's HTML, in the order they come.
HEADING_OR_DIAGRAM = re.compile(r'<h([1-6])\b([^>]*)>(.*?)</h\1>|<pre class="mermaid">(.*?)</pre>', re.DOTALL)
HEADING_ID = re.compile(r'\bid="([^"]*)"')
TAG = re.compile(r'<[^>]+>')


def document_diagrams(html: str) -> list[tuple[str, str, str]]:
    """Return [(source, anchor, heading), ...]: each Mermaid diagram of the HTML and the section it is in.

    anchor and heading are those of the nearest heading above the diagram, or '' before the first one.
    """
    diagrams, anchor, heading = [], '', ''
    for match in HEADING_OR_DIAGRAM.finditer(html):
        if match.group(1):
            found = HEADING_ID.search(match.group(2))
            anchor = unescape(found.group(1)) if found else ''
            heading = ' '.join(unescape(TAG.sub('', match.group(3))).split())
        else:
            source = unescape(match.group(4)).strip('\n')
            if source.strip():
                diagrams.append((source, anchor, heading))
    return diagrams


class Diagrams(Feature):
    """diagrams.html: the Gallery page, with the Mermaid diagrams of the documents instead of their images."""

    name = "diagrams"
    templates = ("PAGE_GALLERY",)
    assets = ("gallery",)
    reserves = ("diagrams.md",)

    def html_of(self, doc_id: str) -> str:
        """The HTML of a document body with a mermaid fence, as the compiler makes it, so the heading ids match; else ''.

        The theme pages are built before the documents are compiled, so the body is converted here.
        """
        srvbes = self.engine.srvbes
        try:
            with open(os.path.join(srvbes.get_path('source'), doc_id), encoding='utf-8') as fh:
                text = fh.read().replace('\r\n', '\n')
        except OSError:
            return ''
        if not MERMAID_FENCE.search(text):
            return ''
        if text.startswith('---'):
            end = text.find('\n---', 3)
            if end >= 0:
                line_end = text.find('\n', end + 4)
                text = text[line_end + 1:].lstrip('\n') if line_end >= 0 else ''
        settings = getattr(srvbes, 'markdown', None) or load_settings(srvbes.get_dict('repo'))
        return str(settings.new_markdown().convert(strip_first_heading(text)))

    def items(self, doc_id: str) -> list[dict[str, Any]]:
        """The diagrams of one document, each linked to its section."""
        href = html_id_for(doc_id)
        html = self.theme.diagram_html(doc_id) if self.legacy else self.html_of(doc_id)
        return [{'code': source, 'caption': heading, 'href': f'{href}#{anchor}' if anchor else href}
                for source, anchor, heading in document_diagrams(html)]

    def write(self) -> None:
        """diagrams.html: no diagram at first; the browser draws the ones the filters choose."""
        items_of = self.theme.diagram_items if self.legacy else self.items
        with trace.span('diagrams'):
            data = media_data(self.engine, items_of)
        render_media_page(self.engine, 'diagrams', 'Diagrams', 'diagram', data)
        docs, items, _filters = data
        self.engine.log.info(f"[THEME] DIAGRAMS diagrams={len(items)} docs={len(docs)}")

    def pages(self, site: Site) -> None:
        self.write()
