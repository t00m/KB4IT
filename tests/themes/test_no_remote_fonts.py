"""Bundled themes use fonts installed on the reader's computer; no page loads a web font from a remote host."""

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo

THEMES_DIR = ROOT / "kb4it" / "resources" / "themes"
REMOTE_FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net", "fonts.bunny.net")


@pytest.mark.parametrize("theme", sorted(p.name for p in THEMES_DIR.iterdir() if (p / "theme.json").is_file()))
def test_theme_sources_load_no_remote_fonts(theme):
    for path in (THEMES_DIR / theme).rglob("*"):
        if path.suffix in (".tpl", ".css", ".html") and ".min." not in path.name:
            text = path.read_text(encoding="utf-8", errors="replace")
            for host in REMOTE_FONT_HOSTS:
                assert host not in text, f"{path.relative_to(ROOT)} loads fonts from {host}"


def test_bookshelf_pages_load_no_remote_fonts(tmp_path, home):
    pages = {"hello.md": page("Hello page", "Some text.", Category="Chapter", Date="2026-10-08")}
    cfg = write_repo(tmp_path / "repo", "bookshelf", pages)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / "repo" / "target"
    assert (target / "index.html").is_file()
    for html in target.glob("*.html"):
        text = html.read_text(encoding="utf-8")
        for host in REMOTE_FONT_HOSTS:
            assert host not in text, f"{html.name} loads fonts from {host}"
