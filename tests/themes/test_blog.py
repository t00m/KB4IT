"""blog theme: index with excerpts, archive, metadata pages and incremental rebuilds."""

import json

import pytest

from tests.helpers import page, run_kb4it


def post(title, date, excerpt=None, category="Post", **keys):
    body = f"## Excerpt\n\n{excerpt}\n\n## Body\n\nFull text of {title}." if excerpt else f"Full text of {title}."
    return page(title, body, Date=date, Category=category, **keys)


PAGES = {
    "first.md": post("First post", "2025-03-01", "Old excerpt.", Tag="python", Author="Ann"),
    "second.md": post("Second post", "2026-05-10", "Fresh excerpt.", Tag="python, linux", Topic="Development"),
    "third.md": post("Third post", "2026-06-20", Tag="linux"),
    "note.md": post("A note", "2026-01-01", "Note excerpt.", category="Note", Tag="misc"),
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("blog")
    home = base / "home"
    home.mkdir()
    assert run_kb4it("create", "blog", "repo", cwd=base, home=home).returncode == 0
    repo = base / "repo"
    cfg = repo / "config" / "repo.json"
    conf = json.loads(cfg.read_text())
    conf.update(index_posts=2, strict=True)
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    for name, text in PAGES.items():
        (repo / "source" / name).write_text(text, encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"base": base, "home": home, "cfg": cfg, "target": repo / "target", "log": result.stdout}


def read(site, name):
    return (site["target"] / name).read_text(encoding="utf-8")


def test_build_is_clean(site):
    assert "ERROR |" not in site["log"]
    assert "INDEX_SKIP" not in site["log"]
    for name in PAGES:
        assert (site["target"] / name.replace(".md", ".html")).exists()


def test_index_shows_the_newest_posts_with_excerpts(site):
    html = read(site, "index.html")
    assert "Third post" in html and "Excerpt missing" in html
    assert "Second post" in html and "Fresh excerpt." in html
    assert "First post" not in html


def test_archive_lists_every_year(site):
    html = read(site, "events.html")
    assert "2025" in html and "2026" in html


def test_metadata_pages(site):
    html = read(site, "Tag_python.html")
    assert "first.html" in html and "second.html" in html and "third.html" not in html
    assert "second.html" in read(site, "Topic_Development.html")
    for name in ("properties.html", "stats.html", "all.html", "bookmarks.html", "Tag.html"):
        assert (site["target"] / name).exists(), name


def test_post_and_note_pages(site):
    assert "Fresh excerpt." in read(site, "second.html")
    assert "Document last update" in read(site, "second.html")   # post layout, without an Author
    assert "Ann" in read(site, "first.html")
    assert "Note excerpt." in read(site, "note.html")


def test_unchanged_rebuild_reuses_the_cached_pages(site):
    before = read(site, "index.html")
    result = run_kb4it("build", site["cfg"], cwd=site["base"], home=site["home"])
    assert result.returncode == 0, result.stdout
    assert "compiled=0" in result.stdout
    assert read(site, "index.html") == before
    assert (site["target"] / "events.html").exists()
