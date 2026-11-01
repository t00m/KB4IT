"""techdoc diagrams: the Mermaid diagrams of every document, shown by the properties chosen in a filter panel."""

import os
import re
from html import unescape

from kb4it.core import trace
from kb4it.core.documents import strip_first_heading
from kb4it.core.mdconfig import load_settings
from kb4it.core.util import html_id_for

# A document is converted only when a line opens a mermaid fence.
MERMAID_FENCE = re.compile(r'^(`{3,}|~{3,})[ \t]*mermaid[ \t]*$', re.MULTILINE)

# A heading or a diagram of a document's HTML, in the order they come.
HEADING_OR_DIAGRAM = re.compile(r'<h([1-6])\b([^>]*)>(.*?)</h\1>|<pre class="mermaid">(.*?)</pre>', re.DOTALL)
HEADING_ID = re.compile(r'\bid="([^"]*)"')
TAG = re.compile(r'<[^>]+>')


def document_diagrams(html):
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


class DiagramsMixin:
    """The Diagrams page: the Gallery page, with the Mermaid diagrams of the documents instead of their images."""

    def diagram_html(self, doc_id):
        """The HTML of a document body with a mermaid fence, as the compiler makes it, so the heading ids match; else ''.

        The theme pages are built before the documents are compiled, so the body is converted here.
        """
        try:
            with open(os.path.join(self.srvbes.get_path('source'), doc_id), encoding='utf-8') as fh:
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
        settings = getattr(self.srvbes, 'markdown', None) or load_settings(self.srvbes.get_dict('repo'))
        return settings.new_markdown().convert(strip_first_heading(text))

    def diagram_items(self, doc_id):
        """The diagrams of one document, each linked to its section."""
        href = html_id_for(doc_id)
        html = self.diagram_html(doc_id)
        return [{'code': source, 'caption': heading, 'href': f'{href}#{anchor}' if anchor else href}
                for source, anchor, heading in document_diagrams(html)]

    def build_page_diagrams(self):
        """The Diagrams page: no diagram at first; the browser draws the ones the filters choose."""
        with trace.span('diagrams'):
            data = self.media_data(self.diagram_items)
        self.build_media_page('diagrams', 'Diagrams', 'diagram', data)
        docs, items, _filters = data
        self.log.info(f"[THEME] DIAGRAMS diagrams={len(items)} docs={len(docs)}")
