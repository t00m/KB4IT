"""Custom themes written for 0.11 keep building after the shared page pipeline (theme base, part 1)."""

import json

from tests.helpers import mini_theme, page, run_kb4it, write_repo

OLD_API_THEME = '''
from kb4it.services.builder import Builder
from kb4it.services.themekit.keypages import KeyPagesMixin


class Theme(KeyPagesMixin, Builder):
    def build(self):
        self.distribute_md("extra", "<p>extra</p>")
        self._add_system_page("extra", "Extra")

    def build_page(self, path_md):
        pass

    def post_deploy_activities(self):
        import os
        with open(os.path.join(self.srvbes.get_path("target"), "documents.json"), "w", encoding="utf-8") as fh:
            json.dump({"system": self.srvdtb.is_system("extra.md"),
                       "title": self.srvdtb.get_doc_properties("extra.md").get("Title")}, fh)


import json
'''


def _build(tmp_path, home, theme):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    return repo / "target"


def test_theme_that_overrides_build_page_still_builds(tmp_path, home):
    target = _build(tmp_path, home, mini_theme(tmp_path / "mini"))
    html = (target / "a.html").read_text(encoding="utf-8")
    assert '<meta name="docs" content=' in html  # rendered by the mini theme's own build_page()


def test_theme_calling_old_add_system_page_still_builds(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    (theme / "logic" / "theme.py").write_text(OLD_API_THEME, encoding="utf-8")
    target = _build(tmp_path, home, theme)
    assert json.loads((target / "documents.json").read_text(encoding="utf-8")) == {"system": True, "title": "Extra"}
    assert (target / "extra.html").exists()


NO_BUILD_PAGE_THEME = '''
from kb4it.services.builder import Builder


class Theme(Builder):
    def build(self):
        pass
'''

PIPELINE_THEME = '''
from kb4it.services.builder import Builder


class Theme(Builder):
    page_pipeline = True  # build_page() wraps every document in HTML_BODY

    def build(self):
        pass
'''


def test_theme_without_build_page_keeps_the_compiled_body(tmp_path, home):
    """A 0.11 theme that never overrode build_page() gets the compiled body, as before."""
    theme = mini_theme(tmp_path / "mini")
    (theme / "logic" / "theme.py").write_text(NO_BUILD_PAGE_THEME, encoding="utf-8")
    html = (_build(tmp_path, home, theme) / "a.html").read_text(encoding="utf-8")
    assert "Text." in html and '<meta name="docs"' not in html


def test_minimal_theme_on_the_pipeline_needs_only_html_body(tmp_path, home):
    """A theme that opts in gets header, footer and heading templates only when it has them."""
    theme = mini_theme(tmp_path / "mini")
    (theme / "logic" / "theme.py").write_text(PIPELINE_THEME, encoding="utf-8")
    (theme / "templates" / "HTML_BODY.tpl").write_text(
        "<html><body><h1>${var['page']['title']}</h1>${var['source_html'] | n}</body></html>", encoding="utf-8")
    html = (_build(tmp_path, home, theme) / "a.html").read_text(encoding="utf-8")
    assert "<h1>A</h1>" in html and "Text." in html
