"""The target folder may not overlap the repository, the source, the home folder or a filesystem root (FS-01)."""

import json
import os

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.paths import check_target
from tests.helpers import page, run_kb4it, write_repo


@pytest.fixture
def layout(tmp_path):
    root = tmp_path / "repo"
    source = root / "source"
    for folder in (source, root / "config", root / "var", tmp_path / "home"):
        folder.mkdir(parents=True)
    return root, source, tmp_path / "home"


@pytest.mark.parametrize("target, protected", [
    ("", "repository root"),
    ("source", "source folder"),
    ("config", "config folder"),
    ("var", "var folder"),
    ("..", "repository root"),
])
def test_forbidden_targets_are_refused(layout, target, protected):
    root, source, home = layout
    with pytest.raises(ConfigError) as error:
        check_target(root / target, root, source, home)
    message = str(error.value)
    assert protected in message and str(root / target) in message


def test_home_folder_is_refused(layout):
    root, source, home = layout
    with pytest.raises(ConfigError, match="home folder"):
        check_target(home, root, source, home)
    elsewhere = home.parent / "other"
    (elsewhere / "home").mkdir(parents=True)
    with pytest.raises(ConfigError, match="home folder"):
        check_target(elsewhere, root, source, elsewhere / "home")


def test_filesystem_root_is_refused(layout):
    root, source, home = layout
    anchor = os.path.splitdrive(str(root))[0] + os.sep
    with pytest.raises(ConfigError, match="filesystem root"):
        check_target(anchor, root, source, home)


def test_target_inside_source_is_refused(layout):
    root, source, home = layout
    with pytest.raises(ConfigError, match="inside the source folder"):
        check_target(source / "site", root, source, home)


@pytest.mark.parametrize("target", ["target", "public/site", "var/www/site"])
def test_nested_targets_are_accepted(layout, target):
    root, source, home = layout
    check_target(root / target, root, source, home)


def test_target_outside_the_repository_is_accepted(layout, tmp_path):
    root, source, home = layout
    check_target(tmp_path / "site", root, source, home)


def test_target_dot_deletes_nothing(tmp_path, home):
    """The audit reproduction of COR-03: "target": "." swept the repository."""
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": page("A", Tag="x")}, target=".")
    keep = repo / "notes.html"
    keep.write_text("mine", encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode != 0
    assert "holds the repository root" in result.stdout
    assert keep.read_text(encoding="utf-8") == "mine"
    assert (repo / "source" / "a.md").is_file()
    assert json.loads(cfg.read_text(encoding="utf-8"))["target"] == "."
