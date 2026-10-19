"""requirements.txt lists exactly the runtime dependencies declared in pyproject.toml."""

import re
import tomllib

from tests.helpers import ROOT


def _from_pyproject():
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poetry"]["dependencies"]
    wanted = set()
    for name, spec in deps.items():
        if name == "python":
            continue
        if isinstance(spec, dict):
            if spec.get("optional"):
                continue
            spec = spec["version"]
        if spec == "*":
            wanted.add(name.lower())
        elif re.match(r"^\d", spec):
            wanted.add(f"{name.lower()}=={spec}")
        else:
            wanted.add(f"{name.lower()}{spec.replace(' ', '')}")
    return wanted


def _from_requirements():
    lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return {line.strip().lower().replace(" ", "") for line in lines if line.strip() and not line.startswith("#")}


def test_requirements_match_pyproject():
    assert _from_requirements() == _from_pyproject()
