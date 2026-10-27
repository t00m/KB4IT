"""techdoc "Edit in the editor": a document page opens add.html with its source, in Chromium from file://."""

import pytest

from tests.browser.conftest import editor_text
from tests.core.test_highlight import _app_conf
from tests.helpers import run_kb4it, write_repo

pytestmark = pytest.mark.browser

SOURCE = ('---\nCategory: Procedure\nWorkType: Knowledge\nSummary: "Quotes, <tags> & ampersands"\n---\n\n'
          "# Edit me & check <this>\n\nText: 100% é ñ ü, `code <b>` and a+b=c?&x=1#frag.\n\n"
          '```bash\necho "a < b && c > d"   \n```\n')


@pytest.fixture(scope="module")
def edit_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("browser-edit")
    home = base / "home"
    home.mkdir()
    cfg = write_repo(base, "techdoc", {"edit-me.md": SOURCE}, **_app_conf("techdoc"))
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return base / "target"


@pytest.fixture
def doc_page(browser, edit_site):
    context = browser.new_context(accept_downloads=True)
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto((edit_site / "edit-me.html").as_uri())
    yield page
    context.close()


def open_editor(page):
    page.evaluate("() => document.querySelector('a[data-kb-edit]').click()")
    page.wait_for_function("() => !!(window.KB4ITEditor && KB4ITEditor.views._edit)")
    page.wait_for_function("() => document.getElementById('modal-add-_edit').open")


def test_the_editor_opens_with_the_exact_source_and_keeps_the_file_name(doc_page):
    assert doc_page.locator("a[data-kb-edit]").count() == 2  # title menu and History tab
    open_editor(doc_page)
    assert doc_page.url.endswith("/add.html")  # the text left the address
    assert editor_text(doc_page, "_edit") == SOURCE
    assert doc_page.text_content("#kb-edit-name") == "edit-me.md"
    assert doc_page.evaluate("() => KB4ITEditor.dirty('_edit')") is False
    with doc_page.expect_download() as download:
        doc_page.evaluate("() => KB4ITEditor.download('_edit')")
    assert download.value.suggested_filename == "edit-me.md"


def test_a_reload_does_not_open_the_document_again(doc_page):
    open_editor(doc_page)
    doc_page.reload()
    doc_page.wait_for_function("() => !!(window.KB4ITEditor && KB4ITEditor.open)")
    assert doc_page.evaluate("() => document.getElementById('modal-add-_edit').open") is False


def test_a_bad_address_opens_nothing(doc_page, edit_site):
    doc_page.goto((edit_site / "add.html").as_uri() + "#edit=..%2Fpasswd&text=x")
    doc_page.wait_for_function("() => !!(window.KB4ITEditor && KB4ITEditor.open)")
    assert doc_page.evaluate("() => document.getElementById('modal-add-_edit').open") is False
    assert "could not be read" in doc_page.text_content("#kb-toasts")
