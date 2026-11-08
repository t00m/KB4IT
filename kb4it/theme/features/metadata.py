"""Feature metadata: the property and value links of a document page, and its page actions."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from kb4it.core.dateclass import display_date
from kb4it.core.log import q
from kb4it.core.util import valid_filename
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc


class Metadata(Feature):
    """section(doc): the METADATA_SECTION of a document; actions(var): its SECTION_ACTIONS."""

    name = "metadata"
    hooks = ("build_metadata_section",)
    templates = ("METADATA_SECTION", "METADATA_VALUE_LINK", "SECTION_ACTIONS")

    def actions(self, var: dict[str, Any]) -> str:
        """The html of the page actions (SECTION_ACTIONS)."""
        html: str = self.engine.template('SECTION_ACTIONS').render(var=var)
        return html

    def labels(self, values: list[tuple[str, str]]) -> str:
        """The html links of (page, text) pairs; empty texts are left out."""
        label_links = ''
        tpl_value_link = self.engine.template('METADATA_VALUE_LINK')
        for page, text in values:
            if text:
                url = valid_filename(page) if page else '#'
                label_links += tpl_value_link.render(var={'link_url': url, 'link_name': text})
        return label_links

    def values_of(self, doc_id: str, key: str) -> list[tuple[str, str]]:
        """(page, value) pairs of a property of a document; a date key has no page."""
        db = self.engine.srvdtb
        if key in db.get_blocked_keys():
            return [("", display_date(value)) for value in db.get_values(doc_id, key)]
        return [(f"{key}_{value}.html", value) for value in db.get_values(doc_id, key)]

    def section_html(self, doc_id: str) -> str:
        """The METADATA_SECTION block of a document (keys and values)."""
        engine = self.engine
        try:
            tpl_section = engine.template('METADATA_SECTION')
            var: dict[str, Any] = {'items': []}
            blocked = set(engine.srvdtb.get_blocked_keys())
            for key in engine.srvdtb.get_custom_keys(os.path.basename(doc_id)):
                try:
                    values = self.values_of(doc_id, key)
                    var['items'].append({
                        'doc': doc_id,
                        'key': key,
                        'vfkey': valid_filename(key),
                        'has_page': key not in blocked,  # date keys get no page of their own
                        'labels': self.labels(values),
                    })
                except Exception as error:
                    engine.log.error(f"[THEME] KEY_FAIL key={q(key)} error={q(error)}", exc_info=True)
                    raise
            html: str = tpl_section.render(var=var)
            return html
        except Exception as error:
            engine.log.error(f"[THEME] METADATA_FAIL doc={q(doc_id)} error={q(error)}", exc_info=True)
            raise

    def build_metadata_section(self, doc: Doc) -> str:
        """Default of the hook: the metadata section of a document."""
        return self.section_html(doc.id)

    def section(self, doc: Doc) -> str:
        """The metadata section of a document, through the theme's hook when it has one."""
        html: str = self.hook("build_metadata_section")(doc)
        return html
