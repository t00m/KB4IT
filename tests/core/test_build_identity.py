"""Every KB4IT build knows which commit it came from, and a different build recompiles the site (BI)."""

import json
import shutil
import subprocess
import sys

import pytest

from kb4it.core.env import ENV
from kb4it.core.version import BUILD_FILE, build_cache_key, build_info, build_version, git_info, read_build_file
from tests.helpers import ROOT, page, run_kb4it, write_repo

VERSION = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
SHA = "0a71990c" + "0" * 32
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def facts(**over):
    info = {"version": "1.2.3", "commit": SHA, "describe": "", "count": None, "branch": "main",
            "dirty": False, "diff_hash": "", "source": "dev"}
    info.update(over)
    return info


@pytest.mark.parametrize("over, expected", [
    ({"source": "release"}, "1.2.3"),
    ({"count": 42}, "1.2.3-dev+42.g0a71990"),
    ({}, "1.2.3-dev+g0a71990"),
    ({"count": 3, "dirty": True, "diff_hash": "abc"}, "1.2.3-dev+3.g0a71990.dirty"),
    ({"source": "release", "dirty": True}, "1.2.3-dev+g0a71990.dirty"),
    ({"commit": None, "source": "unknown"}, "1.2.3+unknown"),
])
def test_build_version(over, expected):
    assert build_version(facts(**over)) == expected


def test_dirty_builds_with_different_changes_do_not_share_a_cache():
    one = build_cache_key(facts(dirty=True, diff_hash="aaa"))
    two = build_cache_key(facts(dirty=True, diff_hash="bbb"))
    assert one != two
    assert build_cache_key(facts()) == "1.2.3-dev+g0a71990"


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "HOME": str(repo), "PATH": __import__("os").environ["PATH"]})


@needs_git
def test_git_info_of_a_checkout(tmp_path):
    repo = tmp_path / "checkout"
    (repo / "kb4it").mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    (repo / "kb4it" / "VERSION").write_text("1.2.3", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "one")
    git(repo, "tag", "v1.2.3")

    release = git_info(repo, "1.2.3")
    assert release["source"] == "release" and not release["dirty"]
    assert build_version(release) == "1.2.3"

    (repo / "a.txt").write_text("a", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-q", "-m", "two")
    dev = git_info(repo, "1.2.3")
    assert dev["count"] == 1 and dev["branch"] == "main"
    assert build_version(dev) == f"1.2.3-dev+1.g{dev['commit'][:7]}"

    (repo / "a.txt").write_text("b", encoding="utf-8")
    assert not git_info(repo, "1.2.3")["dirty"], "only changes to the package make a build dirty"
    (repo / "kb4it" / "VERSION").write_text("1.2.4", encoding="utf-8")
    dirty = git_info(repo, "1.2.3")
    assert dirty["dirty"] and dirty["diff_hash"]
    assert build_version(dirty).endswith(".dirty")


def test_git_info_outside_a_checkout(tmp_path):
    assert git_info(tmp_path, "1.2.3") is None


def test_build_file_is_used_by_an_installed_copy(tmp_path):
    package = tmp_path / "site-packages" / "kb4it"
    package.mkdir(parents=True)
    stamp = facts(version="1.2.3", count=5, date="2026-10-26T08:00:00Z")
    (package / BUILD_FILE).write_text(json.dumps(stamp), encoding="utf-8")
    info = build_info(package, "1.2.3")
    assert info["build_version"] == "1.2.3-dev+5.g0a71990"
    assert info["date"] == "2026-10-26T08:00:00Z"


def test_build_file_of_another_version_or_unreadable_is_ignored(tmp_path):
    (tmp_path / BUILD_FILE).write_text(json.dumps(facts(version="9.9.9")), encoding="utf-8")
    assert read_build_file(tmp_path, "1.2.3") is None
    (tmp_path / BUILD_FILE).write_text("{", encoding="utf-8")
    assert read_build_file(tmp_path, "1.2.3") is None
    assert build_info(tmp_path, "1.2.3")["build_version"] == "1.2.3+unknown"


def test_env_holds_the_release_and_the_build_version():
    assert ENV["APP"]["version"] == VERSION
    assert ENV["APP"]["build_version"].startswith(VERSION)
    assert ENV["APP"]["build"]["build_version"] == ENV["APP"]["build_version"]


def test_version_flag_names_the_commit(home):
    result = run_kb4it("--version", cwd=home, home=home)
    assert result.returncode == 0
    first, second = result.stdout.splitlines()[:2]
    assert first == f"KB4IT {ENV['APP']['build_version']}"
    if ENV["APP"]["build"]["commit"]:
        assert second.startswith(f"commit {ENV['APP']['build']['commit']}")
    else:
        assert second.startswith("commit unknown")


def test_another_build_of_the_same_version_recompiles_everything(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="y")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    kbdict_path = tmp_path / "repo" / "var" / "db" / "kbdict.json"
    kbdict = json.loads(kbdict_path.read_text(encoding="utf-8"))
    assert kbdict["kb4it_build"] == build_cache_key(ENV["APP"]["build"])

    unchanged = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert "compiled=0" in unchanged.stdout and "KBDICT_BUILD_MISMATCH" not in unchanged.stdout

    kbdict["kb4it_build"] = f"{VERSION}-dev+1.g1234567"
    kbdict_path.write_text(json.dumps(kbdict), encoding="utf-8")
    other = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert other.returncode == 0, other.stdout
    assert "KBDICT_BUILD_MISMATCH" in other.stdout
    assert "compiled=2" in other.stdout
    assert f"kb4it={ENV['APP']['build_version']}" in other.stdout


def test_generator_meta_names_the_build(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    html = (tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8")
    assert f'content="KB4IT {ENV["APP"]["build_version"]}' in html


@needs_git
def test_stamp_script_writes_the_build_file(tmp_path):
    work = tmp_path / "work"
    shutil.copytree(ROOT / "kb4it" / "core", work / "kb4it" / "core", ignore=shutil.ignore_patterns("__pycache__"))
    (work / "kb4it" / "__init__.py").write_text("", encoding="utf-8")
    (work / "kb4it" / "VERSION").write_text("1.2.3", encoding="utf-8")
    (work / "scripts" / "devel").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "devel" / "stamp_build.py", work / "scripts" / "devel")
    git(work, "init", "-q", "-b", "main")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "one")
    script = [sys.executable, str(work / "scripts" / "devel" / "stamp_build.py")]

    refused = subprocess.run([*script, "--require-release"], capture_output=True, text=True, encoding="utf-8")
    assert refused.returncode == 1 and "not a release build" in refused.stderr
    assert not (work / "kb4it" / BUILD_FILE).exists()

    git(work, "tag", "v1.2.3")
    done = subprocess.run([*script, "--require-release"], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    stamp = json.loads((work / "kb4it" / BUILD_FILE).read_text(encoding="utf-8"))
    assert stamp["build_version"] == "1.2.3" and stamp["source"] == "release" and stamp["date"].endswith("Z")
