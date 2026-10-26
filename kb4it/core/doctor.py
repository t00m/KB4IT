"""'kb4it doctor': what is installed, from which commit, and whether anything bundled is missing (SI-07).

The report is what a bug report should include. Missing bundled files make it fail,
so the source installer can prove that an installation is complete.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.version import theme_fingerprint, theme_identity

# The themes every package ships; tests/core/test_doctor.py keeps it equal to the tracked themes.
BUNDLED_THEMES = ("apphelp", "blog", "bookshelf", "techdoc")
BUNDLED_FILES = {
    "editor": Path("resources") / "editor" / "codemirror.min.js",
    "render": Path("resources") / "render" / "kb4it-render.js",
}
HELP_INDEX = Path("resources") / "help" / "index.html"


def _themes(root: str, scope: str) -> list[dict]:
    """Every theme folder under root, with its version, fingerprint and the problem that stops it loading."""
    found = []
    if not os.path.isdir(root):
        return found
    for name in sorted(os.listdir(root)):
        folder = Path(root) / name
        if not folder.is_dir():
            continue
        entry = {"id": name, "scope": scope, "path": str(folder), "problem": ""}
        try:
            conf = json.loads((folder / "theme.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            entry["problem"] = f"theme.json unreadable: {error}"
            found.append(entry)
            continue
        base = conf.get("template_base")
        base_dir = Path(ENV["GPATH"]["BASES"]) / base / "templates" if isinstance(base, str) and base else None
        fingerprint = theme_fingerprint(folder, base_dir if base_dir and base_dir.is_dir() else None,
                                        ENV["GPATH"]["TEMPLATES"])
        entry["id"] = conf.get("id", name)
        entry["identity"] = theme_identity(entry["id"], conf.get("version"), fingerprint)
        if not (folder / "logic" / "theme.py").is_file():
            entry["problem"] = "logic/theme.py is missing"
        found.append(entry)
    return found


def report() -> tuple[list[str], list[str]]:
    """The report lines and the problems found; no problem means the installation is complete."""
    build = ENV["APP"]["build"]
    package = Path(ENV["CONF"]["ROOT"])
    checkout = build.get("source") in ("dev", "release") and (package.parent / ".git").exists()
    lines, problems = [], []

    lines.append(f"KB4IT      {ENV['APP']['build_version']}")
    if build.get("commit"):
        origin = f"built {build['date']}" if build.get("date") else "source checkout"
        branch = f" on {build['branch']}" if build.get("branch") else ""
        lines.append(f"Commit     {build['commit']}{branch} ({origin})")
    else:
        lines.append("Commit     unknown: no git checkout and no build stamp (kb4it/BUILD.json)")
    lines.append(f"Python     {platform.python_version()} ({sys.executable})")
    lines.append(f"Package    {package}")
    on_path = shutil.which("kb4it")
    lines.append(f"Command    {on_path or 'kb4it is not on PATH'}")
    lines.append(f"User data  {ENV['LPATH']['ROOT']}")

    help_index = package / HELP_INDEX
    if help_index.is_file():
        lines.append(f"Help       {help_index}")
    elif checkout:
        lines.append("Help       not built in this checkout (scripts/help/build_offline.py)")
    else:
        lines.append("Help       MISSING")
        problems.append(f"offline help missing: no {help_index}")
    for name, rel in BUNDLED_FILES.items():
        if not (package / rel).is_file():
            problems.append(f"{name} files missing: no {package / rel}")

    themes = _themes(ENV["GPATH"]["THEMES"], "builtin") + _themes(ENV["LPATH"]["THEMES"], "user")
    lines.append("Themes")
    builtin = {t["id"] for t in themes if t["scope"] == "builtin"}
    for theme in themes:
        label = theme.get("identity", theme["id"])
        hides = " (hides the built-in theme)" if theme["scope"] == "user" and theme["id"] in builtin else ""
        lines.append(f"  {label:40} {theme['scope']:8} {theme['path']}{hides}")
        if theme["problem"]:
            problems.append(f"theme {theme['id']} ({theme['path']}): {theme['problem']}")
    for name in BUNDLED_THEMES:
        if name not in builtin:
            problems.append(f"bundled theme missing: {name} (not in {ENV['GPATH']['THEMES']})")
    return lines, problems
