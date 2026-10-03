#!/usr/bin/env python3
"""AppHelp theme: help sites for applications that work from disk, on GitHub Pages and embedded."""

import json
import os

from apphelp_checks import (check_anchors, check_contract, check_helpids, helpid_map, load_contract,
                            render_helpids_js)
from apphelp_config import load_config
from apphelp_html import transform
from apphelp_meta import (DOCTYPES, LANDING, Problem, feature_anchor, is_classified, is_content, page_from_keys,
                          validate_all)
from apphelp_nav import build_sections, flatten, neighbours, related_pages
from apphelp_search import extract_sections, page_record, render_index_js

from kb4it.core.exceptions import ThemeError
from kb4it.core.util import get_hash_from_content, html_id_for
from kb4it.services.builder import Builder

ASSETS = "resources/themes/apphelp/framework/apphelp"
INDEX_WARN_BYTES = 2 * 1024 * 1024
SIGNATURE_REPO_KEYS = ("title", "tagline", "version", "logo", "logo_alt", "git", "git_server",
                       "git_user", "git_repo", "git_branch", "git_path", "apphelp")


class Theme(Builder):
    def _initialize(self):
        super()._initialize()
        self.config = load_config({})
        self.pages = {}
        self.sections = []
        self.flat = []
        self.theme_pages = set()

    def _source_metadata(self) -> dict:
        documents = self.srvbes.get_kb_dict()["document"]
        return {doc_id: info.get("keys", {}) for doc_id, info in documents.items()}

    def site_signature(self) -> str:
        repo = self.srvbes.get_dict("repo")
        payload = {"docs": self._source_metadata(), "repo": {k: repo.get(k) for k in SIGNATURE_REPO_KEYS}}
        return get_hash_from_content(json.dumps(payload, sort_keys=True, default=str))

    def build(self):
        repo = self.srvbes.get_dict("repo")
        self.config = load_config(repo)
        docs = self._source_metadata()
        plan = self.srvbes.get_plan()
        # Documents KB4IT could not read are left out of the site; they are metadata problems too.
        invalid = [Problem("DOC_INVALID", doc, f"reason={reason}") for doc, reason in (plan.invalid_docs if plan else [])]
        self._report(invalid + validate_all(docs, self.config))
        content = {d: k for d, k in docs.items() if is_content(d, k)}
        for doc_id in sorted(d for d, k in content.items() if not is_classified(k)):
            self._leave_out(doc_id)
        self.pages = {d: page_from_keys(d, k) for d, k in content.items() if is_classified(k)}
        self.sections = build_sections(list(self.pages.values()))
        self.flat = flatten(self.sections)
        self.theme_pages = set()
        labels = self.config.labels
        if LANDING not in docs:
            self._emit("index", repo.get("title", ""), self._render("PAGE_INDEX", self._landing_var()))
        self._emit("topics", labels["topics"], self._render("PAGE_TOPICS", self._topics_var()))
        self._emit("search", labels["search"], self._render("PAGE_SEARCH", {}))
        self._emit("go", labels["go_title"], self._render("PAGE_GO", {}))
        self._emit("404", labels["not_found_title"], self._render("PAGE_404", {}))
        if self.config.about:
            self.create_page_about_kb4it()
            self.create_page_about_app()

    def _leave_out(self, doc_id):
        """Keep a page without a valid type of document out of the site: not compiled, not deployed."""
        html = html_id_for(doc_id)
        targets = self.srvbes.get_value("docs", "targets")
        if targets is not None:
            targets.discard(html)
        staged = os.path.join(self.srvbes.get_path("tmp"), doc_id)
        if os.path.exists(staged):
            os.remove(staged)
        self.log.warning(f"[APPHELP] DOC_LEFT_OUT doc={doc_id} reason=unclassified")

    def _report(self, problems):
        for problem in problems:
            self.log.warning(f"[APPHELP] {problem}")
        if problems and self.config.strict:
            lines = "\n".join(f"  {problem}" for problem in problems)
            raise ThemeError(f"{len(problems)} metadata problem(s):\n{lines}")

    def _emit(self, name, title, html):
        """Add a theme-made page; build_page wraps it like any other page."""
        self.distribute_md(name, html)
        doc_id = f"{name}.md"
        self.srvdtb.add_document(doc_id)
        self.srvdtb.add_document_key(doc_id, "Title", title)
        self.srvdtb.add_document_key(doc_id, "SystemPage", "Yes")
        self.theme_pages.add(doc_id)

    def _render(self, name, extra):
        var = {"ah": self._common()}
        var.update(extra)
        return self.template(name).render(var=var)

    def _common(self) -> dict:
        repo = self.srvbes.get_dict("repo")
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
        values = self.srvdtb.get_values(doc_id, "Title")
        return values[0] if values else doc_id

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

    def _edit_url(self, doc_id) -> str:
        repo = self.srvbes.get_dict("repo")
        parts = [repo.get(k) for k in ("git_server", "git_user", "git_repo", "git_branch")]
        if not repo.get("git") or not all(parts):
            return ""
        server, user, name, branch = (str(p).strip("/") for p in parts)
        path = "/".join(x for x in (str(repo.get("git_path") or "").strip("/"), doc_id) if x)
        return f"https://{server}/{user}/{name}/edit/{branch}/{path}"

    def _page_var(self, doc_id, page, content, toc) -> dict:
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
            prev, nxt = neighbours(self.flat, doc_id)
            var["prev"] = {"title": prev.title, "url": prev.url} if prev else None
            var["next"] = {"title": nxt.title, "url": nxt.url} if nxt else None
            var["related"] = [self._card_item(p) for p in related_pages(page, self.flat)]
            var["edit_url"] = self._edit_url(doc_id)
            var["updated"] = page.date[:10]
        return var

    def _body_class(self, page):
        if page is None:
            return "ah-system"
        return f"ah-doctype-{page.doctype}" + (f" ah-layout-{page.layout}" if page.layout else "")

    def build_page(self, path_md):
        path_html = html_id_for(path_md)
        doc_id = os.path.basename(path_md)
        if not os.path.exists(path_html):
            self.log.error(f"[APPHELP] HTML_MISSING doc={doc_id}")
            return
        with open(path_html, encoding="utf-8") as fh:
            fragment = fh.read()
        page = self.pages.get(doc_id)
        if doc_id in self.theme_pages:
            content, toc = fragment, []
        else:
            content, toc = transform(fragment, page.doctype if page else "", page.layout if page else "",
                                     self.config.labels)
        html = self.template("HTML_BODY").render(var={"ah": self._page_var(doc_id, page, content, toc)})
        with open(path_html, "w", encoding="utf-8") as fh:
            fh.write(html)

    def _write(self, target, name, content):
        with open(os.path.join(target, name), "w", encoding="utf-8") as fh:
            fh.write(content)

    def post_deploy_activities(self):
        target = self.srvbes.get_path("target")
        self._write(target, ".nojekyll", "")
        self._write_search_index(target)
        mapping = helpid_map(self.flat)
        self._write(target, "helpids.js", render_helpids_js(mapping))
        self._run_checks(target, mapping)

    def _write_search_index(self, target):
        records = []
        for page in self.flat:
            path = os.path.join(target, page.url)
            if not os.path.isfile(path):
                self.log.warning(f"[APPHELP] INDEX_PAGE_MISSING page={page.url}")
                continue
            with open(path, encoding="utf-8") as fh:
                records.append(page_record(page, extract_sections(fh.read())))
        content = render_index_js(records)
        self._write(target, "search-index.js", content)
        size = len(content.encode("utf-8"))
        if size > INDEX_WARN_BYTES:
            self.log.warning(f"[APPHELP] INDEX_LARGE size={size}")
        self.log.info(f"[APPHELP] INDEX_BUILT pages={len(records)} size={size}")

    def _run_checks(self, target, mapping):
        pages = sorted(name for name in os.listdir(target) if name.endswith(".html"))
        for page, href in check_anchors(target, pages):
            self.log.warning(f"[APPHELP] ANCHOR_MISSING from={page} to={href}")
        missing_ids = check_helpids(target, mapping)
        for ident in missing_ids:
            self.log.warning(f"[APPHELP] HELPID_TARGET_MISSING id={ident} url={mapping[ident]}")
        if missing_ids and self.config.strict:
            raise ThemeError(f"Help ids point to missing pages or anchors: {', '.join(missing_ids)}")
        contract = os.path.join(str(self.srvbes.get_path("root")), self.config.contract)
        if self.config.contract_explicit and not os.path.isfile(contract):
            self.log.warning(f"[APPHELP] CONTRACT_FILE_MISSING path={contract}")
        missing = check_contract(load_contract(contract), mapping, target)
        for entry in missing:
            self.log.error(f"[APPHELP] CONTRACT_MISSING entry={entry}")
        if missing:
            raise ThemeError(f"{len(missing)} contract entries missing: {', '.join(missing)}")

    def generate_sources(self):
        pass

    def post_activities(self):
        self.log.debug("[APPHELP] POST_END")
