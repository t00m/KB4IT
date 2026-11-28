#!/usr/bin/env python3
"""AppHelp theme: help sites for applications that work from disk, on GitHub Pages and embedded."""

import json
import os

from kb4it.core.structured import DEFAULT_MAP
from kb4it.core.util import get_hash_from_content, html_id_for
from kb4it.theme import BaseTheme, ThemeError, q
from kb4it.theme import Problem as CheckProblem

from .apphelp_checks import check_contract, check_helpids, helpid_map, load_contract, render_helpids_js
from .apphelp_config import HelpConfig, load_config
from .apphelp_html import transform
from .apphelp_meta import (DOCTYPES, LANDING, LAYOUTS, Problem, feature_anchor, is_classified, is_content,
                           page_from_keys, validate_all)
from .apphelp_nav import build_sections, flatten, related_pages
from .apphelp_search import extract_sections, page_record
from .apphelp_versions import publish as publish_versions

ASSETS = "resources/themes/apphelp/framework/apphelp"
INDEX_WARN_BYTES = 2 * 1024 * 1024
SIGNATURE_REPO_KEYS = ("title", "tagline", "version", "logo", "logo_alt", "git", "git_server",
                       "git_user", "git_repo", "git_branch", "git_path", "apphelp")


# apphelp page properties in the structured data; None leaves a key out.
STRUCTURED_MAP = {
    "Feature": "about:Thing", "Level": "educationalLevel", "Platform": "audience:Audience",
    "Since": "version", "Keyword": "keywords", "Plugin": "mentions:SoftwareApplication",
    "Section": "articleSection", "HelpId": None, "Order": None, "Layout": None, "Related": None,
}


class Theme(BaseTheme):
    features = ("navigation", "search", "editor", "about")
    log_area = "APPHELP"
    # Help sites have no person pages, so the Add page offers no Person profile.
    profile_skeleton = False
    # No person pages either: the schema.org Person of each profile goes into the home page.
    person_pages = False
    config_class = HelpConfig  # KB4IT sets self.config from the "apphelp" block of repo.json
    search_index_var = "APPHELP_INDEX"
    search_index_warn_bytes = INDEX_WARN_BYTES
    search_own_page = True    # build() writes search.html, which reads ?q=
    search_optional = False   # the help always has its search

    @staticmethod
    def template_var(ctx) -> dict:
        """The template context: under "apphelp", and under "ah" as the templates always used it (P3)."""
        return {"apphelp": ctx, "ah": ctx}

    def setup(self):
        self.config = load_config({})  # KB4IT replaces it; a Theme() built by hand keeps the defaults
        self.pages = {}
        self.sections = []
        self.flat = []
        self.theme_pages = set()

    def page_lang(self) -> str:
        """apphelp.lang wins over seo.lang (apphelp had its own setting first)."""
        return load_config(self.site.repo).lang

    def structured_defaults(self) -> dict:
        """The apphelp vocabulary (Feature, Level, Platform, Since...) in the structured data."""
        return {"type": "TechArticle", "map": {**DEFAULT_MAP, **STRUCTURED_MAP}}

    def search_page(self) -> str:
        """apphelp always builds search.html, which reads ?q=."""
        return "search.html"

    def about_pages(self) -> bool:
        """The About pages only with apphelp.about."""
        return self.config.about

    def _source_metadata(self) -> dict:
        """{source file: its front matter}, every document KB4IT read, also the ones left out of the site."""
        documents = self.internals.backend.get_kb_dict()["document"]
        return {doc_id: info.get("keys", {}) for doc_id, info in documents.items()}

    def site_signature(self) -> str:
        repo = self.site.repo
        payload = {"docs": self._source_metadata(), "repo": {k: repo.get(k) for k in SIGNATURE_REPO_KEYS}}
        return get_hash_from_content(json.dumps(payload, sort_keys=True, default=str))

    def target_subdir(self):
        """With versions on, each version builds into its own folder of the target."""
        config = load_config(self.site.repo)
        if not config.versions:
            return None
        if not config.version:
            raise ThemeError("apphelp versions need the 'version' key in repo.json, such as \"1.0\" or \"kb4it\"")
        return config.version

    def build(self, site):
        repo = site.repo
        docs = self._source_metadata()
        # Documents KB4IT could not read are left out of the site; they are metadata problems too.
        invalid = [Problem("DOC_INVALID", doc, f"reason={reason}") for doc, reason in site.build.invalid]
        self._report(invalid + validate_all(docs, self.config))
        content = {d: k for d, k in docs.items() if is_content(d, k)}
        for doc_id in sorted(d for d, k in content.items() if not is_classified(k)):
            self._leave_out(doc_id)
        self.pages = {d: page_from_keys(d, k) for d, k in content.items() if is_classified(k)}
        self.sections = build_sections(list(self.pages.values()))
        self.flat = flatten(self.sections)
        labels = self.config.labels
        if LANDING not in docs:
            self._emit("index", repo.get("title", ""), self._render("PAGE_INDEX", self._landing_var()))
        self._emit("topics", labels["topics"], self._render("PAGE_TOPICS", self._topics_var()))
        self._emit("search", labels["search"], self._render("PAGE_SEARCH", {}))
        self._emit("go", labels["go_title"], self._render("PAGE_GO", {}))
        self._emit("404", labels["not_found_title"], self._render("PAGE_404", {}))

    def register_add_page(self, html):
        """Emit add.html through _emit() so the page pipeline wraps it like the other theme pages."""
        self._emit("add", self.config.labels["add"], html)

    def editor_keys(self) -> dict:
        """Completion data of the documents plus the allowed values no document uses yet, with count 0."""
        keys = self.site.features.editor.editor_keys()
        allowed = {name: list(values) for name, values in self.config.vocabulary.items()}
        allowed["DocType"] = list(DOCTYPES)
        allowed["Layout"] = list(LAYOUTS)
        for name, values in allowed.items():
            seen = {item["v"] for item in keys.get(name, [])}
            extra = [{"v": value, "c": 0} for value in values if value not in seen]
            if extra:
                keys[name] = sorted(keys.get(name, []) + extra, key=lambda item: item["v"])
        return keys

    def _leave_out(self, doc_id):
        """Keep a page without a valid type of document out of the site: not compiled, not deployed."""
        backend = self.internals.backend
        html = html_id_for(doc_id)
        targets = backend.get_value("docs", "targets")
        if targets is not None:
            targets.discard(html)
        staged = os.path.join(backend.get_path("tmp"), doc_id)
        if os.path.exists(staged):
            os.remove(staged)
        self.log.warning(f"[APPHELP] DOC_LEFT_OUT doc={q(doc_id)} reason=unclassified")

    def _report(self, problems):
        for problem in problems:
            self.log.warning(f"[APPHELP] {problem}")
        if problems and self.config.strict:
            lines = "\n".join(f"  {problem}" for problem in problems)
            raise ThemeError(f"{len(problems)} metadata problem(s):\n{lines}")

    def _emit(self, name, title, html):
        """Add a theme-made page; the page pipeline wraps it like any other page."""
        self.site.page(name, title, html)
        self.theme_pages.add(f"{name}.md")

    def _render(self, name, extra):
        var = self.template_var(self._common())
        var.update(extra)
        return self.template(name).render(var=var)

    def _common(self) -> dict:
        repo = self.site.repo
        title = repo.get("title", "")
        version = self.config.version
        return {
            "lang": self.config.lang,
            "accent": self.config.accent,
            "labels": self.config.labels,
            "labels_json": json.dumps(self.config.labels, ensure_ascii=False).replace("</", "<\\/"),
            "site_title": title,
            "tagline": repo.get("tagline", ""),
            "version": version,
            "footer_name": f"{title} {version}".strip(),
            "logo": repo.get("logo", ""),
            "assets": ASSETS,
            "highlight": (repo.get("markdown") or {}).get("highlight", "client"),
            "versions": self.config.versions,
            "editor": self.site.features.editor.enabled(),
        }

    def _label(self, name, fallback):
        return self.config.labels.get(name, fallback)

    def _card_item(self, page) -> dict:
        return {"title": page.title, "url": page.url, "summary": page.summary,
                "doctype": page.doctype, "doctype_label": self._label(f"doctype_{page.doctype}", page.doctype)}

    def _landing_var(self) -> dict:
        cards = []
        for doctype in DOCTYPES.values():
            entries = [page for page in self.flat if page.doctype == doctype]
            if entries:
                cards.append({"doctype": doctype,
                              "label": self._label(f"doctype_{doctype}_title", doctype),
                              "desc": self._label(f"doctype_{doctype}_desc", ""),
                              "pages": [self._card_item(p) for p in entries[:5]], "more": len(entries) - 5})
        version = self.config.version
        new = [self._card_item(p) for p in self.flat if version and p.since == version]
        return {"cards": cards, "new": new}

    def _topics_var(self) -> dict:
        order = list(self.config.vocabulary.get("Feature", []))
        for page in self.flat:
            order += [f for f in page.features if f not in order]
        groups = []
        for name in order:
            entries = [self._card_item(p) for p in self.flat if name in p.features]
            if entries:
                groups.append({"name": name, "anchor": feature_anchor(name), "pages": entries})
        return {"groups": groups}

    def _doc_title(self, doc_id):
        return self.site.doc(doc_id).value("Title", doc_id)

    def _sidebar(self, doc_id) -> list:
        return [{"name": name,
                 "current": any(p.doc_id == doc_id for p in entries),
                 "pages": [{"title": p.title, "url": p.url, "current": p.doc_id == doc_id} for p in entries]}
                for name, entries in self.sections]

    def _chips(self, page):
        if page is None:
            return None
        return {
            "doctype": page.doctype, "doctype_label": self._label(f"doctype_{page.doctype}", page.doctype),
            "section": page.section,
            "features": [{"name": f, "anchor": feature_anchor(f)} for f in page.features],
            "level": page.level, "platforms": page.platforms, "since": page.since, "plugin": page.plugin,
        }

    def _page_var(self, doc_id, page, content, toc, edit_url="") -> dict:
        var = self._common()
        var.update({
            "title": page.title if page else self._doc_title(doc_id),
            "summary": page.summary if page else "",
            "content": content,
            "toc": toc,
            "page": self._chips(page),
            "sections": self._sidebar(doc_id),
            "prev": None,
            "next": None,
            "related": [],
            "edit_url": "",
            "updated": "",
            "body_class": self._body_class(page),
            "load_helpids": doc_id == "go.md",
        })
        if page is not None:
            neighbours = self.site.features.navigation.neighbours(self.site.doc(doc_id))
            prev, nxt = (self.pages.get(d.id) if d else None for d in neighbours)
            var["prev"] = {"title": prev.title, "url": prev.url} if prev else None
            var["next"] = {"title": nxt.title, "url": nxt.url} if nxt else None
            var["related"] = [self._card_item(p) for p in related_pages(page, self.flat)]
            var["edit_url"] = edit_url
            var["updated"] = page.date[:10]
        return var

    def _body_class(self, page):
        if page is None:
            return "ah-system"
        return f"ah-doctype-{page.doctype}" + (f" ah-layout-{page.layout}" if page.layout else "")

    def page_var(self):
        """apphelp templates read only the "ah" context, so a page needs no base_var()."""
        return {"page": {"title": ""}}

    def body_transforms(self, doc, var):
        """Theme pages stay as they are; a help page gets the apphelp rewrite and its own TOC."""
        var["apphelp_toc"] = []
        if doc.id in self.theme_pages:
            return []
        page = self.pages.get(doc.id)

        def rewrite(html):
            content, var["apphelp_toc"] = transform(html, page.doctype if page else "", page.layout if page else "",
                                                    self.config.labels)
            return content
        return [rewrite]

    def render_page(self, doc, var):
        """One HTML_BODY template with the apphelp context."""
        page = self.pages.get(doc.id)
        return self.template("HTML_BODY").render(
            var=self.template_var(self._page_var(doc.id, page, var["source_html"], var["apphelp_toc"],
                                                 var["edit_url"])))

    def _write(self, target, name, content):
        with open(os.path.join(target, name), "w", encoding="utf-8") as fh:
            fh.write(content)

    def after_deploy(self, site):
        target = site.paths.target
        self._write(target, ".nojekyll", "")
        self._write(target, "helpids.js", render_helpids_js(helpid_map(self.flat)))

    def checks(self, site) -> list:
        """The shared anchor check, then help ids and the contract file."""
        target = site.paths.target
        problems = super().checks(site)
        mapping = helpid_map(self.flat)
        severity = "error" if self.config.strict else "warning"
        problems += [CheckProblem("HELPID_TARGET_MISSING", "", f"id={q(ident)} url={q(mapping[ident])}", severity)
                     for ident in check_helpids(target, mapping)]
        contract = os.path.join(str(self.internals.backend.get_path("root")), self.config.contract)
        if self.config.contract_explicit and not os.path.isfile(contract):
            problems.append(CheckProblem("CONTRACT_FILE_MISSING", "", f"path={q(contract)}"))
        problems += [CheckProblem("CONTRACT_MISSING", "", f"entry={q(entry)}", "error")
                     for entry in check_contract(load_contract(contract), mapping, target)]
        return problems

    def after_checks(self, site):
        """Publish the version folder only after the checks pass."""
        if self.config.versions:
            site_root = self.internals.backend.get_path("site_root")
            labels, latest = publish_versions(site_root, self.config.version, self.config.latest)
            self.log.info(f"[VERSIONS] PUBLISHED current={q(self.config.version)} latest={q(latest)} all={q(','.join(labels))}")

    def ordered_pages(self, doc) -> list:
        """Every page, section by section, in the sidebar order."""
        return [page.doc_id for page in self.flat]

    def search_documents(self) -> list:
        """The pages in reading order."""
        return [page.doc_id for page in self.flat]

    def search_record(self, doc):
        """apphelp facets (DocType, Feature, Level...); None when the page file was not written."""
        page = self.pages.get(doc.id)
        if page is None:
            return None
        if not os.path.isfile(os.path.join(self.site.paths.target, page.url)):
            self.log.warning(f"[APPHELP] INDEX_PAGE_MISSING page={q(page.url)}")
            return None
        return page_record(page, [])

    def search_sections(self, doc) -> list:
        """The sections of the built page's article."""
        path = os.path.join(self.site.paths.target, self.pages[doc.id].url)
        with open(path, encoding="utf-8") as fh:
            return [[s["id"], s["heading"], s["text"]] for s in extract_sections(fh.read())]

    def after_build(self, site):
        self.log.debug("[APPHELP] POST_END")
