"""The page pipeline of every theme: build_page() and its hooks, generated pages, the edit link and the title."""

import os
from datetime import datetime

from kb4it.core.log import q
from kb4it.core.util import ellipsize_text, get_human_datetime, html_id_for

GIT_KEYS = ("git_server", "git_user", "git_repo", "git_branch")


def git_ready(repo) -> bool:
    """True when repo.json turns git links on and names server, user, repository and branch.

    git_path may stay empty (documents at the repository root). A "{placeholder}" counts as unset,
    so a sample configuration never produces edit links that lead nowhere.
    """
    if repo.get("git") is not True:
        return False
    values = [repo.get(key) for key in GIT_KEYS] + [repo.get("git_path") or ""]
    return all(isinstance(v, str) for v in values) and all(v.strip() for v in values[:4]) and \
        not any("{" in v for v in values)


class PagePipelineMixin:
    """Mixin of Builder: build_page() runs the same steps for every theme and calls small hooks.

    A theme overrides the hooks it needs. A theme that overrides build_page() keeps its own pipeline.
    """

    # Title of a page whose document has no Title.
    untitled_label = ""
    # Area of the HTML_MISSING log line.
    log_area = "THEME"
    # Cut long titles with ellipsize_text(); techdoc cuts them with CSS.
    ellipsize_titles = True

    def build_page(self, path_md: str) -> None:
        """Turn the compiled body of a document into its final page and overwrite the HTML file."""
        path_hdoc = html_id_for(path_md)
        doc_id = os.path.basename(path_md)
        if not os.path.exists(path_hdoc):
            self.log.error(f"[{self.log_area}] HTML_MISSING doc={q(doc_id)}")
            return
        with open(path_md, encoding="utf-8") as fh:
            source_md = fh.read()
        with open(path_hdoc, encoding="utf-8") as fh:
            source_html = fh.read()

        var = self.get_theme_var()
        var["keys"] = self.srvdtb.get_doc_properties(doc_id)
        var["basename_md"] = doc_id
        var["basename_hdoc"] = os.path.basename(path_hdoc)
        var["source_md"] = source_md
        var["timestamp"] = get_human_datetime(datetime.now())
        var["toc"] = self.page_toc(source_html)
        var["has_toc"] = True
        var["SystemPage"] = self.srvdtb.is_system(doc_id)
        var["edit_url"] = self.edit_url(doc_id)
        title = self.page_title(doc_id)
        cut = self.ellipsize_titles and title != self.untitled_label
        var["page"]["title"] = ellipsize_text(title) if cut else title
        var["page"]["title-tooltip"] = title

        var = self.page_context(doc_id, var)
        html = source_html
        for transform in self.body_transforms(doc_id, var):
            html = transform(html)
        var["source_html"] = html
        var["actions"] = self.page_actions(var)
        html = self.finalize_html(self.render_page(doc_id, var))
        with open(path_hdoc, "w", encoding="utf-8") as fh:
            fh.write(html)

    def page_toc(self, source_html: str) -> str:
        """Table of contents of the page; document themes extract it from the compiled body."""
        return ""

    def page_context(self, doc_id: str, var: dict) -> dict:
        """Add the theme's own data to var before the body is rewritten and the page rendered."""
        return var

    def body_transforms(self, doc_id: str, var: dict) -> list:
        """Functions from HTML to HTML applied in order to the compiled body."""
        return [self.apply_transformations]

    def page_actions(self, var: dict) -> str:
        """HTML of the page actions (edit, properties...); '' when the theme has none."""
        return ""

    def page_body_template(self, doc_id: str, var: dict) -> str:
        """Name of the template that renders the body of the page."""
        return "HTML_BODY"

    def render_page(self, doc_id: str, var: dict) -> str:
        """Whole page: header, body and footer templates rendered with var."""
        return "".join(self.template(name).render(var=var) for name in
                       ("HTML_HEADER_COMMON", self.page_body_template(doc_id, var), "HTML_FOOTER"))

    def finalize_html(self, html: str) -> str:
        """Last change to the whole page before it is written."""
        return html

    def edit_url(self, doc_id: str = "") -> str:
        """Link to edit doc_id on the git server, or to the source folder without doc_id; '' when git is off.

        git_server may be a URL (https://github.com) or a host name (github.com); a host gets https://.
        """
        repo = self.srvbes.get_dict("repo") or {}
        if not git_ready(repo):
            return ""
        server = repo["git_server"].strip().strip("/")
        if "://" not in server:
            server = f"https://{server}"
        parts = [repo[key].strip().strip("/") for key in GIT_KEYS[1:3]]
        branch = repo["git_branch"].strip().strip("/")
        tail = [p for p in ((repo.get("git_path") or "").strip().strip("/"), doc_id) if p]
        return "/".join([server, *parts, "edit", branch, *tail])

    def add_system_page(self, name: str, title: str, html: str | None = None, as_html: bool = True,
                        listing: bool = False) -> None:
        """Add a page the theme generates: write it (unless html is None) and register it as a system page."""
        if html is not None:
            self.distribute_md(name, html, as_html=as_html, listing=listing)
        doc_id = f"{name}.md"
        self.srvdtb.add_document(doc_id)
        self.srvdtb.add_document_key(doc_id, "Title", title)
        self.srvdtb.add_document_key(doc_id, "SystemPage", "Yes")

    def page_title(self, doc_id: str) -> str:
        """Title of a document page, or untitled_label when the document has none."""
        return self.srvdtb.get_doc_properties(doc_id).get("Title") or self.untitled_label
