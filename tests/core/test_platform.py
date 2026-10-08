"""KB4IT starts on any operating system; the platform is described, never checked."""

import platform

import pytest

from kb4it.core import env


@pytest.mark.parametrize("name, family", [
    ("linux", "linux"), ("darwin", "darwin"), ("win32", "windows"), ("cygwin", "windows"), ("freebsd14", "other"),
])
def test_platform_family(name, family):
    assert env.platform_family(name) == family


def test_description_without_os_release(monkeypatch):
    def missing():
        raise OSError("no os-release")
    monkeypatch.setattr(platform, "freedesktop_os_release", missing)
    monkeypatch.setattr(platform, "platform", lambda: "macOS-14.5-arm64-arm-64bit")
    assert env.platform_description() == "macOS-14.5-arm64-arm-64bit"


def test_description_with_os_release(monkeypatch):
    monkeypatch.setattr(platform, "freedesktop_os_release", lambda: {"PRETTY_NAME": "Debian GNU/Linux 13"})
    assert env.platform_description() == "Debian GNU/Linux 13"


def test_env_records_the_platform():
    assert env.ENV["SYS"]["PLATFORM"]["FAMILY"] in ("linux", "darwin", "windows", "other")
    assert env.ENV["SYS"]["PLATFORM"]["OS"]
    assert env.ENV["SYS"]["PS"]["NAME"]
