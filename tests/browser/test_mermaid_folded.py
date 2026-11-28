"""A Mermaid diagram in a folded techdoc section renders when the section opens, not as "Syntax error in text"."""

import pytest

from tests.helpers import page as md_page
from tests.themes.test_techdoc_add import build_techdoc

pytestmark = pytest.mark.browser

FENCE = "`" * 3
# Subgraphs with labelled dotted edges: Mermaid 11 throws on this one when its container has no layout box.
DIAGRAM = """flowchart TB
    U[Users]
    subgraph APP[Application tier]
      ASCS[ASCS]
      ERS[ERS]
      PAS[Primary Application Server]
    end
    subgraph DR[DR site]
      HDB2[Secondary HANA system]
      CL[Cluster]
    end
    U --> PAS
    ASCS --- PAS
    ERS -. enqueue replication .-> ASCS
    CL -. controls failover .-> HDB2
"""
BODY = f"## Overview\n\nText.\n\n## Topology\n\n{FENCE}mermaid\n{DIAGRAM}{FENCE}\n"
STATE = """() => { const e = document.querySelector('pre.mermaid');
    return {svg: !!e.querySelector('svg[aria-roledescription]'), error: e.textContent.includes('Syntax error')}; }"""


@pytest.fixture(scope="module")
def mermaid_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-mermaid")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, {"topology.md": md_page("Topology", body=BODY, Category="Note", Date="2026-11-01")})


def test_folded_diagram_renders_when_opened(browser, mermaid_site):
    context = browser.new_context()
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.set_default_timeout(10000)
    try:
        page.goto((mermaid_site / "topology.html").as_uri())
        page.wait_for_function("!!window.mermaid")
        section = page.locator("#topology").locator("xpath=ancestor::*[contains(@class,'kb-sect1')][1]")
        assert "kb-closed" in section.get_attribute("class")
        page.wait_for_timeout(500)
        assert page.evaluate(STATE) == {"svg": False, "error": False}
        page.click("#topology")
        page.wait_for_function("!!document.querySelector('pre.mermaid svg')")
        assert page.evaluate(STATE) == {"svg": True, "error": False}
    finally:
        context.close()
