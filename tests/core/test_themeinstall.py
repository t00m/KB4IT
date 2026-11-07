"""Install a theme from a zip file or an https URL, and uninstall it."""

import json
import os
import stat
import zipfile
from pathlib import Path

import pytest

from kb4it.core import themeinstall
from kb4it.core.themeinstall import ThemeInstallError, inspect_zip

MINI = Path(__file__).resolve().parents[1] / "fixtures" / "themes" / "mini"


def make_zip(path, files, symlinks=None, folders=()):
    """Write a zip at path with files {name: content} and symlinks {name: target}."""
    path = Path(path)
    with zipfile.ZipFile(path, "w") as archive:
        for name in folders:
            archive.writestr(zipfile.ZipInfo(name.rstrip("/") + "/"), b"")
        for name, content in files.items():
            archive.writestr(name, content)
        for name, target in (symlinks or {}).items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, target)
    return path


def mini_files(top="mini", **theme_json):
    """The mini theme's files under top/, with theme.json updated by theme_json."""
    files = {}
    for path in MINI.rglob("*"):
        if path.is_file():
            files[f"{top}/{path.relative_to(MINI).as_posix()}"] = path.read_bytes()
    data = json.loads((MINI / "theme.json").read_text(encoding="utf-8"))
    data.update(theme_json)
    files[f"{top}/theme.json"] = json.dumps(data)
    return files


def mini_zip(tmp_path, top="mini", name=None, **theme_json):
    """A zip of the mini theme under top/, with theme.json updated by theme_json."""
    return make_zip(tmp_path / (name or f"{top}.zip"), mini_files(top, **theme_json), folders=[top])


def reason_of(path):
    with pytest.raises(ThemeInstallError) as caught:
        inspect_zip(path)
    return caught.value


# inspect_zip

def test_valid_zip(tmp_path):
    result = inspect_zip(mini_zip(tmp_path))
    assert result.top == "mini"
    assert result.theme["id"] == "mini"


def test_zip_without_folder_entries_is_valid(tmp_path):
    path = make_zip(tmp_path / "t.zip", mini_files())
    assert inspect_zip(path).top == "mini"


def test_macosx_entries_are_ignored(tmp_path):
    files = mini_files()
    files["__MACOSX/mini/._theme.json"] = b"junk"
    result = inspect_zip(make_zip(tmp_path / "t.zip", files))
    assert result.top == "mini"
    assert not any(m.filename.startswith("__MACOSX/") for m in result.members)


def test_not_a_zip(tmp_path):
    path = tmp_path / "t.zip"
    path.write_text("hello", encoding="utf-8")
    assert reason_of(path).reason == "not_a_zip"


def test_two_top_folders(tmp_path):
    files = mini_files()
    files["other/readme.txt"] = "x"
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "layout"


def test_file_at_the_root(tmp_path):
    files = mini_files()
    files["readme.txt"] = "x"
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "layout"


@pytest.mark.parametrize("name", [
    "mini/../evil.txt",
    "/mini/abs.txt",
    "C:/mini/x.txt",
    "mini\\..\\..\\evil.txt",
])
def test_unsafe_names(tmp_path, name):
    files = mini_files()
    files[name] = "x"
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "unsafe_entry"


def test_dotdot_entry(tmp_path):
    files = mini_files()
    files["mini/templates/../../evil.txt"] = "x"
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "unsafe_entry"


def test_backslash_escape(tmp_path):
    files = mini_files()
    files["mini\\..\\evil"] = "x"
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "unsafe_entry"


def test_symlink_entry(tmp_path):
    path = make_zip(tmp_path / "t.zip", mini_files(), symlinks={"mini/link": "/etc/passwd"})
    assert reason_of(path).reason == "unsafe_entry"


def test_too_many_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(themeinstall, "MAX_ENTRIES", 3)
    assert reason_of(mini_zip(tmp_path)).reason == "too_large"


def test_too_large(tmp_path, monkeypatch):
    monkeypatch.setattr(themeinstall, "MAX_UNPACKED", 10)
    assert reason_of(mini_zip(tmp_path)).reason == "too_large"


def test_no_theme_json(tmp_path):
    files = {k: v for k, v in mini_files().items() if not k.endswith("theme.json")}
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "no_theme_json"


def test_theme_one_level_too_deep(tmp_path):
    files = {f"mini/{name}": content for name, content in mini_files().items()}
    error = reason_of(make_zip(tmp_path / "t.zip", files))
    assert error.reason == "no_theme_json"
    assert "mini/mini/theme.json" in str(error)


@pytest.mark.parametrize("text", ["{not json", "[1, 2]", '{"name": "x"}', '{"id": 3}'])
def test_bad_theme_json(tmp_path, text):
    files = mini_files()
    files["mini/theme.json"] = text
    assert reason_of(make_zip(tmp_path / "t.zip", files)).reason == "bad_theme_json"


def test_id_mismatch(tmp_path):
    error = reason_of(mini_zip(tmp_path, id="other"))
    assert error.reason == "id_mismatch"
    assert "mini" in str(error) and "other" in str(error)


def test_bad_id(tmp_path):
    error = reason_of(mini_zip(tmp_path, top="MyTheme", id="MyTheme"))
    assert error.reason == "bad_id"
    assert "lowercase" in str(error)


@pytest.mark.parametrize("spec", [">=99.0.0", "not a version"])
def test_unmet_requirement(tmp_path, spec):
    assert reason_of(mini_zip(tmp_path, kb4it=spec)).reason == "requirement"


def test_missing_requirement_is_accepted(tmp_path):
    files = mini_files()
    data = json.loads(files["mini/theme.json"])
    del data["kb4it"]
    files["mini/theme.json"] = json.dumps(data)
    assert inspect_zip(make_zip(tmp_path / "t.zip", files)).top == "mini"
