#!/usr/bin/env python

"""
The read-only view of a knowledge base that themes get: Site, Doc and Table.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

A theme reads documents, properties and settings through these classes instead
of the Database and Backend services. Nothing returned can change the build:
values come as tuples, settings as read-only mappings over a copy. The only
writers are site.page(), site.keep() and site.table(), which hand the work to
the theme engine.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Iterable, Iterator, Mapping

from kb4it.core.people import person_status, person_tip
from kb4it.core.util import guess_datetime, html_id_for, valid_filename


def _freeze(value: Any) -> Any:
    """A read-only copy of a JSON-like value: dicts become mappings, lists become tuples."""
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return copy.copy(value)


def page_name(key: str, value: str | None = None) -> str:
    """File name of the page of a property (Key.html) or of one of its values (Key_Value.html)."""
    if value is None:
        return f"{valid_filename(key)}.html"
    return f"{valid_filename(key)}_{valid_filename(value)}.html"


class Doc:
    """One document of the knowledge base, read-only."""

    __slots__ = ("_site", "id")

    def __init__(self, site: Site, doc_id: str):
        self._site = site
        self.id = doc_id  # file name in source/, such as 'note.md'

    def __repr__(self) -> str:
        return f"Doc({self.id!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Doc) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def _db(self) -> Any:
        return self._site._db

    @property
    def name(self) -> str:
        """The file name without .md."""
        return self.id[:-3] if self.id.endswith(".md") else self.id

    @property
    def title(self) -> str:
        return self.value("Title")

    @property
    def url(self) -> str:
        """The page of the document, relative to the site root."""
        return html_id_for(self.id)

    @property
    def date(self) -> str | None:
        """The Date property as written, or None."""
        date: str | None = self._db.get_doc_timestamp(self.id)
        return date

    @property
    def datetime(self) -> Any:
        """The Date property as a datetime, or None when missing or unreadable."""
        date = self.date
        return guess_datetime(date) if date else None

    @property
    def is_system(self) -> bool:
        """True for a page KB4IT or the theme generates (property pages, index, about...)."""
        return bool(self._db.is_system(self.id))

    def values(self, key: str) -> tuple[str, ...]:
        """The values of a property, () when the document does not have it."""
        return tuple(v for v in self._db.db.get(self.id, {}).get(key, ()) if v != "")

    def value(self, key: str, default: str = "") -> str:
        """The first value of a property, or default."""
        values = self.values(key)
        return values[0] if values else default

    def keys(self) -> tuple[str, ...]:
        """The properties of the document, sorted, without the ones KB4IT ignores (Title...)."""
        return tuple(self._db.get_custom_keys(self.id))

    @property
    def properties(self) -> Mapping[str, tuple[str, ...]]:
        """Every property of the document and its values."""
        return MappingProxyType({key: self.values(key) for key in self._db.get_doc_keys(self.id)})

    def links(self, key: str) -> list[dict[str, str]]:
        """{name, url} of each value of a property, url being the value's page."""
        return [{"name": value, "url": page_name(key, value)} for value in self.values(key)]

    def source(self) -> str:
        """The Markdown text of the document ('' for a page without a source file)."""
        folder = self._site.paths.source
        path = os.path.join(folder, self.id) if folder else ""
        if not path or not os.path.isfile(path):
            return ""
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    @property
    def backlinks(self) -> list[dict[str, str]]:
        """{title, url} of the documents that link to this one."""
        plan = self._site._plan()
        found = (getattr(plan, "backlinks", None) or {}).get(self.id, []) if plan is not None else []
        return [{"title": title, "url": html_id_for(source)} for title, source in found]

    @property
    def modified(self) -> str | None:
        """When the document last changed (Modified property, git or file time), or None."""
        plan = self._site._plan()
        found: str | None = (getattr(plan, "modified", None) or {}).get(self.id) if plan is not None else None
        return found


class Documents:
    """The documents of the site (no system pages), newest first, undated ones last."""

    def __init__(self, site: Site):
        self._site = site

    def _ids(self) -> list[str]:
        db = self._site._db
        return [d for d in db.get_documents() if not db.is_system(d)]

    def __iter__(self) -> Iterator[Doc]:
        return (Doc(self._site, d) for d in self._ids())

    def __len__(self) -> int:
        return len(self._ids())

    def __contains__(self, doc: object) -> bool:
        doc_id = doc.id if isinstance(doc, Doc) else doc
        return doc_id in self._site._db.db and not self._site._db.is_system(doc_id)

    def get(self, doc_id: str) -> Doc | None:
        """The document with this id ('note.md'), system pages included, or None."""
        return Doc(self._site, doc_id) if doc_id in self._site._db.db else None

    def latest(self, n: int) -> list[Doc]:
        return list(self)[:n]

    def by_date(self) -> list[Doc]:
        return list(self)

    def with_value(self, key: str, value: str) -> list[Doc]:
        """Documents that have value among the values of key, newest first."""
        db = self._site._db
        return [Doc(self._site, d) for d in db.get_docs_by_key_value(key, value) if not db.is_system(d)]

    def filter(self, test: Callable[[Doc], bool]) -> list[Doc]:
        return [doc for doc in self if test(doc)]


class Properties:
    """The properties used by the documents and their values."""

    def __init__(self, site: Site):
        self._site = site

    def keys(self) -> tuple[str, ...]:
        """The properties that get pages: every key but the blocked and the ignored ones."""
        return tuple(self._site._db.get_theme_keys())

    def all_keys(self) -> tuple[str, ...]:
        """Every key of the documents except the blocked ones (Title, SystemPage, dates)."""
        return tuple(self._site._db.get_all_keys())

    def values(self, key: str) -> tuple[str, ...]:
        return tuple(self._site._db.get_all_values_for_key(key))

    def documents(self, key: str, value: str) -> list[Doc]:
        return self._site.documents.with_value(key, value)

    @staticmethod
    def url(key: str, value: str | None = None) -> str:
        return page_name(key, value)

    @property
    def blocked(self) -> tuple[str, ...]:
        return tuple(self._site._db.get_blocked_keys())

    @property
    def ignored(self) -> tuple[str, ...]:
        return tuple(self._site._db.get_ignored_keys())

    @property
    def hidden(self) -> tuple[str, ...]:
        """Keys left out of the properties page (repo.json hidden_properties)."""
        return tuple(self._site._db.get_hidden_keys())


class People:
    """The person profiles of the site."""

    def __init__(self, site: Site):
        self._site = site

    def _settings(self) -> Any:
        from kb4it.core.people import PeopleSettings
        return getattr(self._site._backend, "people", None) or PeopleSettings()

    @property
    def keys(self) -> tuple[str, ...]:
        """The properties that name people (Author by default)."""
        return tuple(self._settings().keys)

    def lookup(self, name: str) -> Any:
        """The profile of a person by name or alias, or None."""
        people = getattr(self._site._db, "people", None)
        return people.lookup(name) if people is not None and name else None

    def tip(self, name: str) -> str:
        """Role and team of a person, for a tooltip; '' without a profile."""
        return person_tip(self.lookup(name), self._settings())

    def status(self, name: str) -> str:
        return person_status(self.lookup(name), self._settings())


class Build:
    """What this build compiles."""

    def __init__(self, site: Site):
        self._site = site

    def changed(self, doc: Doc | str) -> bool:
        """True when the document is compiled in this build (new or changed, or a full build)."""
        plan = self._site._plan()
        doc_id = doc.id if isinstance(doc, Doc) else doc
        return plan is None or plan.force_all or doc_id in plan.docs_to_compile

    @property
    def documents_changed(self) -> int:
        plan = self._site._plan()
        return plan.doc_count if plan is not None else 0

    @property
    def keys_changed(self) -> tuple[str, ...]:
        plan = self._site._plan()
        return tuple(key for key, _values, flag in (plan.K_PATH if plan else ()) if flag)

    @property
    def force(self) -> bool:
        plan = self._site._plan()
        return bool(plan.force_all) if plan is not None else True

    @property
    def invalid(self) -> tuple[str, ...]:
        plan = self._site._plan()
        return tuple(doc for doc, _reason in (plan.invalid_docs if plan else ()))


class Paths:
    """Folders of the site."""

    def __init__(self, site: Site):
        self._site = site

    @property
    def source(self) -> str | None:
        path: str | None = self._site._backend.get_path("source")
        return path

    @property
    def target(self) -> str | None:
        """The published site; only complete after deployment (after_deploy)."""
        path: str | None = self._site._backend.get_path("target")
        return path


@dataclass(frozen=True)
class Table:
    """A table of documents, as site.table() renders it.

    columns: property names; 'Date' and 'Title' get their own cells. None: the
    repo.json "datatable" setting, else the theme's default.
    id: the HTML id of the table. filterable: the table filter bar may attach
    to it (feature table_filter). dates: {doc id: 'YYYY-MM-DD'}, the event day of
    each row, for a calendar panel that filters the table.
    """

    documents: tuple[Doc | str, ...] = ()
    columns: tuple[str, ...] | None = None
    id: str = "kb4it-datatable"
    filterable: bool = False
    dates: Mapping[str, str] | None = None

    def doc_ids(self) -> list[str]:
        return [d.id if isinstance(d, Doc) else d for d in self.documents]


class Site:
    """The knowledge base being built, as a theme sees it.

    db and backend are the Database and Backend services; host, the object that
    writes pages (the theme engine), is optional for read-only use.
    """

    def __init__(self, db: Any, backend: Any, host: Any = None, features: Mapping[str, Any] | None = None):
        self._db = db
        self._backend = backend
        self._host = host
        self._frozen: dict[str, Any] = {}
        self.documents = Documents(self)
        self.properties = Properties(self)
        self.people = People(self)
        self.build = Build(self)
        self.paths = Paths(self)
        self.features = _Features(features or {})

    def _plan(self) -> Any:
        getter = getattr(self._backend, "get_plan", None)
        return getter() if getter is not None else None

    def _settings(self, domain: str) -> Mapping[str, Any]:
        if domain not in self._frozen:
            self._frozen[domain] = _freeze(self._backend.get_dict(domain) or {})
        frozen: Mapping[str, Any] = self._frozen[domain]
        return frozen

    @property
    def repo(self) -> Mapping[str, Any]:
        """repo.json, read-only."""
        return self._settings("repo")

    @property
    def theme(self) -> Mapping[str, Any]:
        """theme.json of the theme being built, read-only."""
        return self._settings("theme")

    def doc(self, doc_id: str) -> Doc:
        """The Doc of an id, also for a system page."""
        return Doc(self, doc_id)

    def _need_host(self, what: str) -> Any:
        if self._host is None:
            raise RuntimeError(f"site.{what}() needs a theme engine; this Site is read-only")
        return self._host

    def page(self, name: str, title: str, html: str, *, markdown: bool = False, listing: bool = False) -> None:
        """Add a page to the site: name.html with this title and content.

        name may end in .html (page_name() gives it so). markdown: html is Markdown and goes through
        the converter like a document. listing: a page that only lists documents (search engines get
        noindex, follow).
        """
        name = name[:-5] if name.endswith(".html") else name
        self._need_host("page").add_system_page(name, title, html, as_html=not markdown, listing=listing)

    def keep(self, name: str, reason: str = "no_changes") -> bool:
        """Reuse name.html of the previous build when nothing it shows changed; True if kept."""
        return bool(self._need_host("keep").reuse_cached_page(name, "nck", reason, name))

    def table(self, table: Table) -> str:
        """The HTML of a document table."""
        host = self._need_host("table")
        render = getattr(host, "render_table", None)
        if render is not None:
            html: str = render(table)
            return html
        columns = list(table.columns) if table.columns is not None else None
        html = host.build_datatable(columns, table.doc_ids(), table.id)
        return html


class _Features(Mapping[str, Any]):
    """The enabled features by name, also as attributes: site.features.events."""

    def __init__(self, features: Mapping[str, Any]):
        self._features = dict(features)

    def __getitem__(self, name: str) -> Any:
        return self._features[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._features)

    def __len__(self) -> int:
        return len(self._features)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._features[name]
        except KeyError:
            raise AttributeError(f"feature {name!r} is not enabled") from None


def docs_of(site: Site, ids: Iterable[str]) -> list[Doc]:
    """Docs of a list of ids."""
    return [Doc(site, i) for i in ids]
