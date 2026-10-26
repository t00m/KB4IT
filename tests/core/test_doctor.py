"""'kb4it doctor' reports the build, the paths and the themes, and fails when a bundled part is missing (SI-07)."""

import shutil
import subprocess

import pytest

from kb4it.core import doctor
from kb4it.core.env import ENV
from tests.helpers import ROOT, run_kb4it


def test_bundled_themes_are_the_tracked_themes():
    listed = subprocess.run(["git", "ls-files", "kb4it/resources/themes/*/theme.json"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8").stdout.split()
    if not listed:
        pytest.skip("not a git checkout")
    assert tuple(sorted(rel.split("/")[3] for rel in listed)) == doctor.BUNDLED_THEMES


def test_doctor_reports_the_build_and_every_theme(tmp_path, home):
    result = run_kb4it("doctor", cwd=tmp_path, home=home, split_streams=True)
    assert result.returncode == 0, result.stdout + result.stderr
    out = result.stdout
    assert f"KB4IT      {ENV['APP']['build_version']}" in out
    assert "Python     " in out and f"Package    {ENV['CONF']['ROOT']}" in out
    for theme in doctor.BUNDLED_THEMES:
        assert f"  {theme} 1.0.0+" in out
    assert "No problems found." in out


def test_doctor_shows_a_user_copy_that_hides_a_bundled_theme(tmp_path, home):
    copy = home / ".kb4it" / "opt" / "resources" / "themes" / "blog"
    shutil.copytree(ROOT / "kb4it" / "resources" / "themes" / "blog", copy, ignore=shutil.ignore_patterns("__pycache__"))
    result = run_kb4it("doctor", cwd=tmp_path, home=home, split_streams=True)
    assert result.returncode == 0
    assert any("user" in line and str(copy) in line and "hides the built-in theme" in line
               for line in result.stdout.splitlines())


def test_doctor_fails_on_a_missing_bundled_part(monkeypatch, tmp_path):
    package = tmp_path / "kb4it"
    (package / "resources" / "themes" / "blog").mkdir(parents=True)
    (package / "resources" / "themes" / "blog" / "theme.json").write_text('{"id": "blog", "version": "1.0.0"}',
                                                                         encoding="utf-8")
    patched = {**ENV["CONF"], "ROOT": str(package)}
    gpath = {**ENV["GPATH"], "THEMES": str(package / "resources" / "themes")}
    lpath = {**ENV["LPATH"], "THEMES": str(tmp_path / "none")}
    app = {**ENV["APP"], "build": {**ENV["APP"]["build"], "source": "dev"}}
    monkeypatch.setattr(doctor, "ENV", {**ENV, "CONF": patched, "GPATH": gpath, "LPATH": lpath, "APP": app})
    _lines, problems = doctor.report()
    text = "\n".join(problems)
    assert "offline help missing" in text  # no git checkout next to this package
    assert "editor files missing" in text and "render files missing" in text
    assert "theme blog" in text and "logic/theme.py is missing" in text
    assert "bundled theme missing: techdoc" in text
