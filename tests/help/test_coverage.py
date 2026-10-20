"""The help center names every command, theme, repo.json key and error code a user can meet.

The checks look for names only, not prose. Each list comes from the code, so a new
command, theme, key or code fails here until a help page names it.
"""

import ast
import re
from pathlib import Path

import pytest

from kb4it.core.main import build_parser
from tests.helpers import ROOT

HELP_SOURCE = ROOT / "help" / "source"
PACKAGE = ROOT / "kb4it"
THEMES = PACKAGE / "resources" / "themes"
OFFLINE = PACKAGE / "resources" / "help"
APPHELP = THEMES / "apphelp"
FRAMEWORK_NAME = "taxis"  # matches both spellings of the framework name, in any case
SECTIONS = ("Start here", "Guides", "Reference", "Concepts", "Questions")

# A log tag: "[COMPONENT] CODE ...", where CODE is upper case words joined by "_".
CODE_TAG = re.compile(r"^\[[A-Z0-9_]+\] ([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b")
# Log levels a user sees in a normal run; DEBUG and INFO tags are not error codes.
USER_LEVELS = {"error", "warning", "critical", "exception"}
# Calls whose first argument is a problem code (the apphelp checks report through Problem).
CODE_CALLS = {"Problem"}
# Names that hold the settings of repo.json in the code.
REPO_NAMES = {"repo", "_repo"}
# Key lists the code validates or hashes: Backend.REQUIRED_CONFIG_KEYS, builder.GIT_KEYS,
# the apphelp SIGNATURE_REPO_KEYS and processor.NON_PAGE_KEYS. Read from the source, since
# theme logic modules are not importable on their own.
REPO_KEY_LISTS = {"REQUIRED_CONFIG_KEYS", "GIT_KEYS", "SIGNATURE_REPO_KEYS", "NON_PAGE_KEYS"}


def _pages() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(HELP_SOURCE.glob("*.md"))}


def _sources():
    for path in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _first_text(node) -> str | None:
    """The leading literal text of a str or f-string argument."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        head = node.values[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str):
            return head.value
    return None


def _name_of(node) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _command_names() -> list[str]:
    parser = build_parser()
    for action in parser._subparsers._group_actions:  # noqa: SLF001, argparse keeps them here
        return sorted(action.choices)
    return []


def _option_strings() -> list[str]:
    """Every option of the top-level parser and of each subcommand, without -h and --help."""
    parser = build_parser()
    parsers = [parser]
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        parsers.extend(action.choices.values())
    options = set()
    for sub in parsers:
        for action in sub._actions:  # noqa: SLF001
            options.update(o for o in action.option_strings if o not in ("-h", "--help"))
    return sorted(options)


def _site_sources() -> list[Path]:
    """Tracked text that ends up in a help site: the help pages and the apphelp theme.

    The theme README is contributor documentation; it is not deployed and may name the framework.
    """
    files = sorted(HELP_SOURCE.glob("*.md"))
    files += sorted(p for p in APPHELP.rglob("*") if p.is_file() and p.name != "README.md"
                    and p.suffix in {".md", ".tpl", ".js", ".css", ".html", ".json"})
    return files


def _theme_names() -> list[str]:
    return sorted(p.name for p in THEMES.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def _repo_json_keys() -> list[str]:
    """Top-level repo.json keys the code reads.

    Sources: repo.get("key"), repo["key"] and get_value("repo", "key") anywhere in kb4it/,
    plus the key lists the code validates or hashes (see REPO_KEY_LISTS).
    """
    keys = set()
    for _path, tree in _sources():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.args:
                first = node.args[0]
                if node.func.attr == "get" and _name_of(node.func.value) in REPO_NAMES:
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        keys.add(first.value)
                elif node.func.attr == "get_value" and len(node.args) >= 2:
                    second = node.args[1]
                    if (isinstance(first, ast.Constant) and first.value == "repo"
                            and isinstance(second, ast.Constant) and isinstance(second.value, str)):
                        keys.add(second.value)
            elif isinstance(node, ast.Assign) and any(_name_of(t) in REPO_KEY_LISTS for t in node.targets):
                keys.update(c.value for c in ast.walk(node.value)
                            if isinstance(c, ast.Constant) and isinstance(c.value, str))
            elif isinstance(node, ast.Subscript) and _name_of(node.value) in REPO_NAMES:
                index = node.slice
                if isinstance(index, ast.Constant) and isinstance(index.value, str):
                    keys.add(index.value)
    return sorted(keys)


def _error_codes() -> list[str]:
    """Codes of the log tags a user can meet, and the codes the apphelp checks report."""
    codes = set()
    for _path, tree in _sources():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = _name_of(node.func)
            text = _first_text(node.args[0])
            if text is None:
                continue
            if name in USER_LEVELS:
                match = CODE_TAG.match(text)
                if match:
                    codes.add(match.group(1))
            elif name in CODE_CALLS and re.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+", text):
                codes.add(text)
    return sorted(codes)


def _front_matter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    pairs = (line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def test_the_lists_are_not_empty():
    """Guard: an empty list would make every coverage test pass."""
    assert _command_names()
    assert _theme_names()
    assert _repo_json_keys()
    assert _error_codes()
    assert _option_strings()
    assert _site_sources()


def test_every_command_has_a_page_mention():
    text = "\n".join(_pages().values())
    missing = [name for name in _command_names() if f"kb4it {name}" not in text]
    assert not missing, f"commands with no page: {missing}"


def test_every_command_option_has_a_page_mention():
    text = "\n".join(_pages().values())
    missing = [opt for opt in _option_strings() if not re.search(rf"(?<![\w-]){re.escape(opt)}(?![\w-])", text)]
    assert not missing, f"options with no page: {missing}"


def test_every_bundled_theme_has_a_reference_page():
    missing = [name for name in _theme_names() if not (HELP_SOURCE / f"reference-theme-{name}.md").exists()]
    assert not missing, f"themes with no reference page: {missing}"


def test_every_repo_json_key_is_documented():
    page = (HELP_SOURCE / "reference-repo-json.md").read_text(encoding="utf-8")
    missing = [key for key in _repo_json_keys() if f"`{key}`" not in page]
    assert not missing, f"repo.json keys not in reference-repo-json.md: {missing}"


def test_every_logged_error_code_is_documented():
    pages = _pages()
    text = "\n".join(body for name, body in pages.items()
                     if name == "troubleshooting.md" or name.startswith("reference-"))
    missing = [code for code in _error_codes() if not re.search(rf"\b{code}\b", text)]
    assert not missing, f"error codes not in troubleshooting.md or reference-*.md: {missing}"


@pytest.mark.skip(reason="Task 8: section mapping")
def test_section_names_only():
    wrong = {name: _front_matter(body).get("Section") for name, body in _pages().items()
             if _front_matter(body).get("Section") not in SECTIONS}
    assert not wrong, f"pages with a section outside {SECTIONS}: {wrong}"


def test_no_framework_name_in_the_sources():
    found = [str(p.relative_to(ROOT)) for p in _site_sources()
             if FRAMEWORK_NAME in p.read_text(encoding="utf-8", errors="replace").lower()]
    assert not found, f"files that name the framework: {found}"


def test_no_framework_name_in_the_site():
    if not (OFFLINE / "index.html").exists():
        pytest.skip("offline help copy not built")
    found = [str(p.relative_to(OFFLINE)) for p in sorted(OFFLINE.rglob("*"))
             if p.is_file() and p.suffix in {".html", ".js", ".json", ".txt", ".xml", ".md"}
             and FRAMEWORK_NAME in p.read_text(encoding="utf-8", errors="replace").lower()]
    assert not found, f"files that name the framework: {found}"
