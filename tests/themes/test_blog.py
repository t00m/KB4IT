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
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf.update(index_posts=2, strict=True)
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    for sample in (repo / "source").glob("*.md"):
        sample.unlink()
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


def test_stats_page(site):
    """Totals, activity and property coverage; Summary is not counted."""
    html = read(site, "stats.html")
    for anchor in ("stats-activity", "stats-coverage", "stats-health", "stats-links"):
        assert f'id="{anchor}"' in html, anchor  # every section is a card
    assert 'id="stats-coverage-details"' in html  # its details open in a modal
    assert 'href="Tag.html"' in html and 'href="Summary.html"' not in html


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


def test_event_pages_are_rebuilt_only_when_needed(tmp_path):
    """An unchanged build reuses every event page; a deleted post leaves the day it shared."""
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "blog", "repo", cwd=tmp_path, home=home).returncode == 0
    repo = tmp_path / "repo"
    cfg = repo / "config" / "repo.json"
    for name in list((repo / "source").glob("*.md")):
        name.unlink()
    (repo / "source" / "a.md").write_text(post("Post A", "2026-05-10", Tag="x"), encoding="utf-8")
    (repo / "source" / "b.md").write_text(post("Post B", "2026-05-10", Tag="x"), encoding="utf-8")
    (repo / "source" / "c.md").write_text(post("Post C", "2026-06-20", Tag="x"), encoding="utf-8")
    first = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    assert first.returncode == 0, first.stdout
    assert "EVENT_PAGES built=5 reused=0" in first.stdout  # two days, two months, one year

    again = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    assert again.returncode == 0, again.stdout
    assert "EVENT_PAGES built=0 reused=5" in again.stdout

    (repo / "source" / "b.md").unlink()
    third = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    assert third.returncode == 0, third.stdout
    assert "EVENT_PAGES built=3 reused=2" in third.stdout  # 2026-05-10, May and 2026
    day = (repo / "target" / "events_20260510.html").read_text(encoding="utf-8")
    assert "Post A" in day and "Post B" not in day
