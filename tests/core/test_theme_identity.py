"""Themes carry their own version and a fingerprint of their files; a theme change rebuilds the site (TV)."""

import importlib.util
import json
import shutil
import subprocess

import pytest

from kb4it.core.version import theme_fingerprint, theme_identity
from tests.helpers import ROOT, mini_theme, page, run_kb4it, write_repo

THEMES = ROOT / "kb4it" / "resources" / "themes"
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def test_fingerprint_follows_the_files_that_shape_pages(tmp_path):
    theme = mini_theme(tmp_path / "mini")
    shared = tmp_path / "common"
    shared.mkdir()
    (shared / "A.tpl").write_text("a", encoding="utf-8")
    first = theme_fingerprint(theme, shared)
    assert len(first) == 12 and first == theme_fingerprint(theme, shared)

    (theme / "apps" / "default").mkdir(parents=True)
    (theme / "apps" / "default" / "x.md").write_text("x", encoding="utf-8")
    (theme / "logic" / "__pycache__").mkdir()
    (theme / "logic" / "__pycache__" / "theme.cpython-311.pyc").write_bytes(b"\0")
    assert theme_fingerprint(theme, shared) == first, "apps/ and caches never shape a page"

    (shared / "A.tpl").write_text("b", encoding="utf-8")
    second = theme_fingerprint(theme, shared)
    assert second != first, "a shared template counts"

    (theme / "templates" / "PAGE_INDEX.tpl").rename(theme / "templates" / "PAGE_HOME.tpl")
    assert theme_fingerprint(theme, shared) != second, "a renamed file counts"


def test_identity():
    assert theme_identity("techdoc", "1.0.0", "abc") == "techdoc 1.0.0+abc"
    assert theme_identity("mine", None, "abc") == "mine unversioned+abc"


def test_every_tracked_theme_declares_its_own_version():
    tracked = subprocess.run(["git", "ls-files", "kb4it/resources/themes/*/theme.json"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8").stdout.split()
    if not tracked:
        pytest.skip("not a git checkout")
    for rel in tracked:
        version = json.loads((ROOT / rel).read_text(encoding="utf-8")).get("version")
        assert version and version.count(".") == 2 and "+" not in version, f"{rel}: version {version!r}"


def build(tmp_path, home, theme, *args):
    cfg = tmp_path / "repo" / "config" / "repo.json"
    if not cfg.exists():
        cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="y")},
                         theme_path=str(theme))
    return run_kb4it("-L", "DEBUG", "build", *args, cfg, cwd=tmp_path, home=home)


def test_theme_change_rebuilds_every_page(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", version="2.3.4")
    first = build(tmp_path, home, theme)
    assert first.returncode == 0, first.stdout
    assert "THEME_LOADED id=mini version=2.3.4 fingerprint=" in first.stdout
    assert "theme=mini/2.3.4+" in first.stdout

    again = build(tmp_path, home, theme)
    assert "compiled=0" in again.stdout and "CORE_SIGNATURE_CHANGED" not in again.stdout

    body = theme / "templates" / "HTML_BODY.tpl"
    body.write_text(body.read_text(encoding="utf-8") + "\n<!-- changed -->\n", encoding="utf-8")
    changed = build(tmp_path, home, theme)
    assert changed.returncode == 0, changed.stdout
    assert "CORE_SIGNATURE_CHANGED" in changed.stdout
    assert "compiled=2" in changed.stdout


def test_theme_without_a_version_still_builds(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    conf = json.loads((theme / "theme.json").read_text(encoding="utf-8"))
    del conf["version"]
    (theme / "theme.json").write_text(json.dumps(conf), encoding="utf-8")
    result = build(tmp_path, home, theme)
    assert result.returncode == 0, result.stdout
    assert "THEME_VERSION_MISSING id=mini" in result.stdout
    assert "theme=mini/unversioned+" in result.stdout


@pytest.mark.parametrize("version", ["one", "1.0", "1.0.0+local"])
def test_theme_with_a_bad_version_is_refused(tmp_path, home, version):
    theme = mini_theme(tmp_path / "mini", version=version)
    result = build(tmp_path, home, theme)
    assert result.returncode != 0
    assert "version" in result.stdout


def test_themes_listing_shows_version_fingerprint_and_where_a_theme_comes_from(tmp_path, home):
    user_copy = home / ".kb4it" / "opt" / "resources" / "themes" / "techdoc"
    shutil.copytree(THEMES / "techdoc", user_copy, ignore=shutil.ignore_patterns("__pycache__"))
    result = run_kb4it("themes", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    lines = [line for line in result.stdout.splitlines() if "[FRONTEND] THEME " in line]
    blog = next(line for line in lines if "id=blog" in line)
    assert "scope=builtin" in blog and "version=1.0.0" in blog and "fingerprint=" in blog
    assert f"path={THEMES / 'blog'}" in blog
    techdoc = [line for line in lines if "id=techdoc" in line]
    assert any("scope=user" in line and f"path={user_copy}" in line for line in techdoc), techdoc


def load_check_themes():
    spec = importlib.util.spec_from_file_location("check_themes", ROOT / "scripts" / "devel" / "check_themes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    import os
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "HOME": str(repo), "PATH": os.environ["PATH"]})


@needs_git
def test_release_check_wants_a_new_version_for_a_changed_theme(tmp_path):
    repo = tmp_path / "checkout"
    theme = repo / "kb4it" / "resources" / "themes" / "demo"
    (theme / "templates").mkdir(parents=True)
    (theme / "apps" / "default").mkdir(parents=True)
    (theme / "theme.json").write_text(json.dumps({"id": "demo", "version": "1.0.0"}), encoding="utf-8")
    (theme / "templates" / "A.tpl").write_text("a", encoding="utf-8")
    (theme / "apps" / "default" / "x.md").write_text("x", encoding="utf-8")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "one")
    git(repo, "tag", "v1.0.0")

    check = load_check_themes()
    check.ROOT = repo
    assert check.previous_release("HEAD", "1.1.0") == "v1.0.0"

    (theme / "apps" / "default" / "x.md").write_text("y", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "sample only")
    assert check.check_version_bump("demo", "1.0.0", "HEAD", "v1.0.0") == [], "apps/ is not the theme"

    (theme / "templates" / "A.tpl").write_text("b", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "template")
    problems = check.check_version_bump("demo", "1.0.0", "HEAD", "v1.0.0")
    assert problems and "templates/A.tpl" in problems[0] and "still 1.0.0" in problems[0]
    assert check.check_version_bump("demo", "1.1.0", "HEAD", "v1.0.0") == []
