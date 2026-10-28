"""
Structured data: the repo.json "seo" block and the JSON-LD graph of a page (schema.org).

# File: structured.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from kb4it.core.dates import guess_datetime
from kb4it.core.exceptions import ConfigError

SEO_KEYS = ("structured_data", "lang", "map", "index", "noindex_keys")
LANG_RE = re.compile(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*")
PROPERTY_RE = re.compile(r"[a-z][A-Za-z]*")
TYPE_RE = re.compile(r"[A-Z][A-Za-z]*")

# Keys KB4IT itself turns into the page node; a mapping may not name them.
CORE_KEYS = frozenset({"Title", "Summary", "Date", "Modified", "DocType", "SystemPage", "Bookmark"})
# Properties KB4IT fills; a mapping may not write them.
CORE_PROPERTIES = frozenset({"headline", "name", "description", "url", "inLanguage", "datePublished",
                             "dateModified", "mainEntityOfPage"})

# Frontmatter key -> "property" or "property:Type"; None leaves the key out.
DEFAULT_MAP: dict[str, str | None] = {
    "Author": "author:Person",
    "Tag": "keywords",
    "Topic": "about:Thing",
    "Category": "genre",
    "WorkType": "genre",
    "Scope": "audience:Audience",
    "Product": "mentions:SoftwareApplication",
    "OS": "mentions:SoftwareApplication",
    "Database": "mentions:SoftwareApplication",
    "Protocol": "mentions:DefinedTerm",
    "Project": "isPartOf:CreativeWorkSeries",
    "Status": "creativeWorkStatus",
}

# DocType (Diátaxis) -> schema.org type of the page.
DOCTYPE_TYPES: dict[str, str | list[str]] = {
    "How-to guide": ["TechArticle", "HowTo"],
    "Tutorial": ["TechArticle", "LearningResource"],
    "Reference": "TechArticle",
    "Explanation": "Article",
}


@dataclass(frozen=True)
class SeoSettings:
    """The repo.json "seo" block, checked."""

    structured_data: bool = True
    lang: str = ""
    map: dict[str, str | None] = field(default_factory=dict)
    # True or False: the site may or may not be indexed; None: the owner has not decided yet.
    index: bool | None = None
    # Listing pages (property, value, event, stats pages) carry "noindex, follow".
    noindex_keys: bool = True


def load_seo(repo: Mapping[str, Any]) -> SeoSettings:
    """SeoSettings from repo.json; ConfigError names the first bad entry."""
    block = repo.get("seo")
    if block is None:
        return SeoSettings()
    if not isinstance(block, dict):
        raise ConfigError("repo.json 'seo' must be an object such as {\"lang\": \"en\"}")
    unknown = sorted(set(block) - set(SEO_KEYS))
    if unknown:
        raise ConfigError(f"repo.json 'seo' has unknown key {unknown[0]!r}; known keys: {', '.join(SEO_KEYS)}")
    enabled = block.get("structured_data", True)
    if not isinstance(enabled, bool):
        raise ConfigError("repo.json 'seo.structured_data' must be true or false")
    lang = block.get("lang", "")
    if not isinstance(lang, str) or (lang and not LANG_RE.fullmatch(lang)):
        raise ConfigError(f"repo.json 'seo.lang' must be a language tag such as \"en\" or \"es-ES\", not {lang!r}")
    raw_map = block.get("map", {})
    if not isinstance(raw_map, dict):
        raise ConfigError("repo.json 'seo.map' must be an object of frontmatter key -> schema.org property")
    mapping: dict[str, str | None] = {}
    for key, spec in raw_map.items():
        if key in CORE_KEYS:
            raise ConfigError(f"repo.json 'seo.map.{key}': {key} is mapped by KB4IT and cannot be changed")
        if spec is not None:
            check_target(f"seo.map.{key}", spec)
        mapping[str(key)] = spec
    index = block.get("index")
    if index is not None and not isinstance(index, bool):
        raise ConfigError("repo.json 'seo.index' must be true or false")
    noindex_keys = block.get("noindex_keys", True)
    if not isinstance(noindex_keys, bool):
        raise ConfigError("repo.json 'seo.noindex_keys' must be true or false")
    return SeoSettings(structured_data=enabled, lang=lang, map=mapping, index=index, noindex_keys=noindex_keys)


def og_locale(lang: str) -> str:
    """Open Graph locale of a language tag with a region ('es-ES' -> 'es_ES'); empty without a region."""
    language, *subtags = lang.split("-")
    for subtag in subtags:
        if re.fullmatch(r"[A-Za-z]{2}|[0-9]{3}", subtag):
            return f"{language.lower()}_{subtag.upper()}"
    return ""


def check_target(where: str, spec: Any) -> tuple[str, str]:
    """(property, type) of a "property" or "property:Type" mapping; ConfigError when malformed."""
    if not isinstance(spec, str):
        raise ConfigError(f"repo.json '{where}' must be a schema.org property such as \"keywords\" or null")
    prop, _, kind = spec.partition(":")
    if not PROPERTY_RE.fullmatch(prop) or (kind and not TYPE_RE.fullmatch(kind)):
        raise ConfigError(f"repo.json '{where}' must look like \"property\" or \"property:Type\", not {spec!r}")
    if prop in CORE_PROPERTIES:
        raise ConfigError(f"repo.json '{where}': {prop} is set by KB4IT")
    return prop, kind


def merged_map(*maps: Mapping[str, str | None]) -> dict[str, str | None]:
    """Later maps win; a None entry removes the key."""
    result: dict[str, str | None] = {}
    for mapping in maps:
        result.update(mapping)
    return {key: spec for key, spec in result.items() if spec is not None}


def iso_date(value: str) -> str:
    """'2026-10-23' or '2026-10-23T14:30:00' for a Date value; empty when it does not parse."""
    parsed = guess_datetime(value)
    if parsed is None:
        return ""
    if (parsed.hour, parsed.minute, parsed.second) == (0, 0, 0):
        return parsed.date().isoformat()
    return parsed.isoformat(timespec="seconds")


def _value_node(value: str, kind: str) -> str | dict[str, str]:
    if not kind:
        return value
    if kind == "Audience":
        return {"@type": kind, "audienceType": value}
    return {"@type": kind, "name": value}


def _single(items: list[Any]) -> Any:
    return items[0] if len(items) == 1 else items


def page_type(doctype: str, default: str | list[str]) -> str | list[str]:
    """schema.org type of a page from its DocType, else the theme's default."""
    return DOCTYPE_TYPES.get(doctype, default)


def document_node(*, title: str, description: str, values: Mapping[str, Sequence[str]],
                  mapping: Mapping[str, str], default_type: str | list[str], lang: str,
                  url: str = "", website_id: str = "", modified: str = "") -> dict[str, Any]:
    """The page node of a document: core properties, then every mapped frontmatter key."""
    doctype = next(iter(values.get("DocType") or []), "")
    node: dict[str, Any] = {"@type": page_type(doctype, default_type)}
    if url:
        node["@id"] = f"{url}#article"
        node["url"] = url
        node["mainEntityOfPage"] = url
    node["headline"] = title
    node["name"] = title
    if description:
        node["description"] = description
    if lang:
        node["inLanguage"] = lang
    published = iso_date(next(iter(values.get("Date") or []), ""))
    if published:
        node["datePublished"] = published
    if modified:
        node["dateModified"] = modified
    if doctype:
        node["learningResourceType"] = doctype
    props: dict[str, list[Any]] = {}
    for key, spec in mapping.items():
        prop, _, kind = spec.partition(":")
        for value in values.get(key) or []:
            item = _value_node(value, kind)
            bucket = props.setdefault(prop, [])
            if item not in bucket:
                bucket.append(item)
    if website_id:
        props.setdefault("isPartOf", []).append({"@id": website_id})
    for prop, items in props.items():
        if prop == "keywords":
            node[prop] = ", ".join(str(item) for item in items)
        else:
            node[prop] = _single(items)
    return node


def website_node(*, name: str, description: str, lang: str, url: str = "", search_url: str = "") -> dict[str, Any]:
    """The WebSite node of the home page, with a SearchAction when the site has a search page."""
    node: dict[str, Any] = {"@type": "WebSite"}
    if url:
        node["@id"] = f"{url}#website"
        node["url"] = url
    node["name"] = name
    if description:
        node["description"] = description
    if lang:
        node["inLanguage"] = lang
    if search_url:
        node["potentialAction"] = {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": f"{search_url}?q={{search_term_string}}"},
            "query-input": "required name=search_term_string",
        }
    return node


def graph(nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """A JSON-LD document holding the nodes of one page."""
    return {"@context": "https://schema.org", "@graph": list(nodes)}


def render_jsonld(data: Mapping[str, Any]) -> str:
    """JSON safe to print inside <script type="application/ld+json">."""
    text = json.dumps(data, ensure_ascii=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
