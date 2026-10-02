"""Smallest KB4IT theme, used by the core tests."""

import json
import os

from kb4it.core.util import html_id_for, valid_filename
from kb4it.core.exceptions import ThemeError
from kb4it.services.builder import Builder


class Theme(Builder):
    def build(self):
        if "boom.md" in self.srvdtb.get_documents():
            raise ThemeError("boom page present")
        self.create_page_about_kb4it()
        self.create_page_about_app()

    def build_page(self, path_md):
        path_html = html_id_for(path_md)
        with open(path_html, encoding="utf-8") as fh:
            body = fh.read()
        ndocs = len(self.srvdtb.get_documents())
        html = self.template("HTML_BODY").render(var={"body": body, "ndocs": ndocs})
        with open(path_html, "w", encoding="utf-8") as fh:
            fh.write(html)

    def build_page_key(self, key, values):
        self.distribute_md(valid_filename(key), f"<p>{key}</p>")

    def build_page_key_value(self, kvpath):
        key, value, compile_value = kvpath
        if compile_value:
            self.distribute_md(f"{valid_filename(key)}_{valid_filename(value)}", f"<p>{key}: {value}</p>")

    def site_signature(self):
        if not self.srvbes.get_dict("theme").get("test_signature"):
            return ""
        return ",".join(sorted(self.srvbes.get_kb_dict()["document"]))

    def post_deploy_activities(self):
        target = self.srvbes.get_path("target")
        with open(os.path.join(target, "documents.json"), "w", encoding="utf-8") as fh:
            json.dump(self.srvdtb.get_documents(), fh)
