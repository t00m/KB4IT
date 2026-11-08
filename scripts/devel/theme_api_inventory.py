#!/usr/bin/env python3
"""Inventory of what the bundled themes and starters use from KB4IT (input of the theme API work).

Usage: theme_api_inventory.py [REPO_ROOT] [--json OUT]    (REPO_ROOT defaults to this checkout)

For each theme it imports logic/theme.py under a unique module name, walks the MRO of Theme and
scans the theme's Python files and templates with ast and regexes. It prints Markdown sections:
MRO size, hooks overridden, KB4IT methods called, class attributes set, srvdtb/srvbes calls,
kb4it imports, template variables read, override chains, and cross-class instance state.
"""

import ast
import importlib.util
import inspect
import json
import re
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

_ARGS = [a for a in sys.argv[1:] if a != "--json" and (sys.argv.index(a) < 2 or sys.argv[sys.argv.index(a) - 1] != "--json")]
ROOT = Path(_ARGS[0]).resolve() if _ARGS else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

THEMES = {
    "techdoc": ROOT / "kb4it/resources/themes/techdoc",
    "blog": ROOT / "kb4it/resources/themes/blog",
    "bookshelf": ROOT / "kb4it/resources/themes/bookshelf",
    "apphelp": ROOT / "kb4it/resources/themes/apphelp",
    "starter-docs": ROOT / "kb4it/resources/starters/starter-docs",
    "starter-plain": ROOT / "kb4it/resources/starters/starter-plain",
}
SERVICE_ATTRS = ("srvdtb", "srvbes")
# Parameter names of theme helper functions that receive the database.
DB_NAMES = {"srvdtb", "db"}


def load_theme(name, folder):
    """Import logic/theme.py with logic/ on sys.path, as Frontend does, under a unique name."""
    logic = str(folder / "logic")
    before = set(sys.modules)
    sys.path.insert(0, logic)
    try:
        spec = importlib.util.spec_from_file_location(f"kb4it_inventory_{name.replace('-', '_')}", folder / "logic/theme.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # inspect.getsource() finds the classes through sys.modules
        spec.loader.exec_module(module)
        return module.Theme
    finally:
        sys.path.remove(logic)  # helper modules carry the theme prefix, so they stay loaded without clashing


def is_core(cls):
    return cls.__module__.startswith("kb4it.") or cls is object


def defined_in(theme_cls, attr):
    return [c for c in theme_cls.__mro__ if attr in c.__dict__]


def core_names(theme_cls):
    """Every name a KB4IT class of the MRO defines, mapped to the first KB4IT class defining it."""
    names = {}
    for cls in theme_cls.__mro__:
        if is_core(cls) and cls is not object:
            for attr in cls.__dict__:
                if attr.startswith("__"):
                    continue
                names.setdefault(attr, cls.__name__)
    return names


def py_files(folder):
    return sorted((folder / "logic").glob("*.py"))


def attr_chain(node):
    """['self', 'srvdtb', 'get_values'] for self.srvdtb.get_values."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "super":
        parts.append("super()")
    else:
        return None
    return list(reversed(parts))


def scan_python(folder, core):
    """What the theme's Python code uses from KB4IT."""
    uses = defaultdict(set)  # category -> {name}
    where = defaultdict(set)  # name -> {file}
    for path in py_files(folder):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("kb4it"):
                for alias in node.names:
                    uses["imports"].add(f"{node.module}.{alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("kb4it"):
                        uses["imports"].add(alias.name)
            elif isinstance(node, ast.Attribute):
                chain = attr_chain(node)
                if not chain:
                    continue
                if len(chain) >= 3 and chain[0] in ("self", "host") and chain[1] in SERVICE_ATTRS:
                    uses[chain[1]].add(chain[2])
                    where[f"{chain[1]}.{chain[2]}"].add(path.name)
                elif len(chain) >= 2 and chain[0] in DB_NAMES:
                    uses["srvdtb"].add(chain[1])
                    where[f"srvdtb.{chain[1]}"].add(path.name)
                elif len(chain) == 2 and chain[0] in ("self", "super()") and chain[1] in core:
                    uses["self"].add(chain[1])
                    where[chain[1]].add(path.name)
            elif isinstance(node, ast.Subscript):
                # self.__dict__['_x'] and getattr(self, 'x') style reads of state
                pass
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("getattr", "hasattr"):
                if len(node.args) >= 2 and isinstance(node.args[0], ast.Name) and node.args[0].id == "self" \
                        and isinstance(node.args[1], ast.Constant) and node.args[1].value in core:
                    uses["self"].add(node.args[1].value)
    return uses, where


VAR_KEY = re.compile(r"""\bvar\s*\[\s*['"]([A-Za-z_][\w-]*)['"]\s*\](?:\s*\[\s*['"]([A-Za-z_][\w-]*)['"]\s*\])?""")
VAR_GET = re.compile(r"""\bvar\.get\(\s*['"]([A-Za-z_][\w-]*)['"]""")


def provided_var_keys():
    """Top-level keys of var that KB4IT code fills (get_theme_var, build_page, kits), with the filler."""
    provided = {}
    files = list((ROOT / "kb4it/services").glob("*.py")) + list((ROOT / "kb4it/services/themekit").glob("*.py"))
    pat = re.compile(r"""\b(?:var|theme_var)\s*\[\s*['"]([A-Za-z_][\w-]*)['"]\s*\](?:\s*\[\s*['"]([A-Za-z_][\w-]*)['"]\s*\])?\s*=""")
    for path in files:
        for match in pat.finditer(path.read_text(encoding="utf-8")):
            key = match.group(1) if not match.group(2) else f"{match.group(1)}.{match.group(2)}"
            provided.setdefault(key, set()).add(path.stem)
    return provided


def template_dirs(folder):
    theme = json.loads((folder / "theme.json").read_text(encoding="utf-8"))
    dirs = [("theme", folder / "templates")]
    if theme.get("template_base"):
        dirs.append((f"base:{theme['template_base']}", ROOT / "kb4it/resources/bases" / theme["template_base"] / "templates"))
    return dirs


def scan_templates(folder, provided):
    found = defaultdict(set)  # key -> {origin}
    for origin, tdir in template_dirs(folder):
        for tpl in sorted(tdir.glob("*.tpl")):
            text = tpl.read_text(encoding="utf-8")
            for match in VAR_KEY.finditer(text):
                top, sub = match.group(1), match.group(2)
                key = f"{top}.{sub}" if sub and f"{top}.{sub}" in provided else top
                if key in provided or top in provided:
                    found[key].add(origin)
            for match in VAR_GET.finditer(text):
                if match.group(1) in provided:
                    found[match.group(1)].add(origin)
    return found


def class_state(cls):
    """(writes, reads) of self attributes in the methods a class defines itself."""
    writes, reads = defaultdict(set), defaultdict(set)
    try:
        source = textwrap.dedent(inspect.getsource(cls))
    except (OSError, TypeError):
        return writes, reads
    tree = ast.parse(source)
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(func):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
                (writes if isinstance(node.ctx, ast.Store) else reads)[node.attr].add(func.name)
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) \
                    and node.value.attr == "__dict__" and isinstance(node.slice, ast.Constant):
                bucket = writes if isinstance(node.ctx, ast.Store) else reads
                bucket[node.slice.value].add(func.name)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "__dict__" \
                    and node.func.attr in ("get", "setdefault", "pop") and node.args \
                    and isinstance(node.args[0], ast.Constant):
                bucket = reads if node.func.attr == "get" else writes
                bucket[node.args[0].value].add(func.name)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("getattr", "hasattr", "setattr") \
                    and len(node.args) >= 2 and isinstance(node.args[0], ast.Name) and node.args[0].id == "self" \
                    and isinstance(node.args[1], ast.Constant):
                (writes if node.func.id == "setattr" else reads)[node.args[1].value].add(func.name)
    return writes, reads


def shared_state(theme_cls):
    """Instance attributes (not methods) written in one class of the MRO and read in another."""
    writes, reads = defaultdict(set), defaultdict(set)
    for cls in theme_cls.__mro__:
        if cls is object:
            continue
        w, r = class_state(cls)
        for attr, funcs in w.items():
            writes[attr].update(f"{cls.__name__}.{f}" for f in funcs)
        for attr, funcs in r.items():
            reads[attr].update(f"{cls.__name__}.{f}" for f in funcs)
    rows = []
    for attr in sorted(writes):
        if callable(getattr(theme_cls, attr, None)) and not isinstance(getattr(theme_cls, attr, None), type):
            continue
        writer_classes = {w.split(".")[0] for w in writes[attr]}
        reader_classes = {r.split(".")[0] for r in reads.get(attr, ())}
        if reader_classes - writer_classes:
            rows.append((attr, sorted(writes[attr]), sorted(reads.get(attr, ()))))
    return rows


def main():
    provided = provided_var_keys()
    report = {}
    for name, folder in THEMES.items():
        theme_cls = load_theme(name, folder)
        core = core_names(theme_cls)
        mro = theme_cls.__mro__
        attrs = [a for a in dir(theme_cls) if not a.startswith("__")]
        theme_classes = [c for c in mro if not is_core(c)]
        overridden = sorted(a for c in theme_classes for a in c.__dict__ if a in core and not a.startswith("__"))
        multi = sorted((a, [c.__name__ for c in defined_in(theme_cls, a)]) for a in attrs
                       if len(defined_in(theme_cls, a)) > 1 and callable(getattr(theme_cls, a, None)))
        uses, where = scan_python(folder, core)
        hooks = [a for a in overridden if callable(core and getattr(theme_cls, a, None))]
        settings = [a for a in overridden if not callable(getattr(theme_cls, a, None))]
        called = sorted(uses["self"] - set(overridden) - set(SERVICE_ATTRS))
        report[name] = {
            "base": [c.__name__ for c in theme_cls.__bases__],
            "mro_len": len(mro),
            "mro": [f"{c.__module__}.{c.__name__}" for c in mro],
            "attrs": len(attrs),
            "hooks_overridden": [(h, core[h]) for h in hooks],
            "class_settings": [(s, core[s], repr(getattr(theme_cls, s))) for s in settings],
            "core_calls": [(c, core.get(c, "?")) for c in called],
            "srvdtb": sorted(uses["srvdtb"]),
            "srvbes": sorted(uses["srvbes"]),
            "imports": sorted(uses["imports"]),
            "template_vars": {k: sorted(v) for k, v in sorted(scan_templates(folder, provided).items())},
            "override_chains": multi,
            "shared_state": shared_state(theme_cls),
        }
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if out:
        Path(out).write_text(json.dumps(report, indent=1, default=list), encoding="utf-8")
    print(json.dumps({"provided_var_keys": {k: sorted(v) for k, v in sorted(provided.items())}}, indent=1))
    for name, r in report.items():
        print(f"\n## {name}: bases {r['base']}, MRO {r['mro_len']} classes, {r['attrs']} attributes")
        for key in ("hooks_overridden", "class_settings", "core_calls", "srvdtb", "srvbes", "imports"):
            print(f"- {key} ({len(r[key])}): {r[key]}")
        print(f"- template_vars ({len(r['template_vars'])}): {r['template_vars']}")
        print(f"- override_chains ({len(r['override_chains'])}):")
        for a, classes in r["override_chains"]:
            print(f"    {a}: {' -> '.join(classes)}")
        print(f"- shared_state ({len(r['shared_state'])}):")
        for attr, w, rd in r["shared_state"]:
            print(f"    {attr}: written {w} read {rd}")


if __name__ == "__main__":
    main()
