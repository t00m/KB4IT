"""Pytest setup: isolate HOME before kb4it is imported, expose shared fixtures."""

import os
import sys
import tempfile
from pathlib import Path

# kb4it.core.env creates its per-user folder at import time; keep it out of the real home.
# KB4IT_HOME covers Windows, where Path.home() reads USERPROFILE instead of HOME.
os.environ["HOME"] = tempfile.mkdtemp(prefix="kb4it-test-home-")
os.environ["USERPROFILE"] = os.environ["HOME"]
os.environ["KB4IT_HOME"] = os.path.join(os.environ["HOME"], ".kb4it")

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kb4it" / "resources" / "themes" / "apphelp" / "logic"))


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    path.mkdir()
    return path
