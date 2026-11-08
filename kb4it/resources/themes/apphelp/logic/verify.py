"""Hook for kb4it verify: run the AppHelp metadata checks without building."""

from .apphelp_config import load_config
from .apphelp_meta import validate_all


def verify(repo, docs):
    """Return one line per metadata problem."""
    return [str(problem) for problem in validate_all(docs, load_config(repo))]
