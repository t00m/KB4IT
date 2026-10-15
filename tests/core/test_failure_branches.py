"""The compiler's failure branches: a document that cannot compile, a page that runs out of memory,
and a progress callback that fails (TS-01, TST-01)."""

import subprocess
import sys

from tests.helpers import isolated_env, page, run_kb4it, write_repo

# One build, in a process of its own, with the faults injected before KB4IT starts.
_FAULTY_BUILD = """
import argparse, sys
from kb4it.core import mdconfig
from kb4it.services import compiler

new_markdown = mdconfig.MarkdownSettings.new_markdown
def faulty_markdown(self):
    md = new_markdown(self)
    convert = md.convert
    def faulty_convert(text):
        if "BREAK-COMPILE" in text:
            raise ValueError("compile fault")
        return convert(text)
    md.convert = faulty_convert
    return md
mdconfig.MarkdownSettings.new_markdown = faulty_markdown

# The theme logic is loaded from its file, so wrap the instance the compiler uses.
execute = compiler.Compiler.execute
def faulty_execute(self):
    build_page = self.srvthm.build_page
    def faulty_build_page(path_hdoc, *args, **kwargs):
        if path_hdoc.endswith("oom.md"):
            raise MemoryError()
        return build_page(path_hdoc, *args, **kwargs)
    self.srvthm.build_page = faulty_build_page
    return execute(self)
compiler.Compiler.execute = faulty_execute

def failing_callback(name, rc):
    raise RuntimeError("callback fault")

from kb4it.core.main import KB4IT
params = argparse.Namespace(action="build", config=sys.argv[1], force=False, log_level="INFO",
                            progress_callback=failing_callback)
print("RUN_RESULT", KB4IT(params).run())
"""


def test_compile_and_render_failures(tmp_path, home):
    docs = {"good.md": page("Good", Tag="x"), "broken.md": page("Broken", "BREAK-COMPILE", Tag="x"),
            "oom.md": page("Oom", Tag="x")}
    cfg = write_repo(tmp_path / "repo", "techdoc", docs)
    result = subprocess.run([sys.executable, "-c", _FAULTY_BUILD, str(cfg)], cwd=str(tmp_path),
                            env=isolated_env(home, NO_COLOR="1", COLUMNS="1000"), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=600, check=False, encoding="utf-8")
    out = result.stdout
    assert "RUN_RESULT False" in out, out
    assert "MD_COMPILE_FAIL doc=broken.md error=compile fault" in out
    assert "COMPILE_FAILED doc=broken.md" in out
    assert "MEMORY_EXHAUSTED" in out
    assert "PAGES_FAILED n=2 pages=broken.html, oom.html" in out
    target = tmp_path / "repo" / "target"
    assert (target / "good.html").is_file()
    assert not (target / "broken.html").exists() and not (target / "oom.html").exists()
    # The failed build kept the previous cache, so the next build, without the faults, makes both pages.
    again = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert again.returncode == 0, again.stdout
    assert (target / "broken.html").is_file() and (target / "oom.html").is_file()
