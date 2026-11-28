#!/usr/bin/env python3
"""Write the theme API reference pages from the docstrings of the KB4IT code.

help/source/reference-theme-hooks.md: kb4it.theme (BaseTheme, Site, Doc, Table and every built-in feature).
help/source/reference-theme-legacy.md: the deprecated API (Builder, DocumentTheme and the themekit mixins).

Usage:
    theme_hooks_doc.py           write the pages
    theme_hooks_doc.py --check   exit 1 when a page differs from what it would write
"""

import argparse
import importlib
import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kb4it.core.service import Service  # noqa: E402
from kb4it.services.builder import Builder  # noqa: E402
from kb4it.services.pagepipeline import PagePipelineMixin  # noqa: E402
from kb4it.services.themekit import KITS, DocumentTheme  # noqa: E402
from kb4it.theme import BaseTheme, Doc, Feature, Site, Table  # noqa: E402
from kb4it.theme.features import BUNDLES, REGISTRY  # noqa: E402
from kb4it.theme.site import Build, Documents, Paths, People, Properties  # noqa: E402

PAGE = ROOT / "help" / "source" / "reference-theme-hooks.md"
LEGACY_PAGE = ROOT / "help" / "source" / "reference-theme-legacy.md"

FRONTMATTER = """---
DocType: Reference
Feature: Themes, Development
HelpId: theme-hooks
Keyword: theme hooks, kb4it.theme, BaseTheme, Site, Doc, Table, feature, features, options, prepare, build, page_context, config_class, checks
Level: advanced
Order: 645
Related: howto-create-theme.md, dev-theme-internals.md
Section: Reference
Summary: Every hook, option and feature of kb4it.theme, the public theme API, generated from the KB4IT code.
---
"""

INTRO = """# Theme API reference

A theme is a `Theme` class in `logic/theme.py` that subclasses `kb4it.theme.BaseTheme`. It switches on
features by name in `features`, sets their options as class attributes and fills a hook by defining a
method with the same name. The tables below come from the KB4IT source (`scripts/devel/theme_hooks_doc.py`),
so they match the installed version. See [Write a theme](howto-create-theme.md) for a walk through.

`kb4it.theme` exports `BaseTheme`, `Site`, `Doc`, `Table`, `Feature`, `FEATURES`, `Problem`, `ThemeError`,
`page_name`, `slugify` and `q`; `kb4it.theme.html` has the body rewrites `enhance_images`, `enhance_blocks`,
`lazy_images` and `wrap_code`. Anything else is internal.
"""

LEGACY_FRONTMATTER = """---
DocType: Reference
Feature: Themes, Development
HelpId: theme-legacy
Keyword: Builder, DocumentTheme, themekit, kit, mixin, srvdtb, page_pipeline, deprecated, THEME_API_LEGACY
Level: advanced
Order: 646
Related: dev-theme-internals.md, reference-theme-hooks.md
Section: Reference
Summary: The theme API before kb4it.theme (Builder, DocumentTheme and the kits), deprecated, generated from the KB4IT code.
---
"""

LEGACY_INTRO = """# Theme hooks of the legacy API

**Deprecated.** A theme on `Builder` or `DocumentTheme` keeps working, and a theme outside KB4IT that
uses them logs `THEME_API_LEGACY`. New themes use `kb4it.theme`: see [Theme API reference](reference-theme-hooks.md)
and [Theme internals](dev-theme-internals.md), which says what replaces each part.

A legacy theme subclasses `Builder`, or `DocumentTheme` for a theme with property pages, and adds the kits
it wants to its class line. A method that replaces a shared one starts its docstring with `Override:`. The
tables below come from the KB4IT source (`scripts/devel/theme_hooks_doc.py`).
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

# BaseTheme hooks by group, in the order a build calls them.
BASE_GROUPS = [
    ("Lifecycle", "Called once per build, in this order. Every one is optional.",
     ("setup", "generate_sources", "prepare", "build", "after_build", "after_deploy", "checks", "after_checks")),
    ("Document pages", "Called for every page, in this order: `page_var`, `page_context`, `body_transforms`, "
     "`page_template` (through `render_page`), `finalize_html`. `backlinks_html` adds the block after the body.",
     ("page_var", "page_context", "body_transforms", "page_template", "render_page", "finalize_html", "backlinks_html")),
    ("Site-wide", "Values that hold for the whole site.",
     ("site_signature", "target_subdir", "page_lang", "structured_defaults", "search_page")),
    ("Rendering", "Helpers to call from the hooks.", ("render", "template", "has_template", "base_var")),
]
STAGES = ("prepare", "pages", "page_context", "after_build", "after_deploy")


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
    text = re.sub(r"(: |-> )'([^']*)'", r"\1\2", text)  # annotations are strings under `from __future__ import annotations`
    return text.replace("|", "\\|")


def _shown(value):
    shown = repr(value)
    if len(shown) > 60:
        shown = shown[:57] + "..."
    return shown.replace("|", "/")


def _method_rows(cls, names):
    rows = []
    for name in names:
        value = inspect.getattr_static(cls, name)
        target = value.fget if isinstance(value, property) else value
        sig = "" if isinstance(value, property) else _signature(target)
        rows.append(f"| `{name}{sig}` | {_summary(target)} |")
    return rows


def _base_theme():
    out = ["## BaseTheme", "", "The base class of every theme.", "",
           "| Class attribute | Default | Meaning |", "|---|---|---|"]
    source = inspect.getsource(BaseTheme)
    for name in ("features", "config_class", "reserved_pages", "untitled_label", "ellipsize_titles", "log_area",
                 "person_pages"):
        comment, block = "", []
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{name}:"):
                comment = " ".join(block)
                break
            block = block + [stripped[2:].strip()] if stripped.startswith("#:") else []
        out.append(f"| `{name}` | `{_shown(getattr(BaseTheme, name))}` | {comment.replace('|', '/')} |")
    out += ["", "KB4IT sets `self.site` (the [Site](#site)), `self.config` (the settings), `self.log` and "
            "`self.internals` (unstable, see [Theme internals](dev-theme-internals.md)) before the first hook.", ""]
    for title, text, names in BASE_GROUPS:
        out += [f"### {title}", "", text, "", "| Hook | What it does |", "|---|---|", *_method_rows(BaseTheme, names), ""]
    return out


def _public_members(cls):
    names = []
    for name, value in vars(cls).items():
        if name.startswith("_") or name in ("doc_ids",):
            continue
        if inspect.isfunction(value) or isinstance(value, property):
            names.append(name)
    return sorted(names)


def _site():
    out = ["## Site", "", "The knowledge base being built, read-only. `site.page()`, `site.keep()` and `site.table()` "
           "write through KB4IT.", "", "| Member | What it is |", "|---|---|"]
    out += [f"| `site.documents` | {_summary(Documents)} |", f"| `site.properties` | {_summary(Properties)} |",
            f"| `site.people` | {_summary(People)} |", f"| `site.build` | {_summary(Build)} |",
            f"| `site.paths` | {_summary(Paths)} |", "| `site.features` | The enabled features, by name: "
            "`site.features.events`, `site.features['table']` |"]
    out += _method_rows(Site, _public_members(Site))
    for title, cls in (("site.documents", Documents), ("site.properties", Properties), ("site.people", People),
                       ("site.build", Build), ("site.paths", Paths)):
        out += ["", f"### {title}", "", "| Member | What it does |", "|---|---|", *_method_rows(cls, _public_members(cls))]
    out += ["", "## Doc", "", _summary(Doc), "", "| Member | What it does |", "|---|---|",
            "| `id` | The file name in `source/`, such as `note.md` |", *_method_rows(Doc, _public_members(Doc))]
    out += ["", "## Table", "", " ".join(inspect.getdoc(Table).split()), "",
            "Fields: " + ", ".join(f"`{f}`" for f in Table.__dataclass_fields__) + ".", ""]
    return out


def _feature(cls):
    out = [f"### {cls.name}", "", inspect.getdoc(cls).splitlines()[0], ""]
    facts = []
    for label, values in (("Requires", cls.requires), ("Uses", cls.uses), ("Templates", cls.templates),
                          ("Assets", cls.assets), ("Reserves", cls.reserves)):
        if values:
            facts.append(f"- {label}: {', '.join(f'`{v}`' for v in values)}")
    if cls.theme_json:
        facts.append("- Sets in theme.json: " + ", ".join(f"`\"{k}\": {str(v).lower()}`" for k, v in cls.theme_json.items()))
    out += facts + ([""] if facts else [])
    if cls.options:
        out += ["| Option | Default |", "|---|---|", *[f"| `{k}` | `{_shown(v)}` |" for k, v in cls.options.items()], ""]
    if cls.hooks:
        out += ["| Hook | Default |", "|---|---|", *_method_rows(cls, cls.hooks), ""]
    queries = [n for n in _public_members(cls) if n not in cls.hooks and n not in STAGES
               and n not in vars(Feature) and _summary(inspect.getattr_static(cls, n))]
    if queries:
        out += [f"What `site.features.{cls.name}` offers:", "", "| Method | What it does |", "|---|---|",
                *_method_rows(cls, queries), ""]
    return out


def _features():
    out = ["## Features", "", "Switch a feature on by listing its name in `features`; a feature that another one "
           "`requires` comes with it, and a feature runs after the ones it requires or uses. Set an option as a "
           "class attribute of the theme. Fill a hook by defining a method with its name; to call the default from "
           "it, use the feature: `self.site.features.table.datatable_date_cell(doc)`.", "",
           "| Bundle | Features |", "|---|---|"]
    out += [f"| `{name}` | {', '.join(f'`{m}`' for m in members)} |" for name, members in sorted(BUNDLES.items())]
    out.append("")
    for name in sorted(REGISTRY):
        out += _feature(REGISTRY[name])
    return out


def render():
    lines = [FRONTMATTER, INTRO]
    lines += _base_theme()
    lines += _site()
    lines += _features()
    return "\n".join(lines).rstrip() + "\n"


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
            attributes.append(f"| `{name}` | `{_shown(value)}` | {where} |")
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


def render_legacy():
    builder_classes = [c for c in Builder.__mro__ if c not in (object, Service, PagePipelineMixin)
                       and c.__module__.startswith("kb4it.")]
    document_classes = [c for c in DocumentTheme.__mro__ if c.__module__.startswith("kb4it.services.themekit")
                        and c.__name__ not in ("ThemeHost", "DocumentTheme")]
    lines = [LEGACY_FRONTMATTER, LEGACY_INTRO]
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
    parser.add_argument("--check", action="store_true", help="exit 1 when a page is out of date")
    args = parser.parse_args()
    failed = 0
    for page, text in ((PAGE, render()), (LEGACY_PAGE, render_legacy())):
        if args.check:
            current = page.read_text(encoding="utf-8") if page.exists() else ""
            if current != text:
                print(f"{page.relative_to(ROOT)} is out of date: run scripts/devel/theme_hooks_doc.py")
                failed = 1
            continue
        page.write_text(text, encoding="utf-8")
        print(f"Wrote {page.relative_to(ROOT)}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
