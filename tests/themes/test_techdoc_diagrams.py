"""techdoc Diagrams page: the Mermaid diagrams of the documents, filtered like the Gallery, drawn in the browser."""

import importlib.util
import json
import re
import sys

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
sys.path.insert(0, str(LOGIC))  # techdoc_diagrams is loaded as the theme loads it


def _load(name):
    spec = importlib.util.spec_from_file_location(name, LOGIC / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diagrams = _load("techdoc_diagrams")

FENCE = "`" * 3
FLOW = f"{FENCE}mermaid\nflowchart LR\n  A[Alert] --> B[Restart & check]\n{FENCE}\n"
DOCS = {
    "topology.md": page("Landscape topology",
                        f"## Overview\n\nText.\n\n## Logical `topology`\n\n{FLOW}\n## Steps\n\n"
                        f"~~~~text\n{FLOW}~~~~\n\n{FENCE}mermaid\nsequenceDiagram\n  A->>B: Hi\n{FENCE}\n",
                        Category="Note", Date="2026-03-01", Product="SAP", Tag="landscape"),
    "restart.md": page("Restart procedure", f"Intro.\n\n{FLOW}", Category="Procedure", Date="2025-10-01", Product="Linux",
                       Author="Tomás Vírseda"),
    "plain.md": page("No diagrams", "Text.", Category="Note"),
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-diagrams")
    home = base / "home"
    home.mkdir()
    cfg = write_repo(base, "techdoc", DOCS)
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"target": base / "target", "log": result.stdout}


def read(site, name):
    return (site["target"] / name).read_text(encoding="utf-8")


def data(site):
    raw = re.search(r'<script type="application/json" id="kb-gal-data">(.*?)</script>', read(site, "diagrams.html"), re.DOTALL)
    return json.loads(raw.group(1))


def test_document_diagrams_follow_their_section():
    html = ('<pre class="mermaid">graph TD; A--&gt;B</pre><h2 id="one">One <code>x</code></h2><p>t</p>'
            '<pre class="mermaid">\nflowchart LR\n  C &amp; D\n</pre><h3 id="two">Two</h3><pre class="mermaid">  </pre>'
            '<pre><code>not a diagram</code></pre>')
    assert diagrams.document_diagrams(html) == [("graph TD; A-->B", "", ""), ("flowchart LR\n  C & D", "one", "One x")]


def test_diagrams_page_draws_nothing_until_asked(site):
    html = read(site, "diagrams.html")
    main = html[html.index("DIAGRAMS PAGE :: START"):html.index("DIAGRAMS PAGE :: END")]
    assert '<pre class="mermaid">' not in main and "<svg" not in main
    assert "3 diagrams in 2 documents. Choose a property on the right to show its diagrams." in main
    assert 'data-kb4it-mermaid="page"' in main and "gallery.js" in main
    assert "resources/render/mermaid/mermaid.min.js" in html and "resources/render/kb4it-render.js" in html
    assert "[THEME] DIAGRAMS diagrams=3 docs=2" in site["log"]


def test_diagrams_data_links_each_diagram_to_its_section(site):
    d = data(site)
    assert d["kind"] == "diagram"
    assert [doc["href"] for doc in d["docs"]] == ["topology.html", "restart.html"]
    flow, sequence, restart = d["items"]
    assert flow["code"] == "flowchart LR\n  A[Alert] --> B[Restart & check]"
    assert flow["caption"] == "Logical topology" and flow["href"] == "topology.html#logical-topology"
    assert sequence["code"].startswith("sequenceDiagram") and sequence["href"] == "topology.html#steps"
    assert restart["caption"] == "" and restart["href"] == "restart.html" and restart["d"] == 1
    product = next(f for f in d["filters"] if f["key"] == "Product")
    assert product["values"] == [["Linux", 1], ["SAP", 2]]


def test_diagrams_is_in_the_menu_and_a_system_page(site):
    assert 'href="diagrams.html"' in read(site, "restart.html")
    table = read(site, "all.html")
    assert "diagrams.html" not in table[table.index("<table"):]


def test_gallery_page_loads_no_mermaid(site):
    assert "mermaid.min.js" not in read(site, "gallery.html")


def test_diagrams_without_diagrams_says_so(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    cfg = write_repo(tmp_path, "techdoc", {"plain.md": DOCS["plain.md"]})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "target" / "diagrams.html").read_text(encoding="utf-8")
    assert "No document has a diagram yet" in html and "kb-gal-data" not in html
    assert "mermaid.min.js" not in html


def test_filter_values_keep_their_accents(site):
    # JSON inside <script> is not decoded by the browser: "&#225;" would show as typed.
    html = read(site, "diagrams.html")
    raw = re.search(r'id="kb-gal-data">(.*?)</script>', html, re.DOTALL).group(1)
    assert "&#" not in raw
    author = next(f for f in data(site)["filters"] if f["key"] == "Author")
    assert author["values"] == [["Tomás Vírseda", 1]]
