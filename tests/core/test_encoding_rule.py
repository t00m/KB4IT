"""Every text file KB4IT reads or writes names its encoding, so builds do not depend on the locale."""

import ast
import json
from html import unescape
import os
import subprocess
import sys

from tests.helpers import ROOT, isolated_env, page, write_repo

TEXT_IO_METHODS = {"read_text", "write_text"}


def _mode(call):
    if len(call.args) > 1:
        node = call.args[1]
    else:
        node = next((kw.value for kw in call.keywords if kw.arg == "mode"), None)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return "r" if node is None else "?"


def _offenders(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        has_encoding = any(kw.arg == "encoding" for kw in node.keywords)
        func = node.func
        builtin_open = isinstance(func, ast.Name) and func.id == "open"
        if builtin_open or getattr(func, "attr", "") in ("fdopen", "FileHandler"):
            if "b" not in _mode(node) and not has_encoding:
                yield node.lineno
        elif isinstance(func, ast.Attribute) and func.attr in TEXT_IO_METHODS and not has_encoding:
            yield node.lineno
        elif isinstance(func, ast.Attribute) and func.attr in ("run", "Popen", "check_output"):
            text = any(kw.arg in ("text", "universal_newlines") and getattr(kw.value, "value", False)
                       for kw in node.keywords)
            if text and not has_encoding:
                yield node.lineno


def test_text_io_names_its_encoding():
    found = []
    for path in sorted((ROOT / "kb4it").rglob("*.py")):
        found.extend(f"{path.relative_to(ROOT)}:{line}" for line in _offenders(path))
    assert not found, "text I/O without encoding=:\n" + "\n".join(found)


def test_builds_never_fall_back_to_the_locale_encoding(tmp_path, home):
    """Python's EncodingWarning flags every text open() that would use the locale, as Windows does (cp1252)."""
    for theme in ("techdoc", "blog", "bookshelf", "apphelp"):
        app_conf = ROOT / "kb4it" / "resources" / "themes" / theme / "apps" / "default" / "config" / "repo.json"
        conf = json.loads(app_conf.read_text(encoding="utf-8"))
        conf.update({"source": "source", "target": "target"})
        conf.pop("theme", None)
        if theme == "apphelp":
            conf.setdefault("apphelp", {})["strict"] = False
        cfg = write_repo(tmp_path / theme, theme, {"nota.md": page("Canción de Tomás", "Año, niño.", Author="Tomás",
                                                                     Category="Post", Date="2026-10-08", DocType="Reference")},
                         **conf)
        env = isolated_env(home)
        runner = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"
        cmd = [sys.executable, "-X", "warn_default_encoding", "-W", "error::EncodingWarning",
               "-c", runner, "build", str(cfg)]
        result = subprocess.run(cmd, cwd=str(tmp_path), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=600, check=False)
        assert result.returncode == 0, result.stdout
        html = (tmp_path / theme / "target" / "nota.html").read_text(encoding="utf-8")
        assert "Canción de Tomás" in unescape(html), theme
