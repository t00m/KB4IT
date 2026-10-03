"""KB4IT version helpers: parse versions, check theme requirements, describe a git checkout."""

import re
import subprocess
from pathlib import Path

VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$")
CLAUSE_RE = re.compile(r"^(>=|<=|==|!=|>|<)?\s*(.+)$")


def parse_version(text: str) -> tuple:
    """Return (major, minor, patch) from '0.7.10'; local '+...' parts are ignored."""
    match = VERSION_RE.match(str(text).strip().split("+", 1)[0])
    if not match:
        raise ValueError(f"not a version: {text!r}")
    return tuple(int(part or 0) for part in match.groups())


def requirement_satisfied(spec: str, version: str) -> bool:
    """True when version meets every comma-separated clause of spec; a bare version means '>='."""
    clauses = [c.strip() for c in str(spec).split(",") if c.strip()]
    if not clauses:
        raise ValueError(f"empty requirement: {spec!r}")
    current = parse_version(version)
    checks = {">=": current.__ge__, "<=": current.__le__, ">": current.__gt__,
              "<": current.__lt__, "==": current.__eq__, "!=": current.__ne__}
    for clause in clauses:
        operator, wanted = CLAUSE_RE.match(clause).groups()
        if not checks[operator or ">="](parse_version(wanted)):
            return False
    return True


def git_describe(root) -> str:
    """'git describe' of a source checkout, or '' when root is not one or git is unavailable."""
    if not (Path(root) / ".git").exists():
        return ""
    try:
        out = subprocess.run(["git", "describe", "--tags", "--dirty", "--always"], cwd=root,
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""
