"""AppHelp page metadata: parse frontmatter keys into Page objects and validate them."""

import re
from dataclasses import dataclass, field

from kb4it.core.util import html_id_for, slugify

# Type of document: the frontmatter value and the short name used in CSS classes, URLs and labels.
DOCTYPES = {"Tutorial": "tutorial", "How-to guide": "howto", "Reference": "reference", "Explanation": "explanation"}
LAYOUTS = ("faq", "tips", "troubleshooting")
REQUIRED = ("Section", "Order", "Summary", "Feature")
VOCABULARY_KEYS = ("Feature", "Level", "Platform")
SUMMARY_MAX = 160
LANDING = "index.md"
RESERVED = ("search.md", "topics.md", "go.md", "404.md")
HELPID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ORDER_RE = re.compile(r"^-?\d+$")


@dataclass
class Page:
    doc_id: str
    title: str
    doctype: str
    section: str
    order: int
    summary: str
    features: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    level: str = ""
    platforms: list = field(default_factory=list)
    since: str = ""
    plugin: str = ""
    helpids: list = field(default_factory=list)
    related: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    date: str = ""
    layout: str = ""

    @property
    def url(self) -> str:
        return html_id_for(self.doc_id)


@dataclass(frozen=True)
class Problem:
    code: str
    doc: str
    detail: str

    def __str__(self):
        return f"{self.code} doc={self.doc} {self.detail}".rstrip()


def _first(keys, name, default=""):
    values = keys.get(name) or []
    return values[0] if values else default


def _has_value(keys, name):
    return any(str(v).strip() for v in keys.get(name) or [])


def _joined(keys, name):
    # The frontmatter parser splits strings on commas; free text is joined back.
    return ", ".join(keys.get(name) or [])


def parse_helpid(value: str) -> tuple:
    """Split 'id' or 'id=#anchor' into (id, anchor)."""
    ident, _, anchor = value.partition("=")
    return ident.strip(), anchor.strip().lstrip("#")


def is_content(doc_id: str, keys: dict) -> bool:
    """True for pages that take part in navigation: not system pages and not the landing page."""
    return doc_id != LANDING and "SystemPage" not in keys


def doctype_of(keys: dict) -> str:
    """Short name of the page's type of document, or "" when it is missing, repeated or not one of the four."""
    values = [v for v in keys.get("DocType") or [] if str(v).strip()]
    return DOCTYPES.get(values[0], "") if len(values) == 1 else ""


def is_classified(keys: dict) -> bool:
    return bool(doctype_of(keys))


def feature_anchor(name: str) -> str:
    return "feature-" + (slugify(name) or "other")


def page_from_keys(doc_id: str, keys: dict) -> Page:
    order = _first(keys, "Order", "9999")
    return Page(
        doc_id=doc_id,
        title=_first(keys, "Title", doc_id),
        doctype=doctype_of(keys),
        section=_joined(keys, "Section"),
        order=int(order) if ORDER_RE.match(order) else 9999,
        summary=_joined(keys, "Summary"),
        features=list(keys.get("Feature") or []),
        keywords=list(keys.get("Keyword") or []),
        level=_first(keys, "Level"),
        platforms=list(keys.get("Platform") or []),
        since=_first(keys, "Since"),
        plugin=_first(keys, "Plugin"),
        helpids=[parse_helpid(v) for v in keys.get("HelpId") or []],
        related=list(keys.get("Related") or []),
        tags=list(keys.get("Tag") or []),
        date=_first(keys, "Date"),
        layout=_first(keys, "Layout"),
    )


def validate_all(docs: dict, config) -> list:
    """Check every content page against the AppHelp rules and return all problems found."""
    problems = []
    vocabulary = config.vocabulary
    if not vocabulary.get("Feature"):
        problems.append(Problem("META_CONFIG", "repo.json", "reason=missing_feature_vocabulary"))
    first_owner = {}
    for doc_id in sorted(docs):
        keys = docs[doc_id]
        if not is_content(doc_id, keys):
            continue
        if doc_id in RESERVED:
            problems.append(Problem("META_INVALID", doc_id, "reason=reserved_name"))
        for name in REQUIRED:
            if not _has_value(keys, name):
                problems.append(Problem("META_MISSING", doc_id, f"key={name}"))
        doctypes = [v for v in keys.get("DocType") or [] if str(v).strip()]
        if not doctypes:
            problems.append(Problem("DOCTYPE_MISSING", doc_id, "key=DocType action=left_out"))
        elif not is_classified(keys):
            problems.append(Problem("DOCTYPE_INVALID", doc_id,
                                    f"key=DocType value={', '.join(doctypes)} allowed={'|'.join(DOCTYPES)} action=left_out"))
        if "Kind" in keys:
            problems.append(Problem("META_INVALID", doc_id, "key=Kind reason=replaced_by_DocType_and_Layout"))
        layout = _first(keys, "Layout")
        if layout and layout not in LAYOUTS:
            problems.append(Problem("META_INVALID", doc_id, f"key=Layout value={layout} allowed={'|'.join(LAYOUTS)}"))
        order = _first(keys, "Order")
        if order and not ORDER_RE.match(order):
            problems.append(Problem("META_INVALID", doc_id, f"key=Order value={order}"))
        if len(_joined(keys, "Summary")) > SUMMARY_MAX:
            problems.append(Problem("META_INVALID", doc_id, f"key=Summary reason=longer_than_{SUMMARY_MAX}"))
        for name in VOCABULARY_KEYS:
            allowed = vocabulary.get(name)
            for value in (keys.get(name) or []) if allowed else []:
                if value not in allowed:
                    problems.append(Problem("META_UNKNOWN", doc_id, f"key={name} value={value}"))
        for value in keys.get("Related") or []:
            if value not in docs:
                problems.append(Problem("META_INVALID", doc_id, f"key=Related value={value} reason=unknown_page"))
        for value in keys.get("HelpId") or []:
            ident, _anchor = parse_helpid(value)
            if not HELPID_RE.match(ident):
                problems.append(Problem("META_INVALID", doc_id, f"key=HelpId value={value}"))
            elif ident in first_owner:
                problems.append(Problem("HELPID_DUPLICATE", doc_id, f"id={ident} first={first_owner[ident]}"))
            else:
                first_owner[ident] = doc_id
    return problems
