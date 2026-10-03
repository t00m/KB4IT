"""bookshelf theme: Book > Part > Chapter model, book overview, chapter navigation."""

import pytest

from tests.helpers import page, run_kb4it

BOOK = "Linux Admin"

PAGES = {
    "c1.md": page("Boot process", "## Steps\n\nText.", Book=BOOK, Part="I", PartTitle="Basics", Chapter="1",
                  Status="Done", Date="2026-01-01", Command="systemctl"),
    "c2.md": page("Users", Book=BOOK, Part="I", Chapter="2", Status="Reading", Date="2026-01-02"),
    "c3.md": page("Storage", Book=BOOK, Part="II", PartTitle="Advanced", Chapter="Chapter 3",
                  Date="2026-01-03", Tag="lvm"),
    "loose.md": page("Loose note", Tag="misc", Date="2026-01-04"),
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("bookshelf")
    home = base / "home"
    home.mkdir()
    assert run_kb4it("create", "bookshelf", "repo", cwd=base, home=home).returncode == 0
    repo = base / "repo"
    for name, text in PAGES.items():
        (repo / "source" / name).write_text(text, encoding="utf-8")
    cfg = repo / "config" / "repo.json"
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"base": base, "home": home, "repo": repo, "cfg": cfg, "target": repo / "target", "log": result.stdout}


def read(site, name):
    return (site["target"] / name).read_text(encoding="utf-8")


def test_build_is_clean(site):
    assert "ERROR |" not in site["log"]
    for name in PAGES:
        assert (site["target"] / name.replace(".md", ".html")).exists()


def test_index_shows_every_book(site):
    html = read(site, "index.html")
    assert BOOK in html
    assert "Unfiled" in html


def test_book_overview_orders_parts_and_chapters(site):
    html = read(site, "Book_Linux_Admin.html")
    assert html.index("c1.html") < html.index("c2.html") < html.index("c3.html")
    assert "Basics" in html and "Advanced" in html


def test_chapter_navigation(site):
    html = read(site, "c2.html")
    assert "c1.html" in html and "c3.html" in html     # previous and next chapter
    assert "systemctl" in read(site, "c1.html")


def test_metadata_pages(site):
    assert "c1.html" in read(site, "Command_systemctl.html")
    for name in ("properties.html", "stats.html", "all.html", "bookmarks.html", "help.html"):
        assert (site["target"] / name).exists(), name


def test_user_index_page_wins(site):
    (site["repo"] / "source" / "index.md").write_text(page("My own index", Tag="home"), encoding="utf-8")
    result = run_kb4it("build", site["cfg"], cwd=site["base"], home=site["home"])
    assert result.returncode == 0, result.stdout
    assert "INDEX_SKIP reason=user_generated" in result.stdout
    assert "My own index" in read(site, "index.html")
