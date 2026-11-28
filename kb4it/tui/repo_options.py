"""
The repo.json settings a theme reads, taken from the help pages that ship with KB4IT.

The help pages are the reference for every setting: reference-repo-json.html for the
common ones and reference-theme-<theme>.html for each bundled theme. Reading their
tables keeps the TUI and the help in step, with no second list to maintain.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

# Sections of reference-repo-json.html that describe repo.json keys.
_COMMON_SECTIONS = ("required", "optional", "markdown", "people", "dates", "seo", "feed")
# A code sample right before a table names the block its keys live in: "seo": {...
_BLOCK = re.compile(r'^\s*"([A-Za-z_]+)"\s*:\s*\{')


@dataclass(frozen=True)
class RepoOption:
    key: str  # a top-level key, or a dotted path inside a block, such as seo.index
    default: str
    meaning: str
    group: str  # where it comes from: Common or the theme name
    values: str = ""  # the values the key accepts, from the Values column


def help_dir() -> Path:
    return Path(str(resources.files("kb4it").joinpath("resources", "help")))


def source_help_dir() -> Path:
    """help/source of a source checkout; the package has no such folder."""
    return Path(__file__).resolve().parents[2] / "help" / "source"


def _page(name: str, folder: Path | None):
    """The parsed help page: the built one when present, else its Markdown source rendered."""
    from lxml import html

    built = (folder or help_dir()) / f"{name}.html"
    if built.exists():
        return html.parse(str(built))
    if folder is not None:
        return None
    source = source_help_dir() / f"{name}.md"
    if not source.exists():
        return None
    import markdown

    text = source.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("\n---", 1)[1].split("\n", 1)[1]  # drop the frontmatter
    body = markdown.markdown(text, extensions=["tables", "attr_list", "fenced_code"])
    return html.document_fromstring(f"<html><body>{body}</body></html>").getroottree()


def _text(element) -> str:
    return " ".join(element.text_content().split())


def _block_of(table) -> str:
    """The block name of the code sample just before the table, or '' for top-level keys."""
    previous = table.getprevious()
    if previous is None:
        return ""
    sample = previous.text_content().strip()
    sample = sample.removeprefix("Copy")
    match = _BLOCK.match(sample)
    return match.group(1) if match else ""


def _keys(cell: str) -> list[str]:
    """Key names of a Key cell; one cell may list several, such as `logo`, `logo_alt`."""
    return [key.strip() for key in cell.split(",") if key.strip()]


def _read_tables(tree, sections: tuple[str, ...], group: str) -> list[RepoOption]:
    options: list[RepoOption] = []
    section = None
    for element in tree.iter("h2", "table"):
        if element.tag == "h2":
            section = element.get("id")
            continue
        heads = [_text(th) for th in element.iter("th")]
        if section not in sections or not heads or heads[0] not in ("Key", "Setting") or heads[-1] != "Meaning":
            continue
        previous = element.getprevious()
        if previous is not None and "theme.json" in _text(previous):
            continue  # keys of the theme's theme.json, not of repo.json
        block = _block_of(element)
        if block in ("profiles", "dates"):
            block = f"{block}.<Property>"
        for row in element.iter("tr"):
            cells = [_text(td) for td in row.findall("td")]
            if not cells:
                continue
            default = cells[heads.index("Default")] if "Default" in heads else ""
            values = cells[heads.index("Values")] if "Values" in heads else ""
            # A row may say its key sits at the top level even inside a block's table (apphelp editor).
            prefix = "" if cells[-1].startswith("Top-level key") else block
            for key in _keys(cells[0]):
                options.append(RepoOption(f"{prefix}.{key}" if prefix else key, default, cells[-1], group, values))
    return options


def theme_options(theme: str, folder: Path | None = None) -> tuple[list[RepoOption], bool]:
    """Common settings plus the theme's own; the flag is False when the theme has no help page.

    folder holds built help pages; by default the package's, or help/source when they are not built.
    """
    common = _page("reference-repo-json", folder)
    options = _read_tables(common, _COMMON_SECTIONS, "Common") if common is not None else []
    page = _page(f"reference-theme-{theme}", folder) if theme else None
    if page is None:
        return options, False
    own = _read_tables(page, ("settings",), theme)
    mine = {option.key for option in own}
    # The theme's row of a key says more than the common one (its default, its format).
    return [option for option in options if option.key not in mine] + own, True


def current_value(repo: dict, key: str) -> str | None:
    """The value a project sets for a key (dotted for blocks), as one line of JSON; None when unset."""
    node = repo
    for part in key.split("."):
        if part == "<Property>":
            return None
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return json.dumps(node, ensure_ascii=False)
