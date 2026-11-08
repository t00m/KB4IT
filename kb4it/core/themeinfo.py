#!/usr/bin/env python

"""
kb4it theme-info: what a theme is made of, without building a site.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

It loads the theme's Theme class (logic/ as a package, kb4it/core/themeload.py) and
prints its API, its features, the hooks it overrides, the options it sets, where
each template comes from and its settings class. With --repo the templates also
resolve the repository's overrides and the settings show the merged values.
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import os
import sys

from kb4it.core.env import ENV
from kb4it.core.exceptions import ThemeError
from kb4it.core.paths import resolve_repo_path
from kb4it.core.themeload import is_theme_module, load_module

# Legacy API: the KB4IT class a theme inherits from, and the feature of the new API it stands for.
LEGACY_FEATURES = {
    "DocumentPageMixin": "document_page",
    "TocMixin": "toc",
    "MetadataMixin": "metadata",
    "KeyPagesMixin": "property_pages",
    "TableMixin": "table",
    "StatsMixin": "stats",
    "EventsMixin": "events",
    "NotFoundMixin": "not_found",
    "FilterMixin": "table_filter",
    "RelatedMixin": "related",
    "NavigationMixin": "navigation",
    "TocSidebarMixin": "toc_sidebar",
    "GalleryMixin": "gallery",
    "DiagramsMixin": "diagrams",
    "AddPageMixin": "editor",
    "IndexingMixin": "search",
}
# Classes of the base every theme has: their methods are hooks of the base, not of a feature.
BASE_CLASSES = ("Builder", "PagePipelineMixin", "HeadMetaMixin", "ProfileCardMixin", "Service")
LEGACY_BASES = ("DocumentTheme", "Builder")


def find_theme(name: str, repo_config: str | None = None) -> tuple[str, str, dict]:
    """(folder, origin, repo settings) of a theme given by id or folder, or ThemeError.

    With repo_config, an empty name means the repository's theme, and its theme_path wins.
    """
    repo = {}
    root = None
    if repo_config:
        with open(repo_config, encoding="utf-8") as fh:
            repo = json.load(fh)
        root = os.path.dirname(os.path.dirname(os.path.abspath(repo_config)))
        name = name or repo.get("theme", "")
        if repo.get("theme_path"):
            folder = resolve_repo_path(repo["theme_path"], root)
            if os.path.isfile(os.path.join(folder, "theme.json")):
                return folder, "theme_path", repo
    if name and os.path.isfile(os.path.join(name, "theme.json")):
        return os.path.abspath(name), "path", repo
    for origin, parent in (("user", ENV["LPATH"]["THEMES"]), ("builtin", ENV["GPATH"]["THEMES"])):
        folder = os.path.join(parent, name or "")
        if name and os.path.isfile(os.path.join(folder, "theme.json")):
            return folder, origin, repo
    raise ThemeError(f"theme not found: {name or '(none given)'}")


def _kb4it_class(cls) -> bool:
    return cls.__module__.startswith("kb4it.")


def _theme_class(cls) -> bool:
    return is_theme_module(cls.__module__)


def _where(obj, folder: str) -> str:
    """logic/file.py:line of a function or class, relative to the theme folder."""
    try:
        path = inspect.getsourcefile(obj)
        line = inspect.getsourcelines(obj)[1]
    except (OSError, TypeError):
        return "?"
    return f"{os.path.relpath(path, folder)}:{line}"


def _kb4it_owner(cls, name: str):
    """The KB4IT class of cls's MRO that defines name, or None."""
    for klass in cls.__mro__:
        if _kb4it_class(klass) and name in vars(klass):
            return klass
    return None


def _feature_of(klass) -> str:
    if klass is None or klass.__name__ in BASE_CLASSES:
        return ""
    return LEGACY_FEATURES.get(klass.__name__, klass.__name__)


def legacy_features(cls, theme_json: dict) -> list[str]:
    """The features of a legacy theme: its kit classes, then its theme-local mixins marked (theme)."""
    names, local = [], []
    for klass in reversed(cls.__mro__):
        name = LEGACY_FEATURES.get(klass.__name__)
        if _kb4it_class(klass) and name and name not in ("editor", "search"):
            names.append(name)
        elif _theme_class(klass) and klass is not cls and klass.__name__.endswith("Mixin"):
            local.append(f"{klass.__name__} (theme)")
    if theme_json.get("search") or "search" in (theme_json.get("assets") or []):
        names.append("search")
    if getattr(cls, "add_page", False):
        names.append("editor")
    return names + local


def hooks(cls, folder: str) -> list[dict]:
    """Methods a theme class defines over a KB4IT one, in MRO order."""
    rows, seen = [], set()
    for klass in cls.__mro__:
        if not _theme_class(klass):
            continue
        for name, value in vars(klass).items():
            if name in seen or not callable(value) or inspect.isclass(value) or name.startswith("__"):
                continue
            owner = _kb4it_owner(cls, name)
            if owner is None:
                continue
            seen.add(name)
            rows.append({"hook": name, "class": klass.__name__, "where": _where(value, folder),
                         "feature": _feature_of(owner), "kb4it": f"{owner.__module__}.{owner.__name__}"})
    return sorted(rows, key=lambda r: r["hook"])


def options(cls) -> dict:
    """Class attributes a theme class sets over a KB4IT default."""
    values = {}
    for klass in reversed(cls.__mro__):
        if not _theme_class(klass):
            continue
        for name, value in vars(klass).items():
            if name.startswith("_") or callable(value) or isinstance(value, (classmethod, staticmethod, property)):
                continue
            if _kb4it_owner(cls, name) is not None:
                values[name] = value
    return dict(sorted(values.items()))


def templates(folder: str, theme_json: dict, overrides: str | None, extra=()) -> list[dict]:
    """Every template the theme can render, and the file it comes from (first match wins)."""
    from kb4it.services.builder import REQUIRED_TEMPLATES, template_base_dir
    base = template_base_dir(theme_json)
    sources = []
    if overrides:
        sources.append(("repo", os.path.join(overrides, "templates")))
    sources.append(("theme", os.path.join(folder, "templates")))
    if base:
        sources.append((f"base:{theme_json['template_base']}", base))
    sources.append(("common", ENV["GPATH"]["TEMPLATES"]))
    names = set(REQUIRED_TEMPLATES) | set(extra)
    if theme_json.get("metadata_pages", True) is False:
        names -= {"PAGE_KEY", "PAGE_KEY_VALUE"}
    for _origin, path in sources[:-1]:
        if os.path.isdir(path):
            names.update(f[:-4] for f in os.listdir(path) if f.endswith(".tpl"))
    rows = []
    for name in sorted(names):
        origin, path = "missing", ""
        for where, directory in sources:
            candidate = os.path.join(directory, f"{name}.tpl")
            if os.path.isfile(candidate):
                origin, path = where, candidate
                break
        rows.append({"name": name, "origin": origin, "path": path})
    return rows


def settings(cls, theme_json: dict, repo: dict, theme_id: str) -> dict:
    """The settings class of the theme and its values (merged with repo.json when given)."""
    config_class = getattr(cls, "config_class", None)
    if config_class is None:
        return {"class": None, "values": {}}
    from kb4it.core.themeconfig import build_config
    try:
        config, _unknown = build_config(config_class, theme_json, repo, theme_id)
    except ThemeError as error:
        return {"class": config_class.__name__, "error": str(error), "values": {}}
    values = dataclasses.asdict(config) if dataclasses.is_dataclass(config) else {}
    return {"class": config_class.__name__, "values": values}


def public_api(cls, folder: str) -> dict:
    """features, hooks and options of a theme on kb4it.theme.BaseTheme."""
    from kb4it.services.themeengine import features_of
    from kb4it.theme import BaseTheme
    from kb4it.theme.features import REGISTRY
    classes = features_of(cls)
    owners = {hook: feat.name for feat in classes for hook in feat.hooks}
    option_names = {opt: feat.name for feat in classes for opt in feat.options}
    features = [f.name if REGISTRY.get(f.name) is f else f"{f.name} (theme)" for f in classes]
    rows, values, seen = [], {}, set()
    for klass in cls.__mro__:
        if klass is BaseTheme or klass is object:
            continue
        for attr, value in vars(klass).items():
            if attr in seen or attr.startswith("_"):
                continue
            seen.add(attr)
            if callable(value) and not inspect.isclass(value):
                if hasattr(BaseTheme, attr) or attr in owners:
                    rows.append({"hook": attr, "class": klass.__name__, "where": _where(value, folder),
                                 "feature": owners.get(attr, ""), "kb4it": "kb4it.theme.BaseTheme"})
            elif attr in option_names or (hasattr(BaseTheme, attr) and attr != "features"):
                values[attr] = value
    return {"features": features, "hooks": sorted(rows, key=lambda r: r["hook"]),
            "templates": [t for f in classes for t in f.templates],
            "options": dict(sorted(values.items()))}


def collect(name: str, repo_config: str | None = None) -> dict:
    """Everything theme-info prints, as a dict (the --json output)."""
    folder, origin, repo = find_theme(name, repo_config)
    with open(os.path.join(folder, "theme.json"), encoding="utf-8") as fh:
        theme_json = json.load(fh)
    theme_id = theme_json.get("id") or os.path.basename(folder)
    cls = load_module(os.path.join(folder, "logic"), theme_id).Theme
    legacy = [b.__name__ for b in cls.__mro__ if _kb4it_class(b) and b.__name__ in LEGACY_BASES]
    from kb4it.theme import BaseTheme
    public = public_api(cls, folder) if issubclass(cls, BaseTheme) else None
    if public:
        from kb4it.services.themeengine import theme_json_of
        from kb4it.theme.feature import apply_theme_json
        apply_theme_json(theme_json, theme_json_of(cls), theme_id)
    overrides = None
    if repo_config:
        root = os.path.dirname(os.path.dirname(os.path.abspath(repo_config)))
        overrides = resolve_repo_path(repo.get("overrides", "overrides"), root)
    return {
        "id": theme_id,
        "version": theme_json.get("version"),
        "origin": origin,
        "path": folder,
        "api": "BaseTheme" if public else f"legacy {legacy[0]} (deprecated)" if legacy else "unknown",
        "mro": len(cls.__mro__),
        "features": public["features"] if public else legacy_features(cls, theme_json),
        "hooks": public["hooks"] if public else hooks(cls, folder),
        "options": public["options"] if public else options(cls),
        "templates": templates(folder, theme_json, overrides, public["templates"] if public else ()),
        "settings": settings(cls, theme_json, repo, theme_id),
    }


def render(info: dict) -> str:
    """The text report of collect()."""
    lines = [f"theme      {info['id']} {info['version'] or 'unversioned'} ({info['origin']}) {info['path']}",
             f"api        {info['api']}, {info['mro']} classes in the MRO",
             f"features   {', '.join(info['features']) or 'none'}"]
    width = max([len(h["hook"]) for h in info["hooks"]] + [4])
    for i, hook in enumerate(info["hooks"]):
        label = "hooks" if i == 0 else ""
        feature = f"   (feature {hook['feature']})" if hook["feature"] else ""
        lines.append(f"{label:<10} {hook['hook']:<{width}}  {hook['class']}  {hook['where']}{feature}")
    if not info["hooks"]:
        lines.append("hooks      none")
    opts = " ".join(f"{k}={v!r}" for k, v in info["options"].items())
    lines.append(f"options    {opts or 'none'}")
    width = max([len(t["name"]) for t in info["templates"]] + [4])
    for i, tpl in enumerate(info["templates"]):
        label = "templates" if i == 0 else ""
        root = info["path"] if tpl["origin"] == "theme" else ENV["GPATH"]["RESOURCES"]
        path = tpl["path"] if tpl["origin"] in ("repo", "missing") else os.path.relpath(tpl["path"], root)
        lines.append(f"{label:<10} {tpl['name']:<{width}}  {tpl['origin']:<11} {path}")
    conf = info["settings"]
    if conf["class"] is None:
        lines.append("settings   none (self.config reads theme.json)")
    elif conf.get("error"):
        lines.append(f"settings   {conf['class']}: {conf['error']}")
    else:
        values = ", ".join(f"{k}={v!r}" for k, v in conf["values"].items())
        lines.append(f"settings   {conf['class']}: {values}")
    return "\n".join(lines)


def add_parser(subparsers) -> None:
    """The theme-info subcommand of the kb4it command line."""
    parser = subparsers.add_parser(
        "theme-info", help="Show the features, hooks, options, templates and settings of a theme",
        description="Loads the theme's Theme class without building a site and shows what it is made of.",
        epilog="Examples:\n\n   kb4it theme-info techdoc\n   kb4it theme-info ~/devel/themes/mytheme --json\n"
               "   kb4it theme-info --repo ~/my-site/config/repo.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    from kb4it.core.completion import theme_completer
    parser.add_argument("theme", nargs="?", default="",
                        help="Theme id or folder (default: the theme of --repo)").completer = theme_completer
    parser.add_argument("--repo", metavar="CONFIG", default=None,
                        help="repo.json of a site: templates resolve its overrides, settings its values")
    parser.add_argument("--json", action="store_true", help="Print JSON")


def run_theme_info(params: dict) -> int:
    """CLI: print the report; 1 with the reason when the theme cannot be found or loaded."""
    if not params.get("theme") and not params.get("repo"):
        print("Error: give a theme id or folder, or --repo CONFIG", file=sys.stderr)
        return 1
    try:
        info = collect(params.get("theme", ""), params.get("repo"))
    except (ThemeError, OSError, ValueError, ImportError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(info, indent=2, default=repr) if params.get("json") else render(info))
    return 0
