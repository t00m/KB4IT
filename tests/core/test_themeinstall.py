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


# install_zip

@pytest.fixture
def home(tmp_path, monkeypatch):
    """A fresh KB4IT_HOME: none of its folders exist yet."""
    from kb4it.core.env import ENV
    root = tmp_path / "home"
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(root))
    monkeypatch.setitem(ENV["LPATH"], "VAR", str(root / "var"))
    monkeypatch.setitem(ENV["LPATH"], "THEMES", str(root / "opt" / "resources" / "themes"))
    return root


def themes_dir(home):
    return home / "opt" / "resources" / "themes"


def listing(folder):
    return sorted((p.relative_to(folder).as_posix(), p.read_bytes() if p.is_file() else None)
                  for p in Path(folder).rglob("*"))


def test_install_into_a_fresh_home(tmp_path, home):
    result = themeinstall.install_zip(mini_zip(tmp_path))
    assert (themes_dir(home) / "mini" / "theme.json").is_file()
    assert result.id == "mini" and result.version == "0.1.0"
    assert result.path == themes_dir(home) / "mini"
    assert result.replaced is None and result.bundled is None


def test_install_replaces_and_reports_old_version(tmp_path, home):
    themeinstall.install_zip(mini_zip(tmp_path))
    (themes_dir(home) / "mini" / "old-only.txt").write_text("x", encoding="utf-8")
    files = mini_files(version="0.2.0")
    files["mini/new.txt"] = "new"
    result = themeinstall.install_zip(make_zip(tmp_path / "v2.zip", files))
    assert result.replaced == "0.1.0" and result.version == "0.2.0"
    assert (themes_dir(home) / "mini" / "new.txt").is_file()
    assert not (themes_dir(home) / "mini" / "old-only.txt").exists()


def test_refused_zip_leaves_themes_untouched(tmp_path, home):
    themeinstall.install_zip(mini_zip(tmp_path))
    before = listing(themes_dir(home))
    with pytest.raises(ThemeInstallError) as caught:
        themeinstall.install_zip(mini_zip(tmp_path, name="bad.zip", id="other"))
    assert caught.value.reason == "id_mismatch"
    assert listing(themes_dir(home)) == before


def test_swap_failure_restores_old_theme(tmp_path, home, monkeypatch):
    themeinstall.install_zip(mini_zip(tmp_path))
    before = listing(themes_dir(home))
    real_move = themeinstall._move

    def failing_move(src, dst):
        if Path(dst) == themes_dir(home) / "mini" and "install-" in str(src):
            raise OSError("disk full")
        real_move(src, dst)

    monkeypatch.setattr(themeinstall, "_move", failing_move)
    with pytest.raises(ThemeInstallError) as caught:
        themeinstall.install_zip(mini_zip(tmp_path, name="v2.zip", version="0.2.0"))
    assert caught.value.reason == "install"
    assert listing(themes_dir(home)) == before
    assert list(themeinstall.tmp_dir().iterdir()) == []


def test_temporary_files_are_removed(tmp_path, home):
    themeinstall.install_zip(mini_zip(tmp_path))
    assert list(themeinstall.tmp_dir().iterdir()) == []
    with pytest.raises(ThemeInstallError):
        themeinstall.install_zip(mini_zip(tmp_path, name="bad.zip", id="other"))
    assert list(themeinstall.tmp_dir().iterdir()) == []
    themeinstall.install_zip(mini_zip(tmp_path, name="v2.zip", version="0.2.0"))
    assert list(themeinstall.tmp_dir().iterdir()) == []


def test_same_id_as_bundled(tmp_path, home):
    from kb4it.core.env import ENV
    bundled = json.loads((Path(ENV["GPATH"]["THEMES"]) / "techdoc" / "theme.json").read_text(encoding="utf-8"))
    result = themeinstall.install_zip(mini_zip(tmp_path, top="techdoc", id="techdoc"))
    assert result.bundled == bundled["version"]
    assert themeinstall.bundled_version("nosuchtheme") is None


# download and install(source)

import io
import urllib.error
import urllib.request


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def serve(monkeypatch, payload=None, error=None):
    """Make themeinstall._open return payload, or raise error; return the list of opened URLs."""
    calls = []

    def fake_open(url, timeout):
        calls.append(url)
        if error is not None:
            raise error
        return FakeResponse(payload)

    monkeypatch.setattr(themeinstall, "_open", fake_open)
    return calls


def test_install_from_url(tmp_path, home, monkeypatch):
    calls = serve(monkeypatch, mini_zip(tmp_path).read_bytes())
    result = themeinstall.install("https://example.org/mini.zip")
    assert calls == ["https://example.org/mini.zip"]
    assert result.id == "mini" and (themes_dir(home) / "mini" / "theme.json").is_file()
    assert list(themeinstall.tmp_dir().iterdir()) == []


def test_http_refused(home, monkeypatch):
    calls = serve(monkeypatch, b"")
    with pytest.raises(ThemeInstallError) as caught:
        themeinstall.install("http://example.org/mini.zip")
    assert caught.value.reason == "insecure_url"
    assert calls == []


def test_redirect_to_http_refused():
    handler = themeinstall._HttpsOnlyRedirect()
    request = urllib.request.Request("https://example.org/mini.zip")
    with pytest.raises(ThemeInstallError) as caught:
        handler.redirect_request(request, None, 302, "Found", {}, "http://example.org/mini.zip")
    assert caught.value.reason == "insecure_url"
    allowed = handler.redirect_request(request, None, 302, "Found", {}, "https://cdn.example.org/mini.zip")
    assert allowed.full_url == "https://cdn.example.org/mini.zip"


def test_download_too_large(home, monkeypatch):
    monkeypatch.setattr(themeinstall, "MAX_DOWNLOAD", 100)
    serve(monkeypatch, b"x" * 1000)
    with pytest.raises(ThemeInstallError) as caught:
        themeinstall.install("https://example.org/mini.zip")
    assert caught.value.reason == "too_large"
    assert list(themeinstall.tmp_dir().iterdir()) == []


@pytest.mark.parametrize("error", [urllib.error.URLError("no route"), TimeoutError("timed out"),
                                   OSError("reset")])
def test_download_error(home, monkeypatch, error):
    serve(monkeypatch, error=error)
    with pytest.raises(ThemeInstallError) as caught:
        themeinstall.install("https://example.org/mini.zip")
    assert caught.value.reason == "download"
    assert list(themeinstall.tmp_dir().iterdir()) == []


def test_download_not_a_zip(home, monkeypatch):
    serve(monkeypatch, b"<html>not found</html>")
    with pytest.raises(ThemeInstallError) as caught:
        themeinstall.install("https://example.org/mini.zip")
    assert caught.value.reason == "not_a_zip"
    assert list(themeinstall.tmp_dir().iterdir()) == []


def test_install_from_a_path(tmp_path, home):
    assert themeinstall.install(str(mini_zip(tmp_path))).id == "mini"
