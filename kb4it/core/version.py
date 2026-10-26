"""KB4IT version helpers: parse versions, check theme requirements, identify the build (BI)."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

# Written into the package by scripts/devel/stamp_build.py; git-ignored, shipped in the wheel and sdist.
BUILD_FILE = "BUILD.json"
DESCRIBE_RE = re.compile(r"^v?(?P<tag>\d+\.\d+\.\d+)-(?P<count>\d+)-g(?P<sha>[0-9a-f]+)$")

VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$")
CLAUSE_RE = re.compile(r"^(>=|<=|==|!=|>|<)?\s*(.+)$")


def parse_version(text: str) -> tuple:
    """Return (major, minor, patch) from '1.2.3'; local '+...' parts are ignored."""
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


def _git(root, *args, text=True):
    """stdout of 'git <args>' in root, or None when git is missing or fails."""
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=text, timeout=5,
                             **({"encoding": "utf-8", "errors": "replace"} if text else {}))
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() if text else out.stdout


def git_info(root, version) -> dict | None:
    """Build facts of the checkout at root, or None when root is not one or git is unavailable."""
    if not (Path(root) / ".git").exists():
        return None
    commit = _git(root, "rev-parse", "HEAD")
    if not commit:
        return None
    describe = _git(root, "describe", "--tags", "--long", "--match", "v[0-9]*") or ""
    # Only the package counts: editing the docs or the tests of a checkout does not change the build.
    diff = _git(root, "diff", "HEAD", "--binary", "--", "kb4it", text=False) or b""
    tags = (_git(root, "tag", "--points-at", "HEAD") or "").split()
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or ""
    match = DESCRIBE_RE.match(describe)
    return {
        "version": version,
        "commit": commit,
        "describe": describe,
        "count": int(match.group("count")) if match else None,
        "branch": "" if branch == "HEAD" else branch,
        "dirty": bool(diff),
        "diff_hash": hashlib.blake2b(diff, digest_size=6).hexdigest() if diff else "",
        "source": "release" if f"v{version}" in tags and not diff else "dev",
    }


def build_version(info: dict) -> str:
    """'X.Y.Z' for a release, 'X.Y.Z-dev+<n>.g<sha7>[.dirty]' for any other commit, 'X.Y.Z+unknown' without facts."""
    version = info["version"]
    if not info.get("commit"):
        return f"{version}+unknown"
    if info.get("source") == "release" and not info.get("dirty"):
        return version
    count = info.get("count")
    local = f"{count}.g{info['commit'][:7]}" if count is not None else f"g{info['commit'][:7]}"
    return f"{version}-dev+{local}{'.dirty' if info.get('dirty') else ''}"


def build_cache_key(info: dict) -> str:
    """What kbdict.json stores as kb4it_build: two different uncommitted states never share a cache."""
    key = build_version(info)
    return f"{key}.{info['diff_hash']}" if info.get("dirty") and info.get("diff_hash") else key


def read_build_file(package_dir, version) -> dict | None:
    """The BUILD.json stamped into the package, when it exists, is readable and names this version."""
    try:
        data = json.loads((Path(package_dir) / BUILD_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("version") != version:
        return None
    return data


def build_info(package_dir, version) -> dict:
    """Facts of the running build: a live checkout first, then the stamped BUILD.json, then unknown."""
    info = git_info(Path(package_dir).parent, version) or read_build_file(package_dir, version)
    if info is None:
        info = {"version": version, "commit": None, "describe": "", "count": None, "branch": "",
                "dirty": False, "diff_hash": "", "source": "unknown"}
    info = dict(info)
    info["build_version"] = build_version(info)
    return info


# Folders of a theme that never shape a page: app scaffolds for 'kb4it create' and Python caches (TV-03).
FINGERPRINT_SKIP_TOP = {"apps"}
FINGERPRINT_SKIP_ANY = {"__pycache__", ".git"}


def _hash_tree(digest, label, folder, skip_top=()):
    """Feed every file under folder into digest: relative path and contents, in sorted order."""
    folder = Path(folder)
    if not folder.is_dir():
        return
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if rel.parts[0] in skip_top or FINGERPRINT_SKIP_ANY.intersection(rel.parts):
            continue
        if not path.is_file() or path.suffix == ".pyc":
            continue
        digest.update(f"{label}/{rel.as_posix()}\0".encode("utf-8"))
        digest.update(path.read_bytes())
        digest.update(b"\0")


def theme_fingerprint(theme_path, *shared_dirs) -> str:
    """12 hex characters that change when any file shaping the theme's pages changes.

    shared_dirs are the template folders the theme builds on (its template base, the common templates);
    a file renamed counts as a change.
    """
    digest = hashlib.blake2b(digest_size=6)
    _hash_tree(digest, "theme", theme_path, FINGERPRINT_SKIP_TOP)
    for n, folder in enumerate(d for d in shared_dirs if d):
        _hash_tree(digest, f"shared{n}", folder)
    return digest.hexdigest()


def theme_identity(theme_id, version, fingerprint) -> str:
    """'techdoc 1.0.0+3f9a1c0b7e21', or 'mytheme unversioned+...' for a theme without a version."""
    return f"{theme_id} {version or 'unversioned'}+{fingerprint}"
