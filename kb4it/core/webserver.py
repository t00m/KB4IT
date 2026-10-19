#!/usr/bin/env python

"""
Local web server for a built site, shared by the TUI and `kb4it serve`.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

With live reload on, every HTML page the server sends gets a small script
before </body>. The script polls /__kb4it/status and reloads the page when the
build counter changes, or shows a banner when the last build failed. Files on
disk are never changed, so a deployed site never carries the script.
"""

import http.server
import json
import os
import socket
import threading

from kb4it.core.log import get_logger

DEFAULT_PORT = 8642
PORT_SCAN_LIMIT = 50
STATUS_PATH = "/__kb4it/status"

log = get_logger(__name__)

RELOAD_SCRIPT = """<script id="kb4it-live-reload">
(function () {
  var seen = null;
  function banner(status) {
    var box = document.getElementById("kb4it-serve-error");
    if (status.ok) { if (box) { box.remove(); } return; }
    if (!box) {
      box = document.createElement("div");
      box.id = "kb4it-serve-error";
      box.setAttribute("role", "alert");
      box.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483647;padding:12px 16px;" +
        "background:#8a1c1c;color:#fff;font:14px/1.4 system-ui,sans-serif;white-space:pre-wrap;" +
        "box-shadow:0 2px 8px rgba(0,0,0,.3)";
      document.body.appendChild(box);
    }
    box.textContent = "KB4IT build failed: " + (status.error || "see the terminal for details");
  }
  function poll() {
    fetch("%(status)s", {cache: "no-store"})
      .then(function (r) { return r.json(); })
      .then(function (status) {
        if (seen === null) { seen = status.build; }
        else if (status.build !== seen) { location.reload(); return; }
        banner(status);
      })
      .catch(function () {})
      .then(function () { setTimeout(poll, 1000); });
  }
  poll();
})();
</script>
""" % {"status": STATUS_PATH}


class BuildStatus:
    """Thread-safe record of the last build, read by the status endpoint."""

    def __init__(self):
        self._lock = threading.Lock()
        self.build = 0
        self.ok = True
        self.error = ""

    def record(self, ok, error=""):
        with self._lock:
            self.build += 1
            self.ok = bool(ok)
            self.error = "" if ok else str(error)

    def as_dict(self):
        with self._lock:
            return {"build": self.build, "ok": self.ok, "error": self.error}


def inject_reload(html: bytes) -> bytes:
    """Insert the live reload script before the last </body>, or append it."""
    script = RELOAD_SCRIPT.encode("utf-8")
    marker = html.lower().rfind(b"</body>")
    if marker < 0:
        return html + script
    return html[:marker] + script + html[marker:]


def find_free_port(host="127.0.0.1", start=DEFAULT_PORT, limit=PORT_SCAN_LIMIT):
    """First port in [start, start + limit) that host can bind, or None."""
    for port in range(start, start + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    return None


def _make_handler(directory, status, reload):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, fmt, *args):
            log.debug("[SERVE] REQUEST %s", fmt % args)

        def end_headers(self):
            # A preview must always show the latest build.
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self):
            path = self.path.split("?", 1)[0].split("#", 1)[0]
            if path == STATUS_PATH:
                self._send(200, "application/json", json.dumps(status.as_dict()).encode("utf-8"))
                return
            if reload:
                local = self.translate_path(self.path)
                if os.path.isdir(local):
                    if not path.endswith("/"):
                        super().do_GET()  # the standard handler redirects to the slash form
                        return
                    local = os.path.join(local, "index.html")
                if local.lower().endswith((".html", ".htm")) and os.path.isfile(local):
                    with open(local, "rb") as fh:
                        self._send(200, "text/html; charset=utf-8", inject_reload(fh.read()))
                    return
            super().do_GET()

        def _send(self, code, content_type, body):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


class SiteServer:
    """Serve a directory over HTTP in a background thread."""

    def __init__(self, directory, host="127.0.0.1", port=None, reload=False, status=None):
        self.directory = str(directory)
        self.host = host
        self.requested_port = port
        self.reload = reload
        self.status = status or BuildStatus()
        self.httpd = None
        self.port = None

    @property
    def url(self):
        shown = "127.0.0.1" if self.host in ("", "0.0.0.0") else self.host
        return f"http://{shown}:{self.port}/"

    def start(self):
        """Bind a free port (from the requested one) and start serving; raise OSError when none is free."""
        start = self.requested_port or DEFAULT_PORT
        port = find_free_port(self.host, start)
        if port is None:
            raise OSError(f"No free port found in range {start}-{start + PORT_SCAN_LIMIT}")
        handler = _make_handler(self.directory, self.status, self.reload)
        self.httpd = http.server.ThreadingHTTPServer((self.host, port), handler)
        self.httpd.daemon_threads = True
        self.port = port
        threading.Thread(target=self.httpd.serve_forever, name="kb4it-serve", daemon=True).start()
        log.debug(f"[SERVE] LISTEN url={self.url} dir={self.directory} reload={self.reload}")
        return self

    def shutdown(self):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
