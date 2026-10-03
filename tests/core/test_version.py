import re
from pathlib import Path

import pytest

from kb4it.core.version import parse_version, requirement_satisfied
from tests.helpers import ROOT, mini_theme, page, run_kb4it, write_repo


@pytest.mark.parametrize("text, expected", [
    ("0.7.10", (0, 7, 10)),
    ("0.8", (0, 8, 0)),
    ("1.2.3+build.4", (1, 2, 3)),
    (" 0.7.9\n", (0, 7, 9)),
])
def test_parse_version(text, expected):
    assert parse_version(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "0.7.x", "v0.7.9"])
def test_parse_version_rejects(text):
    with pytest.raises(ValueError):
        parse_version(text)


@pytest.mark.parametrize("spec, version, ok", [
    (">=0.7.9", "0.7.10", True),
    (">=0.7.10", "0.7.9", False),
    (">=0.8", "0.7.10", False),
    (">=0.7.9, <0.8", "0.7.10", True),
    (">=0.7.9, <0.8", "0.8.0", False),
    ("==0.7.10", "0.7.10", True),
    ("!=0.7.10", "0.7.10", False),
    (">0.7", "0.7.0", False),
    ("<=0.7.10", "0.7.10+build.3", True),
    ("0.7.9", "0.7.10", True),
])
def test_requirement_satisfied(spec, version, ok):
    assert requirement_satisfied(spec, version) is ok


@pytest.mark.parametrize("spec", ["", "~=0.7", ">=", ">=0.x"])
def test_requirement_rejects_bad_spec(spec):
    with pytest.raises(ValueError):
        requirement_satisfied(spec, "0.7.10")


def test_version_files_agree():
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text()).group(1)
    assert version == pyproject
    parse_version(version)
    assert "+" not in version


def test_theme_requiring_a_newer_kb4it_is_refused(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", kb4it=">=99.0")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode != 0
    assert "THEME_REQUIREMENT_UNMET id=mini requires=>=99.0" in result.stdout


def test_theme_with_a_bad_requirement_is_refused(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", kb4it="newest")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode != 0
    assert "THEME_REQUIREMENT_INVALID id=mini requires=newest" in result.stdout


def test_version_flag_shows_git_describe_in_a_checkout(home):
    result = run_kb4it("--version", cwd=home, home=home)
    assert result.returncode == 0
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    assert result.stdout.startswith(f"KB4IT {version}")
    if (ROOT / ".git").exists():
        assert "(v" in result.stdout or "(" in result.stdout


def test_every_tracked_theme_declares_a_requirement_this_version_meets():
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    import json
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "kb4it/resources/themes/*/theme.json"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
    assert tracked
    for rel in tracked:
        spec = json.loads((ROOT / rel).read_text(encoding="utf-8")).get("kb4it")
        assert spec, f"{rel} has no kb4it requirement"
        assert requirement_satisfied(spec, version), f"{rel} requires {spec}, this is {version}"
