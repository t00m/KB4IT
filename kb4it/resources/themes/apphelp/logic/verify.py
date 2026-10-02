"""Hook for kb4it verify: run the AppHelp metadata checks without building."""

import os
import sys

# kb4it verify loads this file directly, so the sibling modules are not on sys.path yet.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apphelp_config import load_config  # noqa: E402
from apphelp_meta import validate_all  # noqa: E402


def verify(repo, docs):
    """Return one line per metadata problem."""
    return [str(problem) for problem in validate_all(docs, load_config(repo))]
