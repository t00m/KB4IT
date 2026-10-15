"""A page that cannot be made fails the build, and every other page is still deployed (BO-01)."""

import json
import shutil

from tests.helpers import ROOT, page, run_kb4it, write_repo

TECHDOC_FOOTER = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "templates" / "HTML_FOOTER.tpl"


def _one_bad_page(tmp_path):
    """techdoc site whose footer template raises for the document titled "Bad"."""
    cfg = write_repo(tmp_path / "repo", "techdoc",
                     {"good.md": page("Good", Tag="x"), "bad.md": page("Bad", Tag="x")})
    templates = tmp_path / "repo" / "overrides" / "templates"
    templates.mkdir(parents=True)
    footer = TECHDOC_FOOTER.read_text(encoding="utf-8")
    trap = "<% if var['page'].get('title') == 'Bad': raise ValueError('broken footer') %>"
    (templates / "HTML_FOOTER.tpl").write_text(trap + footer, encoding="utf-8")
    return cfg, tmp_path / "repo" / "target"


def test_a_failed_page_fails_the_build(tmp_path, home):
    cfg, target = _one_bad_page(tmp_path)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1, result.stdout
    assert "failed=1" in result.stdout
    assert "[WORKFLOW] PAGES_FAILED n=1 pages=bad.html" in result.stdout
    # Every other page is deployed; the failed one is not left half-made.
    assert (target / "good.html").is_file()
    assert (target / "index.html").is_file()
    assert not (target / "bad.html").exists()


def test_on_build_end_sees_the_failure(tmp_path, home):
    cfg, target = _one_bad_page(tmp_path)
    hooks = tmp_path / "repo" / "hooks"
    hooks.mkdir()
    (hooks / "hooks.py").write_text(
        "import json, os\n"
        "def on_build_end(target, summary):\n"
        "    open(os.path.join(target, 'summary.json'), 'w').write(json.dumps(summary))\n", encoding="utf-8")
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["hooks"] = "hooks/hooks.py"
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert json.loads((target / "summary.json").read_text(encoding="utf-8"))["failed"] == 1


def test_blog_without_tagline_fails(tmp_path, home):
    """The audit reproduction of COR-01: every page failed and the build exited 0."""
    repo = tmp_path / "blog"
    assert run_kb4it("create", "blog", repo, cwd=tmp_path, home=home).returncode == 0
    cfg = repo / "config" / "repo.json"
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf.pop("tagline", None)
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "PAGES_FAILED" in result.stdout


class _Backend:
    """Just what Deployer.step_07 reads."""

    def __init__(self, cache, target, pages):
        self.paths = {"cache": str(cache), "target": str(target)}
        self.runtime = {"docs": {"targets": set(pages)}}

    def get_dict(self, name):
        return self.runtime

    def get_path(self, name):
        return self.paths[name]

    def get_deployed_before(self):
        return None

    def set_deployed(self, pages):
        self.deployed = sorted(pages)


def test_a_page_missing_from_the_cache_does_not_stop_the_deploy(tmp_path):
    """COR-09: the deploy used to stop at the first missing page, leaving the rest uncopied."""
    from kb4it.services.deployer import Deployer
    cache, target = tmp_path / "cache", tmp_path / "target"
    cache.mkdir()
    target.mkdir()
    (cache / "b.html").write_text("b", encoding="utf-8")
    (cache / "c.html").write_text("c", encoding="utf-8")
    deployer = Deployer(_Backend(cache, target, ["a.html", "b.html", "c.html"]), theme=None)
    deployer.step_07_copy_compiled_documents_to_target()
    assert deployer.missing == ["a.html"]
    assert (target / "b.html").is_file() and (target / "c.html").is_file()


def test_clean_build_reports_no_failure(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0 and "failed=0" in result.stdout
    shutil.rmtree(tmp_path / "repo")
