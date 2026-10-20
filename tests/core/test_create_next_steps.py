import json
import re

from tests.helpers import run_kb4it


def test_create_prints_three_next_steps(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    lines = [line for line in result.stdout.splitlines() if line.startswith(("Your knowledge base", "Write documents", "Preview the site"))]
    assert len(lines) == 3
    assert "HINT" not in result.stdout


def test_create_path_with_spaces_and_unicode(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = run_kb4it("create", "techdoc", "mi base ñ", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert str(tmp_path / "mi base ñ" / "config" / "repo.json") in result.stdout


def test_create_bookshelf_prints_steps(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = run_kb4it("create", "bookshelf", "repo", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "Preview the site with: kb4it serve" in result.stdout


def test_create_into_existing_repo_uses_requested_theme(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    assert run_kb4it("create", "blog", "repo", cwd=tmp_path, home=home).returncode == 0
    conf = json.loads((tmp_path / "repo" / "config" / "repo.json").read_text(encoding="utf-8"))
    assert conf["theme"] == "blog"


def test_tutorial_no_longer_linux_only():
    text = open("help/source/getting-started.md", encoding="utf-8").read()
    assert "GNU/Linux computer" not in text
    assert re.search(r"KB4IT \d+\.\d+", text) is None
