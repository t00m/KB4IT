"""First-run help notice: text, offline index lookup and dismiss marker."""

from pathlib import Path

import pytest

from kb4it.core import notice
from kb4it.core.env import ENV
from kb4it.core.notice import HELP_ONLINE_URL, help_notice_lines


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(tmp_path))
    return tmp_path


def test_notice_names_the_command_and_the_urls():
    text = "\n".join(help_notice_lines(Path("/x/index.html"), HELP_ONLINE_URL))
    assert "kb4it help" in text
    assert "kb4it help --dismiss" in text
    assert "/x/index.html" in text
    assert HELP_ONLINE_URL in text


def test_notice_is_short():
    assert len(help_notice_lines(Path("/x/index.html"), HELP_ONLINE_URL)) <= 3


def test_dismiss_writes_the_marker_and_stops_the_notice(home):
    assert notice.help_notice_dismissed() is False
    notice.dismiss_help_notice()
    assert notice.help_notice_dismissed() is True


def test_marker_that_is_empty_still_counts(home):
    (home / "help-notice-dismissed").write_text("", encoding="utf-8")
    assert notice.help_notice_dismissed() is True


def test_offline_index_is_none_without_a_build(tmp_path, monkeypatch):
    monkeypatch.setenv("KB4IT_HELP_INDEX", str(tmp_path / "missing.html"))
    assert notice.offline_index() is None


def test_offline_index_uses_the_override_when_present(tmp_path, monkeypatch):
    index = tmp_path / "index.html"
    index.write_text("x", encoding="utf-8")
    monkeypatch.setenv("KB4IT_HELP_INDEX", str(index))
    assert notice.offline_index() == index


def test_relative_override_opens_a_file_url(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KB4IT_HELP_INDEX", "index.html")
    opened = []
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    assert notice.run_help() == 0
    assert opened == [(tmp_path / "index.html").resolve().as_uri()]


def test_override_that_is_not_html_is_ignored(tmp_path, monkeypatch):
    script = tmp_path / "run.sh"
    script.write_text("echo x", encoding="utf-8")
    monkeypatch.setenv("KB4IT_HELP_INDEX", str(script))
    assert notice.offline_index() is None
