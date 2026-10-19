"""The polling watcher sees additions, edits and deletions, ignores editor scratch files and debounces bursts."""

import threading
import time

from kb4it.core import watch
from kb4it.core.watch import PollingWatcher


def _later(delay, action):
    timer = threading.Timer(delay, action)
    timer.start()
    return timer


def test_snapshot_and_diff(tmp_path):
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / ".a.md.swp").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.md").write_text("b", encoding="utf-8")
    first = watch.snapshot([tmp_path])
    assert sorted(first) == [str(tmp_path / "a.md"), str(tmp_path / "sub" / "b.md")]
    (tmp_path / "a.md").write_text("changed", encoding="utf-8")
    (tmp_path / "sub" / "b.md").unlink()
    (tmp_path / "c.md").write_text("c", encoding="utf-8")
    assert watch.diff(first, watch.snapshot([tmp_path])) == sorted(
        [str(tmp_path / "a.md"), str(tmp_path / "c.md"), str(tmp_path / "sub" / "b.md")])


def test_ignored_names():
    for name in ("note.md~", ".#note.md", "note.md.swp", "4913", ".DS_Store", ".~lock.x.md#"):
        assert watch.ignored(name), name
    assert not watch.ignored("note.md")


def test_wait_returns_one_batch_for_a_burst(tmp_path):
    watcher = PollingWatcher([tmp_path], interval=0.05, debounce=0.3)
    timers = [_later(0.1, lambda: (tmp_path / "one.md").write_text("1", encoding="utf-8")),
              _later(0.2, lambda: (tmp_path / "two.md").write_text("2", encoding="utf-8"))]
    changed = watcher.wait()
    for timer in timers:
        timer.join()
    assert changed == [str(tmp_path / "one.md"), str(tmp_path / "two.md")]


def test_watch_single_file(tmp_path):
    config = tmp_path / "repo.json"
    config.write_text("{}", encoding="utf-8")
    watcher = PollingWatcher([config], interval=0.05, debounce=0.05)
    _later(0.1, lambda: config.write_text('{"title": "x"}', encoding="utf-8")).join()
    assert watcher.wait() == [str(config)]


def test_stop_event_ends_the_wait(tmp_path):
    stop = threading.Event()
    watcher = PollingWatcher([tmp_path], interval=0.05)
    _later(0.1, stop.set)
    started = time.monotonic()
    assert watcher.wait(stop) is None
    assert time.monotonic() - started < 2
