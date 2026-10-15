"""Names that themes, hooks, templates and applications import keep working after a module split (AR-02)."""

import ast
import importlib

import pytest

from tests.helpers import ROOT

# Every public name of kb4it.core.util before it was split into dates, documents and files.
UTIL_NAMES = [
    "DateCache",
    "SOURCE_EXT_RE",
    "html_id_for",
    "SOURCE_ENCODING",
    "WINDOWS_RESERVED_NAMES",
    "is_windows_reserved",
    "page_name_clashes",
    "source_ext",
    "timeit",
    "extract_sections_from_md",
    "copy_docs",
    "get_default_workers",
    "copydir",
    "get_source_docs",
    "set_max_frequency",
    "get_font_size",
    "delete_target_contents",
    "delete_files",
    "json_load",
    "json_save",
    "quarantine",
    "get_hash_from_content",
    "get_hash_from_file",
    "first_heading",
    "fences_in_blocks",
    "raw_script_lines",
    "strip_first_heading",
    "get_hash_from_body",
    "get_markdown_attributes",
    "get_document_attributes",
    "tree_hash",
    "get_hash_from_dict",
    "get_hash_from_list",
    "valid_filename",
    "slugify",
    "human_size",
    "now",
    "get_year",
    "get_month",
    "get_day",
    "log_timestamp",
    "kb4it_timestamp",
    "guess_datetime",
    "string_timestamp",
    "get_human_datetime",
    "get_human_datetime_day",
    "get_human_datetime_month",
    "get_human_datetime_year",
    "get_timestamp_yyyymmdd",
    "sort_dictionary",
    "ellipsize_text",
]

# Every name kb4it.tui.app had before it was split into projects, servers, clipboard and screens.
TUI_NAMES = [
    "PROJECTS_FILE",
    "VERSION",
    "_LOG_STYLE",
    "load_projects",
    "save_projects",
    "get_themes",
    "get_apps",
    "_project_root",
    "_resolve_repo_path",
    "_log_path",
    "_kbdict_path",
    "KB4IT_DEFAULT_PORT",
    "KB4IT_PORT_SCAN_LIMIT",
    "_WEB_SERVERS",
    "_start_live_server",
    "_start_project_server",
    "_CLIPBOARD_TOOLS",
    "clipboard_commands",
    "_copy_to_clipboard",
    "_parse_level",
    "_reset_logging",
    "_TUILogHandler",
    "ConfirmScreen",
    "BuildScreen",
    "LogViewerScreen",
    "DocumentViewerScreen",
    "ExplorerScreen",
    "ProjectInfoScreen",
    "FileListScreen",
    "ThemesScreen",
    "AppsScreen",
    "CreateProjectScreen",
    "ImportProjectScreen",
    "ProjectScreen",
    "MainScreen",
    "KB4ITTUI",
    "run",
]


@pytest.mark.parametrize("name", UTIL_NAMES)
def test_util_names_still_import(name):
    util = importlib.import_module("kb4it.core.util")
    assert hasattr(util, name), name


def test_util_all_is_the_recorded_list():
    from kb4it.core import util
    assert sorted(util.__all__) == sorted(UTIL_NAMES)


@pytest.mark.parametrize("module", ["dates", "documents", "files"])
def test_split_modules_do_not_import_util(module):
    tree = ast.parse((ROOT / "kb4it" / "core" / f"{module}.py").read_text(encoding="utf-8"))
    imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imported |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert "kb4it.core.util" not in imported


def test_moved_names_are_the_same_objects():
    from kb4it.core import dates, documents, files, util
    assert util.guess_datetime is dates.guess_datetime
    assert util.get_markdown_attributes is documents.get_markdown_attributes
    assert util.valid_filename is files.valid_filename


@pytest.mark.parametrize("name", TUI_NAMES)
def test_tui_names_still_import(name):
    app = importlib.import_module("kb4it.tui.app")
    assert hasattr(app, name), name


def test_tui_app_all_is_the_recorded_list():
    from kb4it.tui import app
    assert sorted(app.__all__) == sorted(TUI_NAMES)
