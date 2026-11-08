"""Feature toc: the table of contents of a document page, in the theme's markup."""

from __future__ import annotations

from typing import Any

from kb4it.theme.feature import Feature

LEVELS = (("sectlevel1", "HTML_TOC_SECTLEVEL1"), ("sectlevel2", "HTML_TOC_SECTLEVEL2"),
          ("sectlevel3", "HTML_TOC_SECTLEVEL3"), ("sectlevel4", "HTML_TOC_SECTLEVEL4"))


class Toc(Feature):
    """var['toc'] of every document page, and the Contents menu of the header."""

    name = "toc"
    templates = ("HTML_TOC_LI", "HTML_TOC_SECTLEVEL1", "HTML_TOC_SECTLEVEL2", "HTML_TOC_SECTLEVEL3",
                 "HTML_TOC_SECTLEVEL4")

    def extract(self, source: str) -> str:
        """The TOC of compiled HTML in the theme's markup; '' when the source has none.

        The compiler writes the TOC block after a "toctitle" line; its lines up to the next
        "</div>" get the theme's HTML_TOC_LI and HTML_TOC_SECTLEVEL1 to 4 markup.
        """
        lines = source.split('\n')
        start = end = 0
        for n, line in enumerate(lines):
            if line.find("toctitle") > 0:
                start = n + 1
            if start > 0 and line.startswith('</div>') and n > start:
                end = n
                break
        if not (start > 0 and end > start):
            return ''

        engine = self.engine
        var = engine.get_theme_var()
        li_top = engine.template('HTML_TOC_LI').render(var=var)
        levels = [(name, engine.template(template).render(var=var)) for name, template in LEVELS]
        items = []
        for line in lines[start:end]:
            if line.startswith('<li><a href='):
                line = line.replace("<li><a ", li_top)
            else:
                for name, markup in levels:
                    line = line.replace(name, markup)
            items.append(line)
        return '\n'.join(items)

    def menu_contents(self, var: dict[str, Any]) -> str:
        """The header's Contents menu: disabled on a system page, the document's TOC otherwise."""
        if var['SystemPage']:
            html: str = self.engine.template('HTML_HEADER_MENU_CONTENTS_DISABLED').render()
        else:
            html = self.engine.template('HTML_HEADER_MENU_CONTENTS_ENABLED').render(var=var)
        return html
