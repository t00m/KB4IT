"""The offline help copy is built from the working tree into a throwaway folder."""

import importlib.util
import json
import subprocess
import sys

import pytest

from tests.helpers import ROOT, isolated_env

SCRIPT = ROOT / "scripts" / "help" / "build_offline.py"
HELP_SOURCE = ROOT / "help" / "source"
VERSION = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    base = tmp_path_factory.mktemp("offline")
    out = base / "help"
    env = isolated_env(base / "home", NO_COLOR="1")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--out", str(out)], cwd=str(ROOT), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", timeout=900)
    return proc, out


def test_offline_build_writes_index_and_search(built):
    proc, out = built
    assert proc.returncode == 0, proc.stdout
    assert (out / "index.html").is_file()
    assert any(out.rglob("*search*"))


def test_offline_build_shows_the_package_version(built):
    _, out = built
    html = (out / "index.html").read_text(encoding="utf-8")
    assert VERSION in html
    assert '"0.8"' not in html


def test_offline_build_has_no_absolute_paths(built):
    # The help text shows example paths such as /home/ann, so look for the real build paths instead.
    _, out = built
    pages = list(out.rglob("*.html"))
    assert pages, "no html files were built"
    leaks = [str(ROOT), str(out), str(out.parent), str(HELP_SOURCE)]
    for path in pages:
        text = path.read_text(encoding="utf-8")
        for leak in leaks:
            assert leak not in text, (path, leak)


def test_help_config_version_is_not_hardcoded():
    conf = json.loads((ROOT / "help" / "config" / "repo.json").read_text(encoding="utf-8"))
    assert conf.get("version", "kb4it") in ("kb4it", VERSION)


def _load_script():
    spec = importlib.util.spec_from_file_location("build_offline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_package_fails_before_touching_the_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: None if name == "nh3" else real(name, *a))
    out = tmp_path / "help"
    out.mkdir()
    keep = out / "keep.txt"
    keep.write_text("x", encoding="utf-8")
    assert module.main(["--out", str(out)]) == 1
    err = capsys.readouterr().err
    assert "missing package(s): nh3; run: pip install KB4IT[extras]" in err
    assert keep.is_file()


def test_build_that_writes_nothing_fails(tmp_path, monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    out = tmp_path / "help"
    assert module.main(["--out", str(out)]) == 1
    assert str(out / "index.html") in capsys.readouterr().err


def test_stale_index_does_not_hide_a_failed_build(tmp_path, monkeypatch):
    module = _load_script()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    out = tmp_path / "help"
    out.mkdir()
    (out / "index.html").write_text("old", encoding="utf-8")
    assert module.main(["--out", str(out)]) == 1
    assert not (out / "index.html").exists()


def _no_build(module, monkeypatch):
    """Skip the preflight and the real build, so only the --out checks run."""
    monkeypatch.setattr(module, "missing_packages", lambda: [])
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))


def test_out_dot_with_other_files_is_refused(tmp_path, monkeypatch, capsys):
    module = _load_script()
    _no_build(module, monkeypatch)
    work = tmp_path / "work"
    work.mkdir()
    keep = work / "keep.txt"
    keep.write_text("x", encoding="utf-8")
    monkeypatch.chdir(work)
    assert module.main(["--out", "."]) == 1
    assert "refusing --out" in capsys.readouterr().err
    assert keep.is_file()


def test_out_outside_resources_and_temp_is_refused(tmp_path, monkeypatch, capsys):
    module = _load_script()
    _no_build(module, monkeypatch)
    fake_temp = tmp_path / "fake-temp"
    fake_temp.mkdir()
    monkeypatch.setattr(module.tempfile, "gettempdir", lambda: str(fake_temp))
    out = tmp_path / "elsewhere" / "help"
    assert module.main(["--out", str(out)]) == 1
    assert "refusing --out" in capsys.readouterr().err
    assert not out.exists()
