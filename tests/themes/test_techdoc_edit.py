"""techdoc "Edit in the editor": the links of a document page and the edit dialog of add.html."""

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo

DOCS = {"doc.md": page("A document", Category="Note")}


def build(tmp_path, **conf):
    home = tmp_path / "home"
    home.mkdir()
    cfg = write_repo(tmp_path, "techdoc", DOCS, **{**_app_conf("techdoc"), **conf})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return tmp_path / "target"


def test_document_page_links_to_the_editor_with_its_file_name(tmp_path):
    target = build(tmp_path)
    html = (target / "doc.html").read_text(encoding="utf-8")
    assert html.count('href="add.html" data-kb-edit="doc.md"') == 2
    assert 'id="source-code"' in html
    add = (target / "add.html").read_text(encoding="utf-8")
    assert 'id="modal-add-_edit"' in add and 'id="kb-edit-name"' in add and 'data-kb-save="_edit"' in add
    assert "<!-- EDIT DIALOG :: START -->" in add


def test_no_editor_link_when_the_editor_is_off(tmp_path):
    target = build(tmp_path, editor=False)
    assert "data-kb-edit" not in (target / "doc.html").read_text(encoding="utf-8")


def test_system_pages_have_no_editor_link(tmp_path):
    target = build(tmp_path)
    for name in ("index.html", "properties.html", "all.html"):
        assert "data-kb-edit" not in (target / name).read_text(encoding="utf-8"), name
