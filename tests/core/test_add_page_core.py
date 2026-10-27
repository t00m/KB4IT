"""ET-06: the Add page is built in core, with shared templates."""

import json
import re

from kb4it.core.env import ENV
from tests.helpers import page, run_kb4it, write_repo
from tests.themes.test_techdoc_add import ADD_DOCS

COMMON = ENV["GPATH"]["TEMPLATES"]


def test_common_page_has_no_framework():
    from mako.template import Template
    with open(f"{COMMON}/PAGE_ADD.tpl", encoding="utf-8") as fin:
        tpl = Template(fin.read(), default_filters=["h"])
    var = {"page": {"categories": [{"id": "note", "name": "Note", "description": "d", "color": "#111",
                                    "icon": "x", "text": "t"}], "editor_dialogs": "<dialog></dialog>"},
           "repo": {}}
    html = tpl.render(var=var)
    assert "uk-" not in html
    assert "data-kb-open=\"note\"" in html
    assert html.count("<dialog") == 1


def test_hostile_category_text_escaped(tmp_path, home):
    cfg = write_repo(tmp_path, "techdoc", ADD_DOCS)
    skel = tmp_path / "overrides" / "templates" / "skeletons"
    skel.mkdir(parents=True)
    (skel / "EVIL-SKELETON.md").write_text("---\nDate: YYYY-MM-DD\n---\n\n# T\n", encoding="utf-8")
    (skel / "skeletons.json").write_text(
        json.dumps([{"id": "evil", "name": "<b>x</b>", "description": "</script>"}]), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "target" / "add.html").read_text(encoding="utf-8")
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "&lt;/script&gt;" in html
    assert "<b>x</b>" not in html
    assert html.count("<dialog") == 2  # the card's dialog and the Edit dialog


def test_system_page_and_keys(tmp_path, home):
    cfg = write_repo(tmp_path, "techdoc", ADD_DOCS)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "target" / "add.html").read_text(encoding="utf-8")
    keys = re.search(r'id="kb-add-keys" type="application/json">(.*?)</script>', html, re.S)
    assert {"v": "Note", "c": 2} in json.loads(keys.group(1))["Category"]
    log = (tmp_path / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")
    assert "[BUILDER] ADD_PAGE enabled=True skeletons=theme categories=8" in log


def test_editor_keys_counts_and_system_page():
    from kb4it.services.addpage import AddPageMixin

    class _Dtb:
        def __init__(self):
            self.added = []

        def get_documents(self):
            return ["a.md", "b.md"]

        def get_theme_keys(self):
            return ["Category", "Empty"]

        def get_values(self, doc, key):
            return ["Note"] if key == "Category" else [""]

    class _B(AddPageMixin):
        srvdtb = _Dtb()

    assert _B().editor_keys() == {"Category": [{"v": "Note", "c": 2}]}


def test_system_page():
    import logging

    from kb4it.services.addpage import AddPageMixin

    class _Dtb:
        def __init__(self):
            self.keys = {}

        def add_document(self, name):
            self.keys.setdefault(name, {})

        def add_document_key(self, name, key, value):
            self.keys[name][key] = value

    class _B(AddPageMixin):
        log = logging.getLogger("test")
        srvdtb = _Dtb()
        written = None

        def editor_enabled(self):
            return True

        def _render_add_page(self):
            return "<p>x</p>", "common", 1

        def distribute_md(self, name, content):
            self.written = (name, content)

    builder = _B()
    builder.create_page_add()
    assert builder.written == ("add", "<p>x</p>")
    assert builder.srvdtb.keys["add.md"] == {"Title": "Add document", "SystemPage": "Yes"}
