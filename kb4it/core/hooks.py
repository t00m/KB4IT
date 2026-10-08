#!/usr/bin/env python

"""
Per-repository build hooks: Python functions a knowledge base can run at fixed points of a build.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

repo.json names the file with "hooks": "hooks/hooks.py". It may define any of:

    on_config(repo) -> dict            after repo.json is loaded and checked
    on_document(doc_id, meta, text)    before a document is compiled; returns the Markdown to compile
    on_page(page, html) -> str         after the theme built a page, before it is deployed
    on_build_end(target, summary)      after the build, with the summary counters

Hooks run with the same rights as KB4IT. on_document and on_page run in the
compiler's worker threads, so they must be thread safe.
"""

import hashlib
import importlib.util
import os

from kb4it.core.exceptions import CompilationError, ConfigError
from kb4it.core.log import get_logger

log = get_logger(__name__)

HOOK_NAMES = ("on_config", "on_document", "on_page", "on_build_end")


class Hooks:
    """The hooks of one repository; an empty Hooks() does nothing."""

    def __init__(self, path=None):
        self.path = path
        self.module = None
        if path is None:
            return
        if not os.path.isfile(path):
            log.error(f"[HOOKS] MISSING path={path}")
            raise ConfigError(f"Hooks file not found: {path}")
        digest = hashlib.blake2b(os.path.abspath(path).encode("utf-8"), digest_size=8).hexdigest()
        spec = importlib.util.spec_from_file_location(f"kb4it_repo_hooks_{digest}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as error:
            log.error(f"[HOOKS] LOAD_FAIL path={path} error={error}")
            raise ConfigError(f"Hooks file {path} cannot load: {error}") from error
        self.module = module
        found = [name for name in HOOK_NAMES if callable(getattr(module, name, None))]
        log.info(f"[HOOKS] LOADED path={path} hooks={','.join(found) or 'none'}")

    def has(self, name) -> bool:
        return self.module is not None and callable(getattr(self.module, name, None))

    def call(self, name, *args, doc=""):
        """Run a hook; any exception stops the build with CompilationError naming the hook."""
        try:
            return getattr(self.module, name)(*args)
        except Exception as error:
            log.error(f"[HOOKS] FAIL hook={name} doc={doc} error={error}")
            raise CompilationError(f"Hook {name} failed{' for ' + doc if doc else ''}: {error}") from error

    def signature(self) -> str:
        """Hash of the hooks file, so editing it rebuilds every page."""
        if not self.path:
            return ""
        with open(self.path, "rb") as fh:
            return hashlib.blake2b(fh.read()).hexdigest()


def load_hooks(repo: dict, root) -> Hooks:
    """Hooks named by repo.json "hooks" (relative to the repository root), or an empty Hooks()."""
    from kb4it.services.backend import resolve_repo_path
    value = repo.get("hooks")
    if value in (None, ""):
        return Hooks()
    if not isinstance(value, str):
        raise ConfigError("repo.json 'hooks' must be the path of a Python file")
    return Hooks(resolve_repo_path(value, root))
