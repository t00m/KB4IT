"""State belongs to one build: nothing a build sets leaks into the next one in the same process (AR-05, ARC-06)."""

import ast
import json
import subprocess
import sys

from kb4it.services.builder import Builder
from tests.helpers import isolated_env, mini_theme, page, run_kb4it, write_repo


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


_KEEP_SETTINGS = '''
import json, os

kept = {}

def on_config(repo):
    kept["repo"] = repo
    return repo

def on_build_end(target, summary):
    with open(os.path.join(target, "repo-at-end.json"), "w", encoding="utf-8") as fh:
        json.dump(kept["repo"], fh)
'''


def test_settings_stay_as_loaded(tmp_path, home):
    """The build writes its decisions and the generation time elsewhere, not into repo.json's settings."""
    theme = mini_theme(tmp_path / "mini")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme),
                     hooks="hooks/hooks.py", force=False)
    (tmp_path / "repo" / "hooks").mkdir()
    (tmp_path / "repo" / "hooks" / "hooks.py").write_text(_KEEP_SETTINGS, encoding="utf-8")
    overrides = tmp_path / "repo" / "overrides" / "templates"
    overrides.mkdir(parents=True)
    (overrides / "PAGE_ABOUT_KB4IT.tpl").write_text(
        "<p id='a'>${var['updated']}</p><p id='b'>${var['repo']['updated']}</p>", encoding="utf-8")
    result = run_kb4it("build", cfg, "--force", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / "repo" / "target"
    seen = json.loads((target / "repo-at-end.json").read_text(encoding="utf-8"))
    assert "updated" not in seen and seen["force"] is False
    about = (target / "about_kb4it.html").read_text(encoding="utf-8")
    first = about.split("<p id='a'>", 1)[1].split("</p>", 1)[0]
    assert first and f"<p id='b'>{first}</p>" in about
