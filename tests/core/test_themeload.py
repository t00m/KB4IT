"""kb4it/core/themeload.py: logic/ is loaded as a package of its own."""

import sys

import pytest

from kb4it.core.themeload import is_theme_module, load_module, package_name


def make_logic(root, name, helper_value, *, relative=False, init=False):
    logic = root / name / "logic"
    logic.mkdir(parents=True)
    (logic / "helper.py").write_text(f"VALUE = {helper_value!r}\n", encoding="utf-8")
    imp = "from .helper import VALUE" if relative else "from helper import VALUE"
    (logic / "theme.py").write_text(f"{imp}\n\nclass Theme:\n    value = VALUE\n", encoding="utf-8")
    if init:
        (logic / "__init__.py").write_text("PACKAGE_INIT = True\n", encoding="utf-8")
    return logic


@pytest.fixture(autouse=True)
def clean_helper():
    yield
    sys.modules.pop("helper", None)


def test_two_themes_with_the_same_helper_name_keep_their_own(tmp_path):
    one = make_logic(tmp_path, "one", "first")
    two = make_logic(tmp_path, "two", "second")
    assert load_module(str(one), "one").Theme.value == "first"
    assert load_module(str(two), "two").Theme.value == "second"
    # Loading the first again gives its own helper, not the one cached by the second.
    assert load_module(str(one), "one").Theme.value == "first"


def test_relative_imports_work(tmp_path):
    logic = make_logic(tmp_path, "rel", "relative", relative=True)
    module = load_module(str(logic), "rel")
    assert module.Theme.value == "relative"
    assert module.__name__ == package_name("rel", str(logic)) + ".theme"
    assert is_theme_module(module.__name__)


def test_package_init_runs_when_present(tmp_path):
    logic = make_logic(tmp_path, "init", "x", relative=True, init=True)
    module = load_module(str(logic), "init")
    package = sys.modules[module.__name__.rsplit(".", 1)[0]]
    assert package.PACKAGE_INIT is True


def test_bare_import_is_one_module_and_is_reported_once(tmp_path):
    logic = make_logic(tmp_path, "bare", "bare")
    seen = []
    module = load_module(str(logic), "bare", on_bare_import=seen.append)
    package = module.__name__.rsplit(".", 1)[0]
    assert seen == ["helper"]
    assert sys.modules["helper"] is sys.modules[f"{package}.helper"]
    assert sys.modules["helper"].__spec__.name == f"{package}.helper"
    import helper  # noqa: F401  (a second bare import is not reported again)
    assert seen == ["helper"]


def test_reload_runs_the_files_again(tmp_path):
    logic = make_logic(tmp_path, "again", "old")
    assert load_module(str(logic), "again").Theme.value == "old"
    (logic / "helper.py").write_text("VALUE = 'newer'\n", encoding="utf-8")
    assert load_module(str(logic), "again").Theme.value == "newer"


def test_same_id_in_two_folders_gets_two_packages(tmp_path):
    a = make_logic(tmp_path / "bundled", "same", "a")
    b = make_logic(tmp_path / "user", "same", "b")
    assert package_name("same", str(a)) != package_name("same", str(b))
    assert load_module(str(a), "same").Theme.value == "a"
    assert load_module(str(b), "same").Theme.value == "b"


def test_a_stdlib_name_is_never_taken(tmp_path):
    logic = make_logic(tmp_path, "std", "x")
    (logic / "json.py").write_text("BROKEN = True\n", encoding="utf-8")
    load_module(str(logic), "std")
    import json
    assert not hasattr(json, "BROKEN")


def test_missing_folder_is_an_import_error(tmp_path):
    with pytest.raises(ImportError):
        load_module(str(tmp_path / "nothing"), "x")
