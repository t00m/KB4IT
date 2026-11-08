#!/usr/bin/env python3
"""Write help/source/reference-theme-hooks.md from the docstrings of Builder, DocumentTheme and the kits.

Usage:
    theme_hooks_doc.py           write the page
    theme_hooks_doc.py --check   exit 1 when the page differs from what it would write
"""

import argparse
import importlib
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kb4it.core.service import Service  # noqa: E402
from kb4it.services.builder import Builder  # noqa: E402
from kb4it.services.pagepipeline import PagePipelineMixin  # noqa: E402
from kb4it.services.themekit import KITS, DocumentTheme  # noqa: E402

PAGE = ROOT / "help" / "source" / "reference-theme-hooks.md"

FRONTMATTER = """---
DocType: Reference
Feature: Themes, Development
HelpId: theme-hooks
Keyword: theme hooks, Builder, DocumentTheme, page pipeline, kit, themekit, override, config_class, checks
Level: advanced
Order: 645
Related: howto-create-theme.md
Section: Reference
Summary: Every hook and helper a theme can fill or call, generated from the docstrings of the KB4IT code.
---
"""

INTRO = """# Theme hooks

A theme is a `Theme` class in `logic/theme.py`. It subclasses `Builder`, or `DocumentTheme` for a theme with
property pages, and adds the kits it wants to its class line. It fills a hook by defining a method with the
same name; a method that replaces a shared one starts its docstring with `Override:`. The tables below come
from the KB4IT source (`scripts/devel/theme_hooks_doc.py`), so they match the installed version.
See [Create your own theme](howto-create-theme.md) for a walk through.
"""

# Builder members that belong to the settings, checks and search section.
SETTINGS = ("config_class", "checks", "run_checks", "search_enabled", "search_index_var", "search_index_warn_bytes",
            "search_documents", "search_record", "search_sections", "write_search_index", "write_index_file")

KIT_TITLES = {
    "DiagramsMixin": ("Diagrams kit", "The Diagrams page: every Mermaid diagram of the documents, with filters."),
    "FilterMixin": ("Table filter kit", "A filter bar over the document tables; needs `DATATABLE_FILTER.tpl` and the "
                    "vendor library `tablefilter`."),
    "GalleryMixin": ("Gallery kit", "The Gallery page: every image of the documents as thumbnails, with filters; "
                     "needs the vendor library `gallery`."),
    "NavigationMixin": ("Navigation kit", "Previous and next page in the reading order the theme gives."),
    "RelatedMixin": ("Related kit", "Related documents: those that share rare property values."),
    "TocSidebarMixin": ("TOC sidebar kit", "A second, sticky table of contents for long documents."),
}


def _summary(obj):
    doc = inspect.getdoc(obj) or ""
    return doc.strip().splitlines()[0].replace("|", "\\|") if doc.strip() else ""


def _signature(func):
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return "()"
    params = [p for name, p in sig.parameters.items() if name != "self"]
    text = str(sig.replace(parameters=params))
    return text.replace("|", "\\|")


def _own_members(cls, base_skip=()):
    """(name, value, defining class) of the public members cls defines itself."""
    for name, value in sorted(vars(cls).items()):
        if name.startswith("_") or name in base_skip:
            continue
        yield name, value, cls


def _rows(members):
    methods, attributes = [], []
    for name, value, owner in members:
        where = f"`{owner.__module__}.{owner.__name__}`"
        if isinstance(value, (staticmethod, classmethod)):
            value = value.__func__
        if inspect.isfunction(value) or isinstance(value, property):
            target = value.fget if isinstance(value, property) else value
            summary = _summary(target)
            if summary:
                sig = "" if isinstance(value, property) else _signature(target)
                methods.append(f"| `{name}{sig}` | {summary} | {where} |")
        elif not callable(value) and not isinstance(value, type):
            shown = repr(value)
            if len(shown) > 60:
                shown = shown[:57] + "..."
            attributes.append(f"| `{name}` | `{shown.replace('|', '/')}` | {where} |")
    return sorted(methods), sorted(attributes)


def _section(title, text, members):
    methods, attributes = _rows(members)
    out = [f"## {title}", "", text, ""]
    if methods:
        out += ["| Method | What it does | Defined in |", "|---|---|---|", *methods, ""]
    if attributes:
        out += ["| Attribute | Default | Defined in |", "|---|---|---|", *attributes, ""]
    return out


def _members_of(classes, only=None, skip=()):
    for cls in classes:
        for name, value, owner in _own_members(cls, skip):
            if only is None or name in only:
                yield name, value, owner


def render():
    builder_classes = [c for c in Builder.__mro__ if c not in (object, Service, PagePipelineMixin)
                       and c.__module__.startswith("kb4it.")]
    document_classes = [c for c in DocumentTheme.__mro__ if c.__module__.startswith("kb4it.services.themekit")
                        and c.__name__ not in ("ThemeHost", "DocumentTheme")]
    lines = [FRONTMATTER, INTRO]
    lines += _section("Page pipeline", "With `page_pipeline = True`, `build_page()` runs these hooks for every "
                      "document page, in this order: `page_var`, `page_toc`, `page_context`, `body_transforms`, "
                      "`page_actions`, `render_page`, `finalize_html`.", _members_of([PagePipelineMixin]))
    lines += _section("Settings, checks and search", "Theme settings (`config_class`), the post-build checks "
                      "and the search index.", _members_of(builder_classes, only=SETTINGS))
    lines += _section("Generated pages and helpers", "What `Builder` offers every theme: pages it can write, "
                      "templates and shared data.", _members_of(builder_classes, skip=SETTINGS))
    lines += _section("DocumentTheme", "What a `DocumentTheme` subclass gets on top of `Builder`: property pages, "
                      "tables, events, the table of contents and the 404 page.", _members_of(document_classes))
    for module, class_name in sorted(KITS.items(), key=lambda item: KIT_TITLES[item[1]][0]):
        kit = getattr(importlib.import_module(module), class_name)
        title, text = KIT_TITLES[class_name]
        lines += _section(title, f"{text} Add `{class_name}` from `{module}` to the class line.", _members_of([kit]))
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the page is out of date")
    args = parser.parse_args()
    text = render()
    if args.check:
        current = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
        if current != text:
            print(f"{PAGE.relative_to(ROOT)} is out of date: run scripts/devel/theme_hooks_doc.py")
            return 1
        return 0
    PAGE.write_text(text, encoding="utf-8")
    print(f"Wrote {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
