"""Vendor libraries live once in kb4it/resources/vendor; a theme names the ones it uses in theme.json 'assets' (P6)."""

import logging
from types import SimpleNamespace

import pytest

from kb4it.core import vendor
from kb4it.core.exceptions import ThemeError
from kb4it.core.vendor import theme_assets, vendor_names, vendor_paths


@pytest.fixture
def fake_vendor(tmp_path, monkeypatch):
    root = tmp_path / "vendor"
    for name in ("a", "b"):
        (root / name).mkdir(parents=True)
        (root / name / "x.js").write_text(name, encoding="utf-8")
    monkeypatch.setattr(vendor, "VENDOR_DIR", str(root))
    return root


def test_missing_assets_key_is_empty():
    assert theme_assets({"id": "x"}) == []


def test_unknown_name_raises(fake_vendor):
    with pytest.raises(ThemeError, match="nope"):
        theme_assets({"assets": ["nope"]})


@pytest.mark.parametrize("assets", ["highlight", [1], {"a": 1}])
def test_not_a_list_raises(fake_vendor, assets):
    with pytest.raises(ThemeError, match="must be a list of names"):
        theme_assets({"assets": assets})


def test_known_names(fake_vendor):
    assert vendor_names() == ["a", "b"]
    assert theme_assets({"assets": ["b"]}) == ["b"]
    assert vendor_paths(["b"]) == [str(fake_vendor / "b")]


def test_fingerprint_changes_with_vendor_file(fake_vendor, tmp_path):
    from kb4it.services.frontend import Frontend
    theme_dir = tmp_path / "theme"
    theme_dir.mkdir()
    (theme_dir / "theme.json").write_text("{}", encoding="utf-8")
    host = SimpleNamespace(log=logging.getLogger("test"))

    def fingerprint():
        theme = {"id": "t", "version": "1.0.0", "path": str(theme_dir), "assets": ["a"]}
        Frontend._identify(host, theme)
        return theme["fingerprint"]

    first = fingerprint()
    (fake_vendor / "a" / "x.js").write_text("changed", encoding="utf-8")
    assert fingerprint() != first
    (fake_vendor / "b" / "x.js").write_text("changed", encoding="utf-8")
    second = fingerprint()
    assert fingerprint() == second, "an undeclared library does not count"


def test_sync_copies_declared_libraries(fake_vendor, tmp_path):
    from kb4it.core.vendor import sync_vendor
    dest = tmp_path / "target" / "resources" / "vendor"
    copied, deleted, files = sync_vendor(str(dest), ["a"], keep=())
    assert (dest / "a" / "x.js").read_text(encoding="utf-8") == "a"
    assert not (dest / "b").exists()
    assert (copied, deleted) == (1, 0)
    assert files == {str(dest / "a" / "x.js")}


def test_sync_prunes_undeclared_libraries(fake_vendor, tmp_path):
    from kb4it.core.vendor import sync_vendor
    dest = tmp_path / "target" / "vendor"
    (dest / "old").mkdir(parents=True)
    (dest / "old" / "y.js").write_text("y", encoding="utf-8")
    (dest / "mine.txt").write_text("user", encoding="utf-8")
    _copied, deleted, _files = sync_vendor(str(dest), ["a"], keep={str(dest / "mine.txt")})
    assert not (dest / "old").exists()
    assert (dest / "mine.txt").exists(), "a repository file is kept"
    assert deleted == 1


def test_sync_without_libraries_removes_the_folder(fake_vendor, tmp_path):
    from kb4it.core.vendor import sync_vendor
    dest = tmp_path / "target" / "vendor"
    (dest / "a").mkdir(parents=True)
    (dest / "a" / "x.js").write_text("a", encoding="utf-8")
    sync_vendor(str(dest), [], keep=())
    assert not dest.exists()
