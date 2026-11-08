"""kb4it new-theme: copy a starter theme under a new id (Part D)."""

import json
import shutil

import pytest

from kb4it.core.exceptions import ThemeError
from kb4it.core.newtheme import create_theme
from tests.helpers import run_kb4it


def _conf(folder):
    return json.loads((folder / "theme.json").read_text(encoding="utf-8"))


def test_creates_docs_starter(tmp_path):
    folder = create_theme("mytheme", dest=str(tmp_path))
    theme = tmp_path / "mytheme"
    assert folder == str(theme)
    assert _conf(theme)["id"] == "mytheme" and _conf(theme)["name"] == "Mytheme"
    assert "class Theme(BaseTheme)" in (theme / "logic" / "theme.py").read_text(encoding="utf-8")
    sample = json.loads((theme / "apps" / "default" / "config" / "repo.json").read_text(encoding="utf-8"))
    assert sample["theme"] == "mytheme"


def test_creates_plain_starter(tmp_path):
    create_theme("notes", plain=True, dest=str(tmp_path))
    assert "class Theme(BaseTheme)" in (tmp_path / "notes" / "logic" / "theme.py").read_text(encoding="utf-8")
    assert _conf(tmp_path / "notes")["id"] == "notes"


def test_refuses_existing_dir(tmp_path):
    (tmp_path / "mytheme").mkdir()
    (tmp_path / "mytheme" / "keep.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(ThemeError, match="exists"):
        create_theme("mytheme", dest=str(tmp_path))
    assert [p.name for p in (tmp_path / "mytheme").iterdir()] == ["keep.txt"]


@pytest.mark.parametrize("theme_id", ["..", "a/b", "Bad", "", "../escape"])
def test_refuses_bad_id(tmp_path, theme_id):
    """Review Focus 5: nothing is written for an unsafe id."""
    parent = tmp_path / "themes"
    parent.mkdir()
    with pytest.raises(ThemeError):
        create_theme(theme_id, dest=str(parent))
    assert list(parent.iterdir()) == [] and sorted(p.name for p in tmp_path.iterdir()) == ["themes"]


def test_refuses_bundled_id(tmp_path):
    with pytest.raises(ThemeError, match="bundled"):
        create_theme("techdoc", dest=str(tmp_path))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("plain", [False, True])
def test_created_theme_builds_its_sample_app(tmp_path, home, plain):
    folder = tmp_path / "themes"
    create_theme("mine", plain=plain, dest=str(folder))
    site = tmp_path / "site"
    shutil.copytree(folder / "mine" / "apps" / "default", site)
    cfg = site / "config" / "repo.json"
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["theme_path"] = str(folder / "mine")
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert " WARNING " not in result.stdout and " ERROR " not in result.stdout
    html = (site / "target" / "index.html").read_text(encoding="utf-8")
    assert "starter-" not in html, "no link names the starter's id"


def test_cli_exit_codes(tmp_path, home):
    result = run_kb4it("new-theme", "mytheme", str(tmp_path / "t"), cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert f"Theme mytheme created in {tmp_path / 't' / 'mytheme'}" in result.stdout
    again = run_kb4it("new-theme", "mytheme", str(tmp_path / "t"), cwd=tmp_path, home=home)
    assert again.returncode == 1 and "exists" in again.stdout
    plain = run_kb4it("new-theme", "--plain", "notes", str(tmp_path / "t"), cwd=tmp_path, home=home)
    assert plain.returncode == 0 and (tmp_path / "t" / "notes" / "logic" / "theme.py").is_file()


def test_cli_default_folder_is_the_user_themes(tmp_path, home):
    result = run_kb4it("new-theme", "mytheme", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert (home / ".kb4it" / "opt" / "resources" / "themes" / "mytheme" / "theme.json").is_file()


def test_cli_next_step_builds_with_the_new_theme(tmp_path, home):
    assert run_kb4it("new-theme", "mytheme", cwd=tmp_path, home=home).returncode == 0
    created = run_kb4it("create", "mytheme", "default", str(tmp_path / "site"), "--index", "no", cwd=tmp_path, home=home)
    assert created.returncode == 0, created.stdout
    built = run_kb4it("build", str(tmp_path / "site" / "config" / "repo.json"), cwd=tmp_path, home=home)
    assert built.returncode == 0, built.stdout
    assert (tmp_path / "site" / "target" / "index.html").is_file()
