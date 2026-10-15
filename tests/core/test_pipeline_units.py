"""Each service of the build pipeline works with stand-ins for its collaborators, without the app (AR-03, ARC-03)."""

import os

from kb4it.services.compiler import Compiler
from kb4it.services.deployer import Deployer
from kb4it.services.pipeline import Pipeline
from kb4it.services.processor import Processor


class _Backend:
    """What the pipeline services ask of the backend, over folders under tmp_path."""

    def __init__(self, root, kbdict=None, force=False, repo=None):
        self.root = root
        self.kbdict = kbdict or {"document": {}, "metadata": {}}
        self.values = {"app": {"force": force}, "runtime": {"force_all": False},
                       "repo": repo or {"workers": 1}, "docs": {"filenames": [], "targets": set()}}
        self.hooks = None
        self.markdown = None
        self.targets = []
        for name in ("source", "tmp", "cache", "target"):
            (root / name).mkdir(parents=True, exist_ok=True)

    def load_kbdict(self):
        return self.kbdict

    def get_path(self, name):
        return str(self.root if name == "root" else self.root / name)

    def get_value(self, domain, key):
        return self.values[domain].get(key)

    def get_dict(self, domain):
        return self.values[domain]

    def add_target(self, doc, html):
        self.targets.append(html)


class _Theme:
    def __init__(self):
        self.built = []

    def site_signature(self):
        return ""

    def backlinks_html(self, doc):
        return ""

    def build_page(self, path):
        self.built.append(os.path.basename(path))

    def inject_head_meta(self, html, name):
        return html.replace("<head>", f'<head><meta name="page" content="{name}">')


def _analysis(tmp_path, cached=True, force=False, body="b1"):
    previous = {"document": {"a.md": {"body_hash": "b1", "metadata_hash": "m1", "Title": "A"}}, "metadata": {}}
    backend = _Backend(tmp_path, kbdict=previous, force=force)
    if cached:
        (tmp_path / "cache" / "a.html").write_text("old", encoding="utf-8")
    processor = Processor(backend, db=None, theme=_Theme())
    processor.kbdict_new["document"]["a.md"] = {"body_hash": body, "metadata_hash": "m1", "Title": "A"}
    return processor.step_01_00_analyze_document("a.md")


def test_processor_decides_what_to_compile(tmp_path):
    assert _analysis(tmp_path / "same")["compile"] is False
    assert _analysis(tmp_path / "body", body="b2")["body_differs"] is True
    assert _analysis(tmp_path / "uncached", cached=False)["not_cached"] is True
    assert _analysis(tmp_path / "forced", force=True)["compile"] is True


def test_compiler_compiles_and_hands_each_page_to_the_theme(tmp_path):
    backend, theme = _Backend(tmp_path), _Theme()
    (tmp_path / "tmp" / "a.md").write_text("---\nTag: x\n---\n\n# A\n\n## Part\n\nText.\n", encoding="utf-8")
    progress = []
    compiler = Compiler(backend, db=None, theme=theme, processor=None,
                        callbacks={"progress_callback": lambda name, rc: progress.append((name, rc))})
    compiler.execute()
    html = (tmp_path / "tmp" / "a.html").read_text(encoding="utf-8")
    assert "Part" in html and "<h1" not in html
    assert theme.built == ["a.md"] and progress == [("a.md", True)] and compiler.failed == []


def test_deployer_adds_head_meta_and_publishes_sources(tmp_path):
    backend, theme = _Backend(tmp_path), _Theme()
    page = tmp_path / "tmp" / "a.html"
    page.write_text("<html><head></head><body>A</body></html>", encoding="utf-8")
    source = tmp_path / "source" / "a.md"
    source.write_text("# A\n", encoding="utf-8")
    log_file = tmp_path / "kb4it.log.1"
    log_file.write_text("log", encoding="utf-8")
    deployer = Deployer(backend, theme, log_file=str(log_file))
    deployer.step_04_copy_sources_to_target([str(source)])
    deployer.step_05_add_head_meta([str(page)])
    assert (tmp_path / "target" / "sources" / "a.md").is_file()
    assert '<meta name="page" content="a.html">' in page.read_text(encoding="utf-8")
    deployer.step_11_cleanup()
    assert not log_file.exists() and not page.exists()


def test_pipeline_wires_one_set_of_services(tmp_path):
    backend, theme = _Backend(tmp_path), _Theme()
    pipeline = Pipeline(backend, db=None, theme=theme, settings={}, callbacks=None, log_file=None)
    assert pipeline.compiler.srvprc is pipeline.processor
    assert pipeline.service("Deployer") is pipeline.deployer and pipeline.service("Theme") is None
    assert pipeline.processor.srvthm is theme is pipeline.compiler.srvthm is pipeline.deployer.srvthm
