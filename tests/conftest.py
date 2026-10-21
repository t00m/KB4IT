"""Pytest setup: isolate HOME before kb4it is imported, expose shared fixtures."""

import os
import sys
import tempfile
from pathlib import Path

# kb4it.core.env reads HOME and KB4IT_HOME at import time to set its per-user paths, which
# KB4IT creates later; point them at a scratch folder before anything imports kb4it.
# KB4IT_HOME covers Windows, where Path.home() reads USERPROFILE instead of HOME.
os.environ["HOME"] = tempfile.mkdtemp(prefix="kb4it-test-home-")
os.environ["USERPROFILE"] = os.environ["HOME"]
os.environ["KB4IT_HOME"] = os.path.join(os.environ["HOME"], ".kb4it")

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "kb4it" / "resources" / "themes" / "apphelp" / "logic"))


def pytest_ignore_collect(collection_path, config):
    # pytest-relaxed (a plugin, not a dependency) collects every module, so skip the helpers and fixtures.
    if collection_path.name == "helpers.py" or FIXTURES in collection_path.parents:
        return True
    return None


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    path.mkdir()
    return path
