"""The kb4it help command: --url, --dismiss and opening the offline index."""

import stat
import sys
from pathlib import Path

from kb4it.core.notice import HELP_ONLINE_URL
from tests.helpers import run_kb4it


def test_help_url_prints_the_online_address(tmp_path, home):
    result = run_kb4it("help", "--url", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert HELP_ONLINE_URL in result.stdout


def test_help_dismiss_hides_the_notice(tmp_path, home):
    control = run_kb4it("themes", cwd=tmp_path, home=home, env={"CI": ""}, split_streams=True)
    assert "kb4it help" in control.stderr
    first = run_kb4it("help", "--dismiss", cwd=tmp_path, home=home, env={"CI": ""})
    assert first.returncode == 0, first.stdout
    assert (home / ".kb4it" / "help-notice-dismissed").exists()
    second = run_kb4it("themes", cwd=tmp_path, home=home, env={"CI": ""}, split_streams=True)
    assert "kb4it help" not in second.stdout
    assert "kb4it help" not in second.stderr


def test_help_without_offline_copy_names_the_build_script(tmp_path, home):
    missing = tmp_path / "missing.html"
    result = run_kb4it("help", cwd=tmp_path, home=home, env={"KB4IT_HELP_INDEX": str(missing)})
    assert result.returncode == 1
    assert "scripts/help/build_offline.py" in result.stdout


def test_help_opens_the_offline_index(tmp_path, home):
    index_dir = tmp_path / "with space"
    index_dir.mkdir()
    index = index_dir / "index.html"
    index.write_text("<html></html>", encoding="utf-8")
    out = tmp_path / "opened.txt"
    browser = tmp_path / "fakebrowser.py"
    browser.write_text(
        f"#!{sys.executable}\nimport sys\nopen({str(out)!r}, 'w').write(sys.argv[1])\n", encoding="utf-8")
    browser.chmod(browser.stat().st_mode | stat.S_IEXEC)
    result = run_kb4it("help", cwd=tmp_path, home=home,
                       env={"KB4IT_HELP_INDEX": str(index), "BROWSER": f"{browser} %s"})
    assert result.returncode == 0, result.stdout
    for _ in range(50):
        if out.exists() and out.read_text(encoding="utf-8"):
            break
        import time
        time.sleep(0.1)
    opened = out.read_text(encoding="utf-8")
    assert opened.startswith("file://")
    assert "with%20space" in opened
    assert opened == index.as_uri()


def test_dismiss_on_unwritable_home_reports_an_error(tmp_path, home):
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    result = run_kb4it("help", "--dismiss", cwd=tmp_path, home=home, env={"KB4IT_HOME": str(blocker)})
    assert result.returncode == 1
    assert result.stdout.strip()
