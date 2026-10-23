"""
Performance traces, kept apart from the log.

kb4it build --trace records how long each part of the build takes and writes var/log/trace.json in
the Chrome Trace Event format, which https://ui.perfetto.dev and chrome://tracing show as a timeline.
Without --trace, span() does nothing.

# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

TRACE_FILE = "trace.json"

_lock = threading.Lock()
_events: list[dict[str, Any]] | None = None
_depth = threading.local()
_t0 = 0.0
_main = 0


def start() -> None:
    """Start recording spans; a trace already running is discarded."""
    global _events, _t0, _main
    with _lock:
        _events = []
        _t0 = time.perf_counter()
        _main = threading.get_ident()


def active() -> bool:
    """True while a trace is recording."""
    return _events is not None


@contextmanager
def span(name: str, **args: Any) -> Iterator[None]:
    """Record the time the block takes under name; args are shown with the span in the viewer."""
    if _events is None:
        yield
        return
    depth = getattr(_depth, "n", 0)
    _depth.n = depth + 1
    begin = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        _depth.n = depth
        event = {"name": name, "ph": "X", "pid": os.getpid(), "tid": threading.get_ident(),
                 "ts": round((begin - _t0) * 1e6), "dur": round((end - begin) * 1e6), "depth": depth}
        if args:
            event["args"] = {key: str(value) for key, value in args.items()}
        with _lock:
            if _events is not None:
                _events.append(event)


def stop(folder: str) -> tuple[str, list[dict[str, Any]]] | None:
    """Stop recording and write folder/trace.json; return (path, events), or None when no trace was running."""
    global _events
    with _lock:
        events, _events = _events, None
    if events is None:
        return None
    events.sort(key=lambda e: (e["ts"], e["depth"]))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, TRACE_FILE)
    trace = {"traceEvents": [{k: v for k, v in e.items() if k != "depth"} for e in events],
             "displayTimeUnit": "ms"}
    with open(path, "w", encoding="utf-8") as fout:
        json.dump(trace, fout, indent=1)
    return path, events


def summary(events: list[dict[str, Any]], min_share: float = 0.01) -> list[str]:
    """Lines of a table of the build's spans.

    Spans of the thread that started the trace come in start order, indented by nesting; those under
    min_share of the total are left out. Spans of worker threads (one per document) are grouped by name.
    """
    if not events:
        return []
    total = max(e["ts"] + e["dur"] for e in events) - min(e["ts"] for e in events)
    lines = [f"{'ms':>9}  {'%':>5}  span"]
    workers: dict[str, list[int]] = {}
    for event in events:
        if event["tid"] != _main:
            workers.setdefault(event["name"], []).append(event["dur"])
            continue
        if total and event["dur"] / total < min_share:
            continue
        share = 100 * event["dur"] / total if total else 0.0
        lines.append(f"{event['dur'] / 1000:9.1f}  {share:5.1f}  {'  ' * event['depth']}{event['name']}")
    for name, durations in sorted(workers.items()):
        lines.append(f"{name} in worker threads: n={len(durations)} sum={sum(durations) / 1000:.1f} ms"
                     f" max={max(durations) / 1000:.1f} ms")
    return lines
