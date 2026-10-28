"""dateModified: the Modified key, the last git commit, the file time, never before Date."""

import os
import shutil
import subprocess
from datetime import datetime

import pytest

from kb4it.core.moddates import file_time, git_dates, modified_date, parse_log, with_zone

HAS_GIT = shutil.which("git") is not None


def test_modified_key_wins():
    assert modified_date("2026-10-25", "2026-10-01", "2026-10-27T10:00:00+00:00", "") == "2026-10-25"


def test_git_date_then_file_time():
    assert modified_date("", "2026-10-01", "2026-10-27T10:00:00+00:00", "2026-10-28T10:00:00+00:00") == \
        "2026-10-27T10:00:00+00:00"
    assert modified_date("", "", "", "2026-10-28T10:00:00+00:00") == "2026-10-28T10:00:00+00:00"


def test_never_older_than_date():
    assert modified_date("2026-01-01", "2026-10-01", "", "") == "2026-10-01"
    assert modified_date("", "2026-10-01 14:30", "2026-09-01T10:00:00+00:00", "") == with_zone("2026-10-01T14:30:00")


def test_bad_modified_falls_back():
    assert modified_date("someday", "", "2026-10-27T10:00:00+00:00", "") == "2026-10-27T10:00:00+00:00"


def test_with_zone_adds_the_local_offset_to_a_time_only():
    assert with_zone("2026-10-23") == "2026-10-23"
    assert datetime.fromisoformat(with_zone("2026-10-23T14:30:00")).tzinfo is not None


def test_file_time(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("x", encoding="utf-8")
    os.utime(path, (1761300000, 1761300000))
    assert datetime.fromisoformat(file_time(str(path))).timestamp() == 1761300000
    assert file_time(str(tmp_path / "missing.md")) == ""


def test_parse_log_keeps_the_newest_commit_and_flat_files():
    text = "\x002026-10-27T10:00:00+00:00\n\na.md\n\x002026-10-20T10:00:00+00:00\n\na.md\nb.md\nsub/c.md\n"
    assert parse_log(text) == {"a.md": "2026-10-27T10:00:00+00:00", "b.md": "2026-10-20T10:00:00+00:00"}


def test_no_git_work_tree(tmp_path):
    assert git_dates(str(tmp_path), str(tmp_path / "cache.json")) == {}


def _git(repo, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@x")
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)


@pytest.mark.skipif(not HAS_GIT, reason="git is not installed")
def test_git_dates_and_cache(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _git(tmp_path, "init", "-q")
    (source / "a.md").write_text("one", encoding="utf-8")
    (source / "b.md").write_text("one", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "one", date="2026-10-20T10:00:00+02:00")
    (source / "a.md").write_text("two", encoding="utf-8")
    _git(tmp_path, "commit", "-q", "-am", "two", date="2026-10-27T10:00:00+02:00")
    cache = tmp_path / "var" / "gitdates.json"
    cache.parent.mkdir()
    dates = git_dates(str(source), str(cache))
    assert dates == {"a.md": "2026-10-27T10:00:00+02:00", "b.md": "2026-10-20T10:00:00+02:00"}
    assert cache.exists()
    assert git_dates(str(source), str(cache)) == dates
