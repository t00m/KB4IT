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
