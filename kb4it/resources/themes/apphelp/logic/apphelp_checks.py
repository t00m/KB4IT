"""AppHelp build checks: help ids and the contract file. The anchor check is shared (kb4it.core.checks)."""

import json
import os

from kb4it.core.checks import target_exists


def helpid_map(pages) -> dict:
    mapping = {}
    for page in pages:
        for ident, anchor in page.helpids:
            mapping[ident] = page.url + (f"#{anchor}" if anchor else "")
    return dict(sorted(mapping.items()))


def render_helpids_js(mapping) -> str:
    return "window.APPHELP_HELPIDS = " + json.dumps(mapping, ensure_ascii=False, sort_keys=True) + ";\n"


def check_helpids(target_dir, mapping) -> list:
    """Return the help ids whose page or anchor does not exist."""
    cache = {}
    return [ident for ident, url in mapping.items()
            if not target_exists(target_dir, *url.partition("#")[::2], cache)]


def load_contract(path) -> list:
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        lines = [line.strip() for line in fh]
    return [line for line in lines if line and not line.startswith("#")]


def check_contract(entries, mapping, target_dir) -> list:
    """Return contract entries (help ids or page.html#anchor) that the site does not provide."""
    cache, missing = {}, []
    for entry in entries:
        if ".html" in entry:
            page, _, anchor = entry.partition("#")
            if not target_exists(target_dir, page, anchor, cache):
                missing.append(entry)
        elif entry not in mapping:
            missing.append(entry)
    return missing
