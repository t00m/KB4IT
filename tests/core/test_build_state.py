"""State belongs to one build: nothing a build sets leaks into the next one in the same process (AR-05, ARC-06)."""

import ast
import subprocess
import sys

from kb4it.services.builder import Builder
from tests.helpers import isolated_env, mini_theme, page, write_repo


class _App:
    def get_service(self, name):
        return object()


def _started_builder():
    builder = Builder()
    builder.start(_App())
    return builder


def test_builders_do_not_share_theme_variables():
    first, second = _started_builder(), _started_builder()
    first.theme_var["x"] = 1
    assert second.theme_var == {}
    assert "theme_var" not in vars(Builder)
    assert first.templates is not second.templates


_CALLBACK_BUILDS = """
import argparse, sys
from kb4it.core.main import KB4IT
from kb4it.services import compiler

seen = {"first": [], "second": [], "deprecated": []}
def build(config, **callbacks):
    params = argparse.Namespace(action="build", config=config, force=True, log_level="DEBUG", **callbacks)
    assert KB4IT(params).run()

build(sys.argv[1], progress_callback=lambda name, rc: seen["first"].append(name),
      compile_start_callback=lambda total: seen["first"].append(total))
build(sys.argv[1], progress_callback=lambda name, rc: seen["second"].append(name))
compiler.set_progress_callback(lambda name, rc: seen["deprecated"].append(name))
build(sys.argv[1])
build(sys.argv[1])
for name in ("first", "second", "deprecated"):
    print(name.upper(), sorted(map(str, seen[name])))
"""


def test_each_build_calls_its_own_callbacks(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="y")},
                     theme_path=str(theme))
    result = subprocess.run([sys.executable, "-c", _CALLBACK_BUILDS, str(cfg)], cwd=str(tmp_path),
                            env=isolated_env(home, NO_COLOR="1", COLUMNS="1000"), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=600, check=False, encoding="utf-8")
    out = result.stdout
    assert result.returncode == 0, out
    seen = {line.split(" ", 1)[0]: ast.literal_eval(line.split(" ", 1)[1])
            for line in out.splitlines() if line.startswith(("FIRST ", "SECOND ", "DEPRECATED "))}
    pages = seen["SECOND"]
    assert {"a.md", "b.md"} <= set(pages)
    # The first build also got the number of documents, from its own start callback.
    assert seen["FIRST"] == sorted([*pages, str(len(pages))])
    # A callback set the deprecated way serves the next build only, once.
    assert seen["DEPRECATED"] == pages
    assert out.count("CALLBACK_DEPRECATED name=progress_callback") == 1
