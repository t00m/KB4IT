import json
import shutil

import pytest

from tests.helpers import APPHELP, page, run_kb4it

PREFIX = "window.APPHELP_INDEX = "


def index_records(target):
    text = (target / "search-index.js").read_text(encoding="utf-8")
    return json.loads(text[len(PREFIX):-2])


@pytest.fixture
def scaffold(tmp_path, home):
    created = run_kb4it("create", "apphelp", tmp_path / "repo", cwd=tmp_path, home=home)
    assert created.returncode == 0, created.stdout
    repo = tmp_path / "repo"
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=home, home=home)
    assert result.returncode == 0, result.stdout
    return repo, result


def test_scaffold_builds_clean(scaffold):
    repo, result = scaffold
    for word in ("WARNING", "ERROR"):
        assert f" {word} " not in result.stdout, result.stdout
    expected = sorted(p.name for p in (APPHELP / "apps" / "default" / "source").iterdir())
    assert sorted(p.name for p in (repo / "source").iterdir()) == expected
    assert (repo / "target" / "faq.html").read_text().count('<details class="ah-faq"') >= 3
    assert (repo / "target" / "resources" / "images" / "screenshot.svg").exists()


def test_body_edit_updates_index(scaffold, home):
    repo, _ = scaffold
    before = index_records(repo / "target")
    path = repo / "source" / "howto-search.md"
    path.write_text(path.read_text() + "\nThe word zanzibar appears here.\n")
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=home, home=home)
    assert result.returncode == 0, result.stdout
    after = index_records(repo / "target")
    assert len(after) == len(before)
    assert "zanzibar" in json.dumps(after)


def test_new_page_appears_in_unchanged_pages(scaffold, home):
    repo, _ = scaffold
    (repo / "source" / "howto-new.md").write_text(page(
        "A new page", DocType="How-to guide", Section="How-to", Order="130", Summary="New.", Feature="Search"))
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=home, home=home)
    assert result.returncode == 0, result.stdout
    assert 'href="howto-new.html"' in (repo / "target" / "faq.html").read_text()


def test_deleted_page_disappears_everywhere(scaffold, home):
    repo, _ = scaffold
    (repo / "source" / "howto-search.md").unlink()
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=home, home=home)
    assert result.returncode == 0, result.stdout
    target = repo / "target"
    assert not (target / "howto-search.html").exists()
    assert "howto-search.html" not in (target / "faq.html").read_text()
    assert "howto-search.html" not in (target / "search-index.js").read_text()
    assert "howto-search.html" not in (target / "helpids.js").read_text()


def test_moved_repository_still_builds(scaffold, tmp_path, home):
    repo, _ = scaffold
    moved = tmp_path / "moved"
    shutil.move(str(repo), str(moved))
    result = run_kb4it("build", moved / "config" / "repo.json", cwd=home, home=home)
    assert result.returncode == 0, result.stdout
