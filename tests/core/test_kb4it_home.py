"""KB4IT_HOME moves every per-user file; without it they live in ~/.kb4it."""

import os
import subprocess
import sys

from tests.helpers import ROOT

_SHOW = "from kb4it.core.env import ENV; print(ENV['LPATH']['ROOT']); print(ENV['FILE']['LOG'])"


def _env(**values):
    # Start from the real environment: Windows needs SYSTEMROOT and friends to start Python.
    env = {k: v for k, v in os.environ.items() if k not in ("KB4IT_HOME", "HOME", "USERPROFILE")}
    env.update(values, PYTHONPATH=str(ROOT))
    return env


def _paths(env):
    out = subprocess.run([sys.executable, "-c", _SHOW], env=env, cwd=str(ROOT), stdout=subprocess.PIPE,
                         text=True, encoding="utf-8", check=True).stdout.splitlines()
    return out


def test_kb4it_home_relocates_user_files(tmp_path):
    home, custom = tmp_path / "home", tmp_path / "portable"
    home.mkdir()
    env = _env(HOME=str(home), USERPROFILE=str(home), KB4IT_HOME=str(custom))
    root, log = _paths(env)
    assert root == str(custom)
    assert log.startswith(str(custom))
    assert not (home / ".kb4it").exists()


def test_default_is_dot_kb4it_in_home(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = _env(HOME=str(home), USERPROFILE=str(home))
    root, _log = _paths(env)
    assert root == str(home / ".kb4it")
