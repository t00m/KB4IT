#!/usr/bin/env python

"""
kb4it serve: build, serve the site locally, and rebuild when sources change.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

import argparse
import logging
import os
import sys
import threading
import time
import webbrowser

from kb4it.core.env import ENV
from kb4it.core.exceptions import LockBusyError
from kb4it.core.lock import FileLock, repo_lock_path
from kb4it.core.log import get_logger, reset_logging
from kb4it.core.util import json_load
from kb4it.core.watch import PollingWatcher
from kb4it.core.webserver import BuildStatus, SiteServer

log = get_logger(__name__)


class _ErrorCollector(logging.Handler):
    """Keep the first error a build logs, for the browser banner."""

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.first = ""

    def emit(self, record):
        if not self.first:
            self.first = record.getMessage()


def repo_paths(config):
    """(repo dict, source dir, target dir) of the repository whose repo.json is config."""
    from kb4it.core.paths import resolve_repo_path
    root = os.path.dirname(os.path.dirname(os.path.abspath(config)))
    repo = json_load(config)
    return repo, resolve_repo_path(repo["source"], root), resolve_repo_path(repo["target"], root)


def watched_paths(config):
    """Files and folders whose changes trigger a rebuild, and the subset that forces a full one."""
    from kb4it.core.paths import resolve_repo_path
    root = os.path.dirname(os.path.dirname(os.path.abspath(config)))
    try:
        repo, source, _target = repo_paths(config)
    except Exception:
        return [config], {config}
    paths = [config, source]
    full = {config}
    theme_dirs = []
    if repo.get("theme_path"):
        theme_dirs.append(resolve_repo_path(repo["theme_path"], root))
    elif repo.get("theme"):
        # Bundled themes only change with KB4IT itself; a user theme can change while writing.
        user_theme = os.path.join(ENV["LPATH"]["THEMES"], repo["theme"])
        if os.path.isdir(user_theme):
            theme_dirs.append(user_theme)
    for extra, default in (("overrides", "overrides"), ("hooks", None)):
        value = repo.get(extra, default)
        if isinstance(value, str) and value:
            theme_dirs.append(resolve_repo_path(value, root))
    for path in theme_dirs:
        if os.path.exists(path):
            paths.append(path)
            full.add(path)
    return paths, full


class Server:
    """Holds the state of one `kb4it serve` run."""

    def __init__(self, params: dict, holds_lock=True, on_build=None):
        self.config = os.path.abspath(params["config"])
        self.params = params
        # kb4it serve holds the repository lock for its whole run. The TUI does not, so its
        # Compile button keeps working; each rebuild then takes the lock like any build.
        self.holds_lock = holds_lock
        self.on_build = on_build
        self.status = BuildStatus()
        self.server = None

    def build(self, force=False):
        """Run one build in this process; record its result for the status endpoint."""
        from kb4it.core.main import KB4IT
        started = time.perf_counter()
        reset_logging()
        build_params = argparse.Namespace(action="build", config=self.config, force=force,
                                          log_level=self.params.get("log_level") or "INFO",
                                          lock_held=self.holds_lock)
        collector = _ErrorCollector()
        error = ""
        try:
            app = KB4IT(build_params)
            logging.getLogger().addHandler(collector)
            ok = app.run()
        except Exception as exc:  # a broken theme must not stop the server
            ok, error = False, str(exc)
        finally:
            logging.getLogger().removeHandler(collector)
        if not ok and not error:
            error = collector.first or "Build failed; see the terminal for details."
        self.status.record(ok, error)
        elapsed = time.perf_counter() - started
        log.info(f"[SERVE] REBUILD elapsed={elapsed:.2f}s result={'ok' if ok else 'failed'}")
        if self.on_build is not None:
            self.on_build(ok, error)
        return ok

    def start_background(self, target):
        """Serve target with live reload and rebuild on change from a daemon thread (used by the TUI)."""
        self.server = SiteServer(target, reload=True, status=self.status).start()
        self.stop_event = threading.Event()
        # Take the first snapshot now, so a file saved right after this call is seen as a change.
        watcher = self.new_watcher()
        threading.Thread(target=self.watch_loop, args=(self.stop_event, watcher), name="kb4it-watch",
                         daemon=True).start()
        return self.server

    def stop_background(self):
        if getattr(self, "stop_event", None) is not None:
            self.stop_event.set()
        if self.server is not None:
            self.server.shutdown()
            self.server = None

    def run(self):
        """Serve until Ctrl+C; return the process exit status."""
        if not os.path.isfile(self.config):
            print(f"Config file not found: {self.config}", file=sys.stderr)
            return 1
        lock = FileLock(repo_lock_path(self.config))
        try:
            lock.acquire()
        except LockBusyError as busy:
            holder = f" (PID {busy.pid})" if busy.pid else ""
            print(f"KB4IT is already working on this repository{holder}", file=sys.stderr)
            return 1
        stop = threading.Event()
        try:
            self.build(force=bool(self.params.get("force")))
            _repo, _source, target = repo_paths(self.config)
            os.makedirs(target, exist_ok=True)
            host = self.params.get("host") or "127.0.0.1"
            if host not in ("127.0.0.1", "localhost", "::1"):
                log.warning(f"[SERVE] WARNING_PUBLIC host={host}")
            # Take the first snapshot before the server answers, so a file saved as soon as
            # the site is up is seen as a change.
            watcher = None if self.params.get("no_watch") else self.new_watcher()
            self.server = SiteServer(target, host=host, port=self.params.get("port"),
                                     reload=not self.params.get("no_reload"), status=self.status).start()
            log.info(f"[SERVE] LISTEN url={self.server.url}")
            print(f"Serving {target} at {self.server.url} (Ctrl+C to stop)", flush=True)
            if self.params.get("open"):
                webbrowser.open(self.server.url)
            if self.params.get("no_watch"):
                while True:
                    time.sleep(3600)
            self.watch_loop(stop, watcher)
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            if self.server is not None:
                self.server.shutdown()
            lock.release()
            log.info("[SERVE] STOP")
        return 0

    def new_watcher(self):
        paths, full = watched_paths(self.config)
        watcher = PollingWatcher(paths, interval=float(self.params.get("interval") or 1.0))
        watcher.full = full
        return watcher

    def watch_loop(self, stop, watcher=None):
        watcher = watcher or self.new_watcher()
        while not stop.is_set():
            changed = watcher.wait(stop)
            if changed is None:
                return
            log.info(f"[WATCH] CHANGE files={len(changed)}")
            force = any(p == f or p.startswith(f + os.sep) for p in changed for f in watcher.full)
            self.build(force=force)
            if self.config in changed:
                # Settings may move the source folder or the theme; watch the new set.
                watcher = self.new_watcher()


def run_serve(params: dict) -> int:
    """Entry point used by kb4it.core.main for the serve action."""
    return Server(params).run()
