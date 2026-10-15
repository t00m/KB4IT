"""techdoc "Add" page: a form that writes a new document from a skeleton."""

import json
import os
from collections import Counter


class AddPageMixin:
    """The "Add" page of techdoc (add.html); part of techdoc's Theme class."""

    def build_page_add(self):
        """Create the 'Add document' helper page with per-category skeletons."""
        TPL = self.template('PAGE_ADD')
        var = self.get_theme_var()
        var['page']['title'] = 'Add document'
        runtime = self.srvbes.get_dict("runtime")
        skeletons_dir = os.path.join(runtime["theme"]["templates"], "skeletons")
        category_ids = ['change', 'incident', 'meeting', 'note', 'post', 'procedure', 'report', 'task']
        skeletons = {}
        for cat_id in category_ids:
            skel_path = os.path.join(skeletons_dir, f"{cat_id.upper()}-SKELETON.md")
            try:
                with open(skel_path, encoding="utf-8") as fh:
                    skeletons[cat_id] = fh.read()
            except OSError:
                skeletons[cat_id] = f"---\nDate: YYYY-MM-DD\nVersion: 1.0\nCategory: {cat_id.capitalize()}\n---\n\n# Title of the {cat_id.capitalize()}\n\n## Overview\n\nDescribe here.\n"
        var['page']['skeletons'] = skeletons
        # Printed raw inside <script>: "<" as \u003c so no value can close the script element.
        var['page']['skeletons_json'] = json.dumps(skeletons, ensure_ascii=True).replace("<", "\\u003c")
        keys_data = {}
        all_docs = self.srvdtb.get_documents()
        for key in self.srvdtb.get_theme_keys():
            counter = Counter()
            for docId in all_docs:
                for val in self.srvdtb.get_values(docId, key):
                    if val:
                        counter[val] += 1
            if counter:
                keys_data[key] = [{'v': v, 'c': c} for v, c in sorted(counter.items())]
        var['page']['keys_json'] = json.dumps(keys_data, ensure_ascii=True).replace("<", "\\u003c")
        page = TPL.render(var=var)
        self.distribute_md('add', page)
        self.srvdtb.add_document('add.md')
        self.srvdtb.add_document_key('add.md', 'Title', 'Add document')
        self.srvdtb.add_document_key('add.md', 'SystemPage', 'Yes')
