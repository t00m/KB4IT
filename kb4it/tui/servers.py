"""
Local web servers of the TUI, one per project.
"""

from __future__ import annotations

from textual.app import App

from kb4it.core.webserver import DEFAULT_PORT, PORT_SCAN_LIMIT, SiteServer

KB4IT_DEFAULT_PORT = DEFAULT_PORT


KB4IT_PORT_SCAN_LIMIT = PORT_SCAN_LIMIT


# project config path -> (server, port)
_WEB_SERVERS: dict[str, tuple[SiteServer, int]] = {}


def _start_live_server(app: App, config: str, target_dir: str) -> tuple[SiteServer | None, int | None, str | None]:
    """Serve a project with live reload; rebuild it when its sources change and tell the user."""
    from kb4it.core.serve import Server

    def built(ok: bool, error: str) -> None:
        message = "Rebuilt the site" if ok else f"Rebuild failed: {error}"
        try:
            app.call_from_thread(app.notify, message, severity="information" if ok else "error")
        except Exception:
            pass

    live = Server({"config": config, "log_level": "INFO"}, holds_lock=False, on_build=built)
    try:
        server = live.start_background(target_dir)
    except OSError as exc:
        return None, None, str(exc)
    return server, server.port, None


def _start_project_server(target_dir: str) -> tuple[SiteServer | None, int | None, str | None]:
    try:
        server = SiteServer(target_dir).start()
    except OSError as exc:
        return None, None, str(exc)
    return server, server.port, None
