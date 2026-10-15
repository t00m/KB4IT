"""kbdict.json is written only after a successful build, so a failed build cannot leave stale pages (BO-02)."""

import json

from tests.helpers import page, run_kb4it, write_repo

FAIL_ONCE = '''
import os
MARK = os.path.join(os.path.dirname(__file__), "fail-once")

def on_document(doc_id, meta, text):
    if doc_id == "page.md" and os.path.exists(MARK):
        os.unlink(MARK)
        raise RuntimeError("transient failure")
    return text
'''


def test_page_is_rebuilt_after_a_failed_build(tmp_path, home):
    """The audit reproduction of COR-02."""
    cfg = write_repo(tmp_path / "repo", "techdoc", {"page.md": page("Page", "Version one.", Tag="x")},
                     hooks="hooks/hooks.py")
    hooks = tmp_path / "repo" / "hooks"
    hooks.mkdir()
    (hooks / "hooks.py").write_text(FAIL_ONCE, encoding="utf-8")
    target = tmp_path / "repo" / "target" / "page.html"

    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "Version one" in target.read_text(encoding="utf-8")

    (tmp_path / "repo" / "source" / "page.md").write_text(page("Page", "Version two.", Tag="x"), encoding="utf-8")
    (hooks / "fail-once").write_text("", encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 1

    third = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert third.returncode == 0, third.stdout
    assert "compiled=1" in third.stdout
    assert "Version two" in target.read_text(encoding="utf-8")


def test_failed_build_keeps_the_previous_cache(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    kbdict = tmp_path / "repo" / "var" / "db" / "kbdict.json"
    before = kbdict.read_bytes()
    # A new document plus a hook that fails on it: the build stops after extraction and analysis.
    (tmp_path / "repo" / "source" / "b.md").write_text(page("B", Tag="y"), encoding="utf-8")
    (tmp_path / "repo" / "hooks").mkdir()
    (tmp_path / "repo" / "hooks" / "hooks.py").write_text(
        "def on_document(doc_id, meta, text):\n    raise RuntimeError('no')\n", encoding="utf-8")
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["hooks"] = "hooks/hooks.py"
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 1
    assert kbdict.read_bytes() == before
