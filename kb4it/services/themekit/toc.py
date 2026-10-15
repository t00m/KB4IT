"""Table of contents of a document page, in the theme's markup."""


class TocMixin:
    """`extract_toc`; needs `Builder.template` and `get_theme_var`."""

    def extract_toc(self, source):
        """Extract TOC from compiled HTML code and make it theme dependent.

        The compiler writes the TOC block after a "toctitle" line; its lines up to
        the next "</div>" get the theme's HTML_TOC_LI and HTML_TOC_SECTLEVEL1 to 4
        markup. Returns '' when the source has no TOC.
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

        var = self.get_theme_var()
        li_top = self.template('HTML_TOC_LI').render(var=var)
        levels = [(name, self.template(template).render(var=var)) for name, template in (
            ("sectlevel1", 'HTML_TOC_SECTLEVEL1'),
            ("sectlevel2", 'HTML_TOC_SECTLEVEL2'),
            ("sectlevel3", 'HTML_TOC_SECTLEVEL3'),
            ("sectlevel4", 'HTML_TOC_SECTLEVEL4'),
        )]
        items = []
        for line in lines[start:end]:
            if line.startswith('<li><a href='):
                line = line.replace("<li><a ", li_top)
            else:
                for name, markup in levels:
                    line = line.replace(name, markup)
            items.append(line)
        return '\n'.join(items)
