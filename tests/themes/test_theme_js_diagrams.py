"""Theme scripts that rewrite <pre> blocks leave Mermaid diagrams (pre.mermaid) to kb4it-render.js."""

import re

from tests.helpers import ROOT

RESOURCES = ROOT / "kb4it" / "resources"
# Each theme's own scripts; vendored libraries (uikit, highlight.js, jQuery) never touch pre.mermaid.
OWN_SCRIPTS = [RESOURCES / "themes" / "bookshelf" / "framework" / "bookshelf" / "js" / "bookshelf.js",
               RESOURCES / "themes" / "apphelp" / "framework" / "apphelp" / "js" / "apphelp.js",
               *sorted((RESOURCES / "common" / "js").glob("*.js"))]
PRE_SELECTOR = re.compile(r"""querySelectorAll\(\s*(["'])([^"']*)\1""")


def test_own_scripts_listed_exist():
    for path in OWN_SCRIPTS:
        assert path.is_file(), path


def test_scripts_that_walk_pre_skip_mermaid():
    for path in OWN_SCRIPTS:
        for match in PRE_SELECTOR.finditer(path.read_text(encoding="utf-8")):
            selector = match.group(2)
            if re.search(r"(^|[\s,>])pre\b", selector):
                assert "pre:not(.mermaid)" in selector, f"{path.name}: {selector}"
