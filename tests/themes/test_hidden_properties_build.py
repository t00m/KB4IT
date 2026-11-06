"""techdoc build with repo.json hidden_properties: off properties.html and the Properties menu, pages kept."""

import json
import re

from tests.helpers import page, run_kb4it


def _menu(html):
    """Property names of the Properties submenu of the logo menu."""
    block = html.split('href="properties.html"')[1].split("</ul>")[0]
    return re.findall(r'<span class="">([^<]+)</span>', block)


def test_hidden_properties_leave_the_page_and_the_menu(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    repo = tmp_path / "repo"
    for sample in (repo / "source").glob("*.md"):
        sample.unlink()
    (repo / "source" / "a.md").write_text(page("Doc A", Category="Note", Team="Linux", Ticket="T-1"),
                                          encoding="utf-8")
    cfg = repo / "config" / "repo.json"
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["hidden_properties"] = ["Team"]
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = repo / "target"

    props = (target / "properties.html").read_text(encoding="utf-8").split("PROPERTIES :: START")[1]
    assert 'href="Team.html"' not in props and 'href="Ticket.html"' in props
    menu = _menu((target / "a.html").read_text(encoding="utf-8"))
    assert "Ticket" in menu and "Team" not in menu
    assert (target / "Team.html").exists() and (target / "Team_Linux.html").exists()

    conf["hidden_properties"] = "Team"  # not a list
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode != 0 and "hidden_properties" in result.stdout
