#!/usr/bin/env python

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Website static-generator based on Markdown
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import uuid
from typing import TYPE_CHECKING, Any, Literal, overload

from kb4it.core.env import ENV
from kb4it.core.exceptions import KB4ITError, CompilationError, ConfigError, LockBusyError, ThemeError
from kb4it.core.lock import FileLock, repo_lock_path
from kb4it.core.log import get_logger, setup_logging
from kb4it.core.version import git_describe
from kb4it.services.backend import Backend
from kb4it.services.builder import Builder
from kb4it.services.database import Database
from kb4it.services.frontend import Frontend
from kb4it.services.workflow import Workflow

if TYPE_CHECKING:
    from kb4it.core.service import Service
    from kb4it.services.compiler import Compiler
    from kb4it.services.deployer import Deployer
    from kb4it.services.processor import Processor

# Actions that write into a repository take its lock: <root>/var/kb4it.lock.
LOCKED_ACTIONS = ("build", "create")
# Parameters that carry code for the build to call, not settings (see services/compiler.py).
CALLBACK_PARAMS = ("progress_callback", "compile_start_callback")
# Services of one build that live in backend.pipeline; get_service still answers them for now.
PIPELINE_SERVICES = ("Processor", "Compiler", "Deployer")


def lock_path_for(params: dict):
    """Lock file for the action in params, or None when the action takes no lock."""
    action = params.get("action")
    if params.get("lock_held"):
        return None  # kb4it serve holds the repository lock for its whole run
    if action == "build" and params.get("config"):
        return repo_lock_path(params["config"])
    if action == "create" and params.get("repo_path"):
        # Kept outside the new repository, so a failed create leaves no folder behind.
        digest = hashlib.blake2b(os.path.abspath(params["repo_path"]).encode("utf-8"), digest_size=8).hexdigest()
        return os.path.join(ENV["LPATH"]["VAR"], f"create-{digest}.lock")
    return None


class KB4IT:
    """KB4IT main class."""

    repo = {}

    def __init__(self, params: argparse.Namespace = None):
        """Initialize KB4IT class.

        Setup environment.
        Initialize main log.
        Register main services.
        """
        self.next_steps = []
        self.set_log_file()
        self.__setup_environment()
        if params is not None:
            self.params = vars(params)
        else:
            self.params = vars(argparse.Namespace())
            self.params["REPO_CONFIG_FILE"] = None
        # Callbacks are code, not settings: keep them out of the parameters, which are logged
        # and passed to the templates. The compiler of this build calls them.
        self.callbacks = {name: self.params.pop(name) for name in CALLBACK_PARAMS if name in self.params}

        # Initialize log
        if "log_level" not in self.params:
            self.params["LOGLEVEL"] = "INFO"
        setup_logging(self.params["log_level"], self.log_file)
        self.log = get_logger(__class__.__name__)
        self.log.debug(f"[CONTROLLER] KB4IT version={ENV['APP']['version']}")
        self.log.debug(f"[CONTROLLER] SYS python={ENV['SYS']['PYTHON']['VERSION']}")
        self.log.debug(f"[CONTROLLER] SYS mako={ENV['SYS']['MAKO']['VERSION']}")
        self.log.debug(f"[CONTROLLER] SYS platform={ENV['SYS']['PLATFORM']['OS']} family={ENV['SYS']['PLATFORM']['FAMILY']}")
        self.log.debug(f"[CONTROLLER] GPATH_ROOT path={ENV['GPATH']['ROOT']}")
        self.log.debug(f"[CONTROLLER] LPATH_ROOT path={ENV['LPATH']['ROOT']}")

        # Start up
        self.__check_params()
        self.__setup_services()

    def set_log_file(self):
        """Generate a temporary log file."""
        suffix = str(uuid.uuid1().time)
        self.log_file = f"{ENV['FILE']['LOG']}.{suffix}"

    def get_log_file(self):
        """Get log file path."""
        return self.log_file

    def __check_params(self):
        """Check arguments passed to the application."""
        for key in sorted(self.params):
            self.log.debug(f"[CONTROLLER] PARAM name={key} value={self.params[key]}")

    def get_params(self):
        """Return app configuration."""
        return self.params

    def __setup_environment(self):
        """Create local paths if they do not exist."""
        for path in ENV["LPATH"].values():
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

    def __setup_services(self):
        """Declare and register services."""
        self.services = {}
        self._deprecated_logged = set()
        services = {
            "DB": Database(),
            "Backend": Backend(),
            "Frontend": Frontend(),
            "Builder": Builder(),
            "Workflow": Workflow(),
        }
        for name, klass in services.items():
            self.register_service(name, klass)

    def get_services(self):
        """Get all registered services."""
        return self.services

    @overload
    def get_service(self, name: Literal["DB"]) -> Database: ...
    @overload
    def get_service(self, name: Literal["Backend"]) -> Backend: ...
    @overload
    def get_service(self, name: Literal["Frontend"]) -> Frontend: ...
    @overload
    def get_service(self, name: Literal["Builder"]) -> Builder: ...
    @overload
    def get_service(self, name: Literal["Workflow"]) -> Workflow: ...
    @overload
    def get_service(self, name: Literal["Theme"]) -> Builder: ...
    @overload
    def get_service(self, name: Literal["Processor"]) -> Processor: ...
    @overload
    def get_service(self, name: Literal["Compiler"]) -> Compiler: ...
    @overload
    def get_service(self, name: Literal["Deployer"]) -> Deployer: ...
    @overload
    def get_service(self, name: str) -> Service: ...

    def get_service(self, name: str) -> Any:
        """Get or start a registered service."""
        if name in PIPELINE_SERVICES:
            return self._pipeline_service(name)
        service = self.services.get(name) or None
        if service is None:
            self.log.error(f"[CONTROLLER] SERVICE_NOT_REGISTERED name={name}")
            raise KB4ITError(f"Service not registered: {name}")
        if not service.is_started():
            service.start(self)
        return service

    def _pipeline_service(self, name: str):
        """Deprecated: the Processor, Compiler and Deployer of this build belong to backend.pipeline.

        Answered from the current pipeline for now, with a debug line once per name; removed in the next minor release.
        """
        backend = self.services.get("Backend")
        pipeline = getattr(backend, "pipeline", None)
        if pipeline is None:
            self.log.error(f"[CONTROLLER] SERVICE_NOT_REGISTERED name={name}")
            raise KB4ITError(f"Service not registered: {name}")
        if name not in self._deprecated_logged:
            self._deprecated_logged.add(name)
            self.log.debug(f"[CONTROLLER] SERVICE_DEPRECATED name={name} replacement=backend.pipeline")
        return pipeline.service(name)

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.debug(f"[CONTROLLER] SERVICE_REGISTER name={name}")
            return service
        except KeyError as error:
            self.log.error(f"[CONTROLLER] ERROR {error}")
            return None

    def deregister_service(self, name):
        """Deregister a running service."""
        service = self.services.get(name)
        registered = service is not None
        started = service.is_started()
        if registered and started:
            service.end()
            self.log.debug(f"[CONTROLLER] SERVICE_UNREGISTER name={name}")
        service = None

    def run(self):
        """Run the requested action. Returns True on success, False on error."""
        action = self.params["action"]
        self.log.debug(f"[CONTROLLER] START version={ENV['APP']['version']}")
        self.log.debug(f"[CONTROLLER] ACTION name={action}")
        error = False
        lock = None
        try:
            path = lock_path_for(self.params)
            if path is not None:
                lock = FileLock(path)
                lock.acquire()
                self.log.debug(f"[LOCK] ACQUIRED path={path}")
            workflow = self.get_service("Workflow")
            if action == "themes":
                workflow.list_themes()
            elif action == "projects":
                workflow.list_projects()
            elif action == "create":
                workflow.create_repository()
                for line in self.next_steps:
                    print(line)
            elif action == "build":
                workflow.build_website()
            elif action == "info":
                workflow.info_repository()
            elif action == "verify":
                workflow.verify_sources()
            elif action == "apps":
                workflow.list_apps(self.params["theme"])
        except LockBusyError as e:
            self.log.error(f"[LOCK] BUSY path={e.path} pid={e.pid}")
            holder = f" (PID {e.pid})" if e.pid else ""
            print(f"KB4IT is already working on this repository{holder}", file=sys.stderr)
            error = True
        except ConfigError as e:
            self.log.error(f"[CONTROLLER] CONFIG_ERROR reason={e}")
            error = True
        except ThemeError as e:
            self.log.error(f"[CONTROLLER] THEME_ERROR reason={e}")
            error = True
        except CompilationError as e:
            self.log.error(f"[CONTROLLER] COMPILE_ERROR reason={e}")
            error = True
        except KB4ITError as e:
            self.log.error(f"[CONTROLLER] KB4IT_ERROR reason={e}")
            error = True
        finally:
            if lock is not None:
                lock.release()
        self.stop(error=error)
        return not error

    def stop(self, error=False):
        """Stop registered services by executing the 'end' method (if any)."""
        if error:
            self.log.error("[CONTROLLER] ABORT reason=serious_errors")
        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError as errmsg:
            # KB4IT wasn't even started
            self.log.error(f"[CONTROLLER] ERROR {errmsg}")
        self.log.debug(f"[CONTROLLER] END version={ENV['APP']['version']}")


def version_text():
    """'KB4IT 1.2.3', plus the git describe of a source checkout so development builds are identifiable."""
    text = f"{ENV['APP']['shortname']} {ENV['APP']['version']}"
    described = git_describe(os.path.dirname(ENV["CONF"]["ROOT"]))
    return f"{text} ({described})" if described else text


def _log_hint(params) -> str:
    """' (see <repo>/var/log/kb4it.log)' when the action has a repository whose log exists, else ''."""
    config = getattr(params, "config", None)
    if not isinstance(config, str):
        return ""
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(config))), "var", "log", "kb4it.log")
    return f" (see {log_file})" if os.path.exists(log_file) else ""


def main():
    """Set up application arguments and execute."""
    # When called with no arguments in an interactive terminal, launch the TUI
    if len(sys.argv) == 1 and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            from kb4it.tui.app import run as run_tui
            run_tui()
        except ImportError as exc:
            print(f"TUI requires the 'textual' library: {exc}")
            print("Install it with: pip install textual")
        except KeyboardInterrupt:
            pass
        return

    extra_usage = """Thanks for using KB4IT!\n"""
    parser = argparse.ArgumentParser(
        prog="kb4it",
        description=f"KB4IT v{ENV['APP']['version']}\nCustomizable \
            static website generator based on Markdown sources",
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-L",
        "--log-level",
        help="Control output verbosity. Default set to INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version_text(),
    )

    # Add subcommands for actions
    subparsers = parser.add_subparsers(
        dest="action", required=True, help="Action to perform"
    )

    # Initialize repository
    init_parser = subparsers.add_parser(
        "create", help="Initialize a new repository")
    init_parser.add_argument("theme", help="Theme to use for initialization")
    init_parser.add_argument(
        "app",
        nargs="?",
        default="default",
        help="App template to use (default: 'default')",
    )
    init_parser.add_argument("repo_path", help="Path to the repository")

    # List themes
    subparsers.add_parser("themes", help="List all installed themes")

    # Help center
    help_parser = subparsers.add_parser("help", help="Open the KB4IT help center")
    help_group = help_parser.add_mutually_exclusive_group()
    help_group.add_argument("--url", action="store_true", help="Print the online help address and exit")
    help_group.add_argument("--dismiss", action="store_true", help="Hide the first-run help notice")

    # List projects
    subparsers.add_parser("projects", help="List all projects created by the user")

    # List apps for a specific theme
    theme_apps = subparsers.add_parser(
        "apps", help="List all apps for a specific theme"
    )
    theme_apps.add_argument("theme", help="Theme to query")

    # Run repository workflow
    repo_build = subparsers.add_parser(
        "build",
        help="Run workflow for a given repository",
        description="Based on your repository configuration, compile and build the website",
        epilog="Example:\n\n"
        "   kb4it build /home/jsmith/Documents/myrepo/config/repo.json",
    )

    repo_build.add_argument(
        "config", help="Path to the repository config file (mandatory)"
    )
    repo_build.add_argument(
        "-f", "--force",
        action="store_true",
        default=False,
        help="Force recompilation of all documents, ignoring content hashes",
    )

    # Build, serve and rebuild on change
    repo_serve = subparsers.add_parser(
        "serve",
        help="Build, serve the site locally and rebuild when sources change",
        description="Build the website, serve it on a local web server and rebuild it when a source, "
        "repo.json or the theme changes. Pages reload in the browser after each rebuild.",
        epilog="Example:\n\n"
        "   kb4it serve /home/jsmith/Documents/myrepo/config/repo.json",
    )
    repo_serve.add_argument("config", help="Path to the repository config file (mandatory)")
    repo_serve.add_argument("--host", default="127.0.0.1",
                            help="Address to listen on (default 127.0.0.1, this computer only)")
    repo_serve.add_argument("--port", type=int, default=8642,
                            help="First port to try; the next free one is used when it is busy (default 8642)")
    repo_serve.add_argument("--no-watch", action="store_true", help="Serve without rebuilding on changes")
    repo_serve.add_argument("--no-reload", action="store_true", help="Do not reload pages in the browser")
    repo_serve.add_argument("--open", action="store_true", help="Open the site in the web browser")
    repo_serve.add_argument("--interval", type=float, default=1.0,
                            help="Seconds between checks for changes (default 1.0)")
    repo_serve.add_argument("-f", "--force", action="store_true", default=False,
                            help="Force recompilation of all documents in the first build")

    # Get repository info
    repo_info = subparsers.add_parser(
        "info",
        help="Get repository info from its config file",
        description="Based on your repository configuration, get all info available",
        epilog="Example:\n\n"
        "   kb4it info /home/jsmith/Documents/myrepo/config/repo.json",
    )

    repo_info.add_argument(
        "config", help="Path to the repository config file (mandatory)"
    )

    # Verify repository sources
    repo_verify = subparsers.add_parser(
        "verify",
        help="Verify project sources for a given repository",
        description="Check if all source files in the project are KB4IT conformant",
        epilog="Example:\n\n"
        "   kb4it verify /home/jsmith/Documents/myrepo/config/repo.json",
    )

    repo_verify.add_argument(
        "config", help="Path to the repository config file (mandatory)"
    )

    # Dispatch to the appropriate action handler
    params = None
    try:
        params = parser.parse_args()
        if params.action != "help" and not os.environ.get("CI"):
            from kb4it.core.notice import (HELP_ONLINE_URL, help_notice_dismissed,
                                           help_notice_lines, offline_index)
            if not help_notice_dismissed():
                for line in help_notice_lines(offline_index(), HELP_ONLINE_URL):
                    print(line, file=sys.stderr)
        if params.action == "serve":
            from kb4it.core.serve import run_serve
            sys.exit(run_serve(vars(params)))
        if params.action == "help":
            from kb4it.core.notice import run_help
            sys.exit(run_help(url=params.url, dismiss=params.dismiss))
        app = KB4IT(params)
        success = app.run()
        sys.exit(0 if success else 1)
    except SystemExit:
        raise
    except Exception as error:
        print(f"Error: {type(error).__name__}: {error}{_log_hint(params)}")
        print("Run 'kb4it <action name> --help' to get help for a specific command.")
        sys.exit(1)


if __name__ == "__main__":
    main()
