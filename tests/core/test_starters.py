"""Starter themes (kb4it/resources/starters/): each builds its sample app cleanly from a copy."""

import json
import re
import shutil

import pytest

from tests.helpers import ROOT, run_kb4it

STARTERS = ROOT / "kb4it" / "resources" / "starters"


@pytest.mark.parametrize("name", ["starter-docs", "starter-plain"])
def test_starter_builds(tmp_path, home, name):
    theme = tmp_path / "themes" / name
    shutil.copytree(STARTERS / name, theme)
    repo = tmp_path / "site"
    shutil.copytree(theme / "apps" / "default", repo)
    cfg = repo / "config" / "repo.json"
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf.update(theme=name, theme_path=str(theme), source="source", target="target")
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert (repo / "target" / "index.html").is_file()
    warnings = [line for line in result.stdout.splitlines() if " WARNING " in line or " ERROR " in line]
    assert warnings == []


@pytest.mark.parametrize("name", ["starter-docs", "starter-plain"])
def test_starter_theme_json(name):
    conf = json.loads((STARTERS / name / "theme.json").read_text(encoding="utf-8"))
    assert conf["id"] == name and re.fullmatch(r"\d+\.\d+\.\d+", conf["version"]) and conf["kb4it"] == ">=0.12.0"
    assert conf["autoescape"] is True


def test_starters_are_not_listed_as_themes(tmp_path, home):
    result = run_kb4it("themes", cwd=tmp_path, home=home)
    assert "starter-" not in result.stdout
