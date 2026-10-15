"""Metadata of a document page: the property and value links, and the page actions."""

from __future__ import annotations

import os
from typing import Any

from kb4it.core.util import valid_filename
from kb4it.services.themekit.host import ThemeHost


class MetadataMixin(ThemeHost):
    """Metadata section and page actions; needs `Builder.template` and `srvdtb`."""

    def get_page_actions(self, var: dict[str, Any]) -> str:
        """Return the html of the page actions (SECTION_ACTIONS)."""
        return self.template('SECTION_ACTIONS').render(var=var)

    def get_labels(self, values: list[tuple[str, str]]) -> str:
        """Return the html links for (page, text) pairs; empty texts are left out."""
        label_links = ''
        tpl_value_link = self.template('METADATA_VALUE_LINK')
        for page, text in values:
            if text:
                label_links += tpl_value_link.render(var={'link_url': valid_filename(page), 'link_name': text})
        return label_links

    def get_html_values_from_key(self, docId: str, key: str) -> list[tuple[str, str]]:
        """Return (page, value) pairs for the values of a property of a document."""
        return [(f"{key}_{value}.html", value) for value in self.srvdtb.get_values(docId, key)]

    def build_metadata_section(self, docId: str) -> str:
        """Return a html block for displaying metadata (keys and values)."""
        try:
            tpl_section = self.template('METADATA_SECTION')
            var: dict[str, Any] = {'items': []}
            for key in self.srvdtb.get_custom_keys(os.path.basename(docId)):
                try:
                    values = self.get_html_values_from_key(docId, key)
                    var['items'].append({
                        'doc': docId,
                        'key': key,
                        'vfkey': valid_filename(key),
                        'labels': self.get_labels(values),
                    })
                except Exception as error:
                    self.log.error(f"[THEME] KEY_FAIL key={key} error={error}")
                    raise
            return tpl_section.render(var=var)
        except Exception as error:
            self.log.error(f"[THEME] METADATA_FAIL doc={docId} error={error}")
            raise
