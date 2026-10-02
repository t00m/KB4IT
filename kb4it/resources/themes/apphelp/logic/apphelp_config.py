"""AppHelp settings, read from the apphelp block of repo.json."""

import re
from dataclasses import dataclass, field

ACCENT_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
DEFAULT_ACCENT = "#3584e4"

DEFAULT_LABELS = {
    "home": "Home",
    "menu": "Menu",
    "breadcrumb": "Breadcrumb",
    "search": "Search",
    "search_placeholder": "Search help",
    "filters": "Filters",
    "results": "results",
    "no_results": "No pages match your search.",
    "topics": "Topics",
    "topics_intro": "Every page, grouped by feature.",
    "on_this_page": "On this page",
    "previous": "Previous",
    "next": "Next",
    "related": "Related pages",
    "edit": "Edit this page",
    "updated": "Last updated",
    "built_with": "Built with KB4IT",
    "theme_toggle": "Switch colour scheme",
    "skip": "Skip to content",
    "new_in": "New in",
    "plugin": "Plugin",
    "copy": "Copy",
    "copied": "Copied",
    "go_title": "Opening help...",
    "go_unknown": "This help topic does not exist. Try the search or the topics list.",
    "not_found_title": "Page not found",
    "not_found_text": "This page does not exist. Search the help or open the topics list.",
    "ts_cause": "Cause",
    "ts_fix": "Fix",
    "kind_tutorial": "Tutorial",
    "kind_howto": "How-to",
    "kind_reference": "Reference",
    "kind_explanation": "Explanation",
    "kind_faq": "FAQ",
    "kind_tips": "Tips",
    "kind_troubleshooting": "Troubleshooting",
    "facet_Kind": "Type",
    "facet_Feature": "Feature",
    "facet_Level": "Level",
    "facet_Platform": "Platform",
    "facet_Plugin": "Plugin",
    "facet_Since": "Since",
}


@dataclass
class HelpConfig:
    strict: bool = True
    lang: str = "en"
    accent: str = DEFAULT_ACCENT
    about: bool = False
    contract: str = "config/contract.txt"
    contract_explicit: bool = False
    vocabulary: dict = field(default_factory=dict)
    labels: dict = field(default_factory=lambda: dict(DEFAULT_LABELS))
    version: str = ""


def load_config(repo: dict) -> HelpConfig:
    """Build the settings from repo.json; unknown label names are ignored."""
    block = repo.get("apphelp") or {}
    labels = dict(DEFAULT_LABELS)
    for name, text in (block.get("labels") or {}).items():
        if name in labels:
            labels[name] = str(text)
    vocabulary = {str(k): [str(v) for v in values] for k, values in (block.get("vocabulary") or {}).items()}
    accent = str(block.get("accent", DEFAULT_ACCENT))
    return HelpConfig(
        strict=bool(block.get("strict", True)),
        lang=str(block.get("lang", "en")),
        # The accent goes into a <style> tag, so only a plain hex colour is accepted.
        accent=accent if ACCENT_RE.fullmatch(accent) else DEFAULT_ACCENT,
        about=bool(block.get("about", False)),
        contract=str(block.get("contract", "config/contract.txt")),
        contract_explicit="contract" in block,
        vocabulary=vocabulary,
        labels=labels,
        version=str(repo.get("version") or ""),
    )
