"""The KB4IT README as Markdown for the About KB4IT page."""

from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path

REPO_FILES_URL = "https://github.com/t00m/KB4IT/blob/master/"
_ROOT = Path(__file__).resolve().parents[2]
# A relative link target: not a scheme, not an anchor, not an absolute path.
_RELATIVE_LINK = re.compile(r"\]\((?![a-zA-Z][a-zA-Z0-9+.-]*:|#|/)([^)\s]+)\)")
_BADGE = re.compile(r"^\s*\[?!\[")


def readme_text() -> str:
    """README.md of a source checkout, else the long description of the installed package, else ''."""
    path = _ROOT / "README.md"
    if path.is_file() and (_ROOT / "pyproject.toml").is_file():
        return path.read_text(encoding="utf-8")
    try:
        meta = importlib.metadata.metadata("KB4IT")
    except importlib.metadata.PackageNotFoundError:
        return ""
    payload = getattr(meta, "get_payload", lambda: "")()
    return str(payload or meta.get("Description") or "")


def about_markdown(text: str) -> str:
    """README body for the About page.

    The H1 becomes a plain line, badge images are left out (they load from the network)
    and relative links point to the repository. Code blocks are kept as written.
    """
    out = []
    in_fence = False
    title_done = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence:
            if not title_done and line.startswith("# "):
                title_done = True
                line = line[2:].strip()
            elif _BADGE.match(line):
                continue
            line = _RELATIVE_LINK.sub(lambda m: f"]({REPO_FILES_URL}{m.group(1)})", line)
        out.append(line)
    return "\n".join(out).strip() + "\n" if any(s.strip() for s in out) else ""
