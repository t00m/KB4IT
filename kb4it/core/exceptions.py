#!/usr/bin/env python

"""
KB4IT domain exception hierarchy.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""


class KB4ITError(Exception):
    """Base class for all KB4IT domain errors."""


class ConfigError(KB4ITError):
    """repo.json is missing or has invalid/missing required keys."""


class ThemeError(KB4ITError):
    """Theme could not be loaded, or a required template is missing."""


class CompilationError(KB4ITError):
    """A document or key/value page failed to compile."""


class LockBusyError(KB4ITError):
    """Another KB4IT process holds the lock."""

    def __init__(self, path, pid=None):
        self.path = str(path)
        self.pid = pid
        holder = f" (PID {pid})" if pid else ""
        super().__init__(f"Lock {self.path} is held by another KB4IT process{holder}")
