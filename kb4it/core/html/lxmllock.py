"""One lock for the lxml work of the compile threads.

lxml releases the GIL while it parses or serializes. With lxml 6.2.0 on macOS, two
threads parsing HTML at the same time corrupt memory and the build aborts
("pointer being freed was not allocated" in lxml's _fixHtmlDictNames), even with one
parser per page. Every parse, change and serialization of HTML that a compile thread
can reach holds this lock, so only one thread is inside lxml at a time. Markdown and
the templates still run in parallel.
"""

from __future__ import annotations

import functools
import threading
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

LXML_LOCK = threading.RLock()


def lxml_serialized(func: Callable[P, R]) -> Callable[P, R]:
    """Run func while holding LXML_LOCK."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with LXML_LOCK:
            return func(*args, **kwargs)
    return wrapper
