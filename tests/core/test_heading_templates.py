"""Default heading templates (Layer 2): a theme without _NEW templates still gets the section wrappers."""

from tests.helpers import mini_theme, page, run_kb4it, write_repo

PIPELINE_THEME = '''"""A page-pipeline theme with no templates of its own for headings."""

from kb4it.core.util import valid_filename
from kb4it.services.builder import Builder


class Theme(Builder):
    page_pipeline = True

    def build(self):
        pass

    def build_page_key(self, key, values):
        self.distribute_md(valid_filename(key), f"<p>{key}</p>")

    def build_page_key_value(self, kvpath):
        key, value, compile_value = kvpath
        if compile_value:
            self.distribute_md(f"{valid_filename(key)}_{valid_filename(value)}", f"<p>{key}: {value}</p>")

    def render_page(self, doc_id, var):
        """Override: the transformed body only."""
        return var["source_html"]
'''


def test_theme_without_new_templates_gets_section_wrappers(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    (theme / "logic" / "theme.py").write_text(PIPELINE_THEME, encoding="utf-8")
    body = "Intro.\n\n## First\n\nText.\n\n### Inner\n\nMore."
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", body, Tag="x")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8")
    assert 'class="kb-sect1"' in html and 'class="kb-sect2"' in html
    assert '<h2 class="kb-h2"' in html and '<h3 class="kb-h3"' in html
    assert "uk-" not in html, "the common defaults carry no framework classes"


def test_heading_attributes_stay_separated(tmp_path, home):
    """The class attribute and the compiler's id attribute keep a space between them."""
    theme = mini_theme(tmp_path / "mini")
    (theme / "logic" / "theme.py").write_text(PIPELINE_THEME, encoding="utf-8")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", "## First\n\nText.", Tag="x")}, theme_path=str(theme))
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    html = (tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8")
    assert '<h2 class="kb-h2" id="first">' in html
