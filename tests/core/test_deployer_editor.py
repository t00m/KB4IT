"""ED-02: the editor assets are deployed only to sites whose pages load them."""

from tests.core.test_highlight import _app_conf
from tests.core.test_build_failures import _Backend
from tests.helpers import page, run_kb4it, write_repo

LOADS = '<html><script src="resources/editor/kb4it-editor.js"></script></html>'


def _deployer(tmp_path):
    from kb4it.services.deployer import Deployer
    target = tmp_path / "target"
    target.mkdir()
    return Deployer(_Backend(tmp_path / "cache", target, []), theme=None), target


def test_deploy_copies_when_a_page_loads_the_editor(tmp_path):
    deployer, target = _deployer(tmp_path)
    (target / "add.html").write_text(LOADS, encoding="utf-8")
    deployer.deploy_page_assets()
    assert (target / "resources" / "editor" / "codemirror.min.js").is_file()


def test_deploy_removes_stale_folder(tmp_path):
    deployer, target = _deployer(tmp_path)
    (target / "add.html").write_text(LOADS, encoding="utf-8")
    deployer.deploy_page_assets()
    (target / "add.html").write_text("<html>plain</html>", encoding="utf-8")
    deployer.deploy_page_assets()
    assert not (target / "resources" / "editor").exists()


def test_text_naming_the_folder_does_not_count(tmp_path):
    deployer, target = _deployer(tmp_path)
    (target / "add.html").write_text("<p>resources/editor/</p>", encoding="utf-8")
    deployer.deploy_page_assets()
    assert not (target / "resources" / "editor").exists()


def _build(tmp_path, home, theme, extra_args=()):
    pages = {"one.md": page("One", "Text.\n", Category="Post", Date="2026-10-08", DocType="Reference")}
    cfg = write_repo(tmp_path / theme, theme, pages, **_app_conf(theme))
    result = run_kb4it(*extra_args, "build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return result, tmp_path / theme / "target"


def test_techdoc_build_deploys_editor(tmp_path, home):
    _result, target = _build(tmp_path, home, "techdoc")
    assert (target / "resources" / "editor" / "codemirror.min.js").is_file()


def test_blog_build_has_no_editor(tmp_path, home):
    _result, target = _build(tmp_path, home, "blog")
    assert not (target / "resources" / "editor").exists()


def test_log_event(tmp_path, home):
    result, _target = _build(tmp_path, home, "blog", ("-L", "DEBUG"))
    assert "[DEPLOYER] EDITOR_ASSETS deployed=False" in result.stdout
