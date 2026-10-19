"""Build hooks: each hook point, failures that stop the build, and the rebuild when the file changes."""

import json

from tests.helpers import page, run_kb4it, write_repo

HOOKS = '''
import json, os

def on_config(repo):
    repo["tagline"] = "Set by a hook"
    return repo

def on_document(doc_id, meta, text):
    return text.replace("PLACEHOLDER", "replaced for " + doc_id + " tags=" + ",".join(meta.get("Tag", [])))

def on_page(page, html):
    return html.replace("</body>", "<!-- on_page " + page + " --></body>")

def on_build_end(target, summary):
    with open(os.path.join(target, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh)
'''


def _repo(tmp_path, hooks_text=HOOKS, **conf):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", "PLACEHOLDER here.", Tag="x")},
                     hooks="hooks/hooks.py", **conf)
    (tmp_path / "repo" / "hooks").mkdir()
    (tmp_path / "repo" / "hooks" / "hooks.py").write_text(hooks_text, encoding="utf-8")
    return cfg, tmp_path / "repo" / "target"


def test_every_hook_runs(tmp_path, home):
    cfg, target = _repo(tmp_path)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "[HOOKS] LOADED" in result.stdout and "on_build_end" in result.stdout
    html = (target / "a.html").read_text(encoding="utf-8")
    assert "replaced for a.md tags=x" in html
    assert "<!-- on_page a.html -->" in html
    assert "Set by a hook" in (target / "index.html").read_text(encoding="utf-8")
    summary = json.loads((target / "summary.json").read_text(encoding="utf-8"))
    assert summary["docs_total"] == 1 and summary["compiled"] == 1


def test_failing_hook_stops_the_build(tmp_path, home):
    cfg, _target = _repo(tmp_path, "def on_document(doc_id, meta, text):\n    raise ValueError('bad doc')\n")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "[HOOKS] FAIL hook=on_document doc=a.md error=bad doc" in result.stdout


def test_missing_hooks_file(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")}, hooks="hooks/none.py")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "[HOOKS] MISSING" in result.stdout


def test_editing_hooks_rebuilds_everything(tmp_path, home):
    cfg, _target = _repo(tmp_path)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    path = tmp_path / "repo" / "hooks" / "hooks.py"
    path.write_text(HOOKS + "\n# edited\n", encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert "CORE_SIGNATURE_CHANGED" in result.stdout


def test_hooks_are_off_unless_named(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", "PLACEHOLDER", Tag="x")})
    (tmp_path / "repo" / "hooks").mkdir()
    (tmp_path / "repo" / "hooks" / "hooks.py").write_text(HOOKS, encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0
    assert "[HOOKS]" not in result.stdout
