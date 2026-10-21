"""The first-run help notice: stderr only, once per run, hidden by dismiss or CI."""

from kb4it.core.notice import HELP_ONLINE_URL, MARKER_NAME
from tests.helpers import run_kb4it

NO_CI = {"CI": ""}


def test_first_run_prints_the_notice_on_stderr(tmp_path, home):
    first = run_kb4it("themes", cwd=tmp_path, home=home, env=NO_CI, split_streams=True)
    assert "kb4it help" in first.stderr
    assert "kb4it help" not in first.stdout
    run_kb4it("help", "--dismiss", cwd=tmp_path, home=home, env=NO_CI)
    dismissed = run_kb4it("themes", cwd=tmp_path, home=home, env=NO_CI, split_streams=True)
    assert first.stdout == dismissed.stdout


def test_notice_is_not_printed_when_dismissed(tmp_path, home):
    before = run_kb4it("themes", cwd=tmp_path, home=home, env=NO_CI, split_streams=True)
    assert "kb4it help" in before.stderr
    dismiss = run_kb4it("help", "--dismiss", cwd=tmp_path, home=home, env=NO_CI)
    assert dismiss.returncode == 0, dismiss.stdout
    assert (home / ".kb4it" / MARKER_NAME).exists()
    after = run_kb4it("themes", cwd=tmp_path, home=home, env=NO_CI, split_streams=True)
    assert "kb4it help" not in after.stderr
    assert "kb4it help" not in after.stdout


def test_notice_is_not_printed_under_ci(tmp_path, home):
    result = run_kb4it("themes", cwd=tmp_path, home=home, env={"CI": "true"}, split_streams=True)
    assert "kb4it help" not in result.stderr
    assert not (home / ".kb4it" / MARKER_NAME).exists()


def test_help_action_does_not_print_the_notice(tmp_path, home):
    result = run_kb4it("help", "--url", cwd=tmp_path, home=home, env=NO_CI, split_streams=True)
    assert result.stdout.strip() == HELP_ONLINE_URL
    assert result.stderr.strip() == ""


def test_notice_that_cannot_read_kb4it_home_does_not_stop_the_command(monkeypatch, capsys):
    # On Python 3.11, Path.exists() raises PermissionError when KB4IT_HOME cannot be searched;
    # later versions return False. Simulate the 3.11 case so the test runs on every version.
    import sys

    import pytest

    from kb4it.core import main as cli
    from kb4it.core import notice

    def unreadable():
        raise PermissionError(13, "Permission denied", "/unreadable/help-notice-dismissed")

    monkeypatch.setattr(notice, "help_notice_dismissed", unreadable)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(sys, "argv", ["kb4it", "themes"])
    with pytest.raises(SystemExit) as stop:
        cli.main()
    assert stop.value.code == 0, capsys.readouterr().out
