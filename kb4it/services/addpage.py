"""The Add page (add.html) of the editor: the `editor` setting, the skeletons and the whole page."""

import json
import os
import re
from collections import Counter

from kb4it.core.env import ENV
from kb4it.core.exceptions import ConfigError, ThemeError

ADD_DOC = "add.md"   # source name reserved while the editor is on
SUFFIX = "-SKELETON.md"
SKELETON_ID = re.compile(r"^[a-z][a-z0-9-]*$")


def check_editor_setting(repo: dict) -> None:
    """Raise ConfigError when repo.json 'editor' is set to anything but true or false."""
    if "editor" in repo and not isinstance(repo["editor"], bool):
        raise ConfigError("repo.json 'editor' must be true or false")


def check_theme_editor(theme: dict) -> None:
    """Raise ThemeError when theme.json 'editor' is set to anything but true or false."""
    if "editor" in theme and not isinstance(theme["editor"], bool):
        name = theme.get("id") or theme.get("name") or "?"
        raise ThemeError(f"Theme {name}: theme.json 'editor' must be true or false")


def editor_on(repo: dict, theme: dict) -> bool:
    """True when repo.json 'editor' is true, or when it is unset and theme.json 'editor' is true."""
    if "editor" in repo:
        return repo["editor"] is True
    return theme.get("editor") is True


class AddPageMixin:
    """Builder part that decides whether the Add page exists and builds it with its skeletons."""

    # The Add page offers the Person profile skeleton; a theme without person pages sets it to False.
    profile_skeleton = True

    add_page = False   # a Theme class sets True when it builds the Add page (create_page_add())

    def editor_enabled(self) -> bool:
        """True when the theme class supports the Add page and the editor setting is on."""
        if not self.add_page:
            return False
        return editor_on(self.srvbes.get_dict("repo") or {}, self.srvbes.get_dict("theme") or {})

    def remove_stale_add_page(self) -> None:
        """Remove add.html left by an earlier build from the target and the cache."""
        for folder in ("target", "cache"):
            path = os.path.join(self.srvbes.get_path(folder), "add.html")
            if os.path.exists(path):
                os.unlink(path)

    def create_page_add(self) -> None:
        """Build add.html when the editor is on, otherwise remove the page an earlier build left."""
        if not self.editor_enabled():
            self.remove_stale_add_page()
            self.log.info("[BUILDER] ADD_PAGE enabled=False")
            return
        html, source, count = self._render_add_page()
        self.log.info(f"[BUILDER] ADD_PAGE enabled=True skeletons={source} categories={count}")
        self.register_add_page(html)

    def register_add_page(self, html: str) -> None:
        """Write the Add page body and register it as a system page; a theme may override this only."""
        self.distribute_md("add", html)
        self.srvdtb.add_document(ADD_DOC)
        self.srvdtb.add_document_key(ADD_DOC, "Title", "Add document")
        self.srvdtb.add_document_key(ADD_DOC, "SystemPage", "Yes")

    def _render_add_page(self) -> tuple[str, str, int]:
        """Return (html, skeleton source, number of categories) of the Add page."""
        source, categories = self.skeleton_set()
        if self.profile_skeleton and not any(c["id"] == "person" for c in categories):
            categories = [*categories, self.person_category()]
        var = self.get_theme_var()
        var["page"]["title"] = "Add document"
        var["page"]["categories"] = categories
        # Printed raw inside <script>: "<" as \u003c so no value can close the script element.
        skeletons = {c["id"]: {"name": c["name"], "text": c["text"]} for c in categories}
        var["page"]["skeletons_json"] = json.dumps(skeletons, ensure_ascii=True).replace("<", "\\u003c")
        var["page"]["keys_json"] = json.dumps(self.editor_keys(), ensure_ascii=True).replace("<", "\\u003c")
        var["page"]["editor_dialogs"] = self.render_template("EDITOR_DIALOGS", var)
        return self.render_template("PAGE_ADD", var), source, len(categories)

    def person_category(self) -> dict:
        """The Person profile skeleton, added to every skeleton set (see core/people.py)."""
        path = os.path.join(ENV["GPATH"]["TEMPLATES"], "profile", "PERSON" + SUFFIX)
        with open(path, "rb") as fin:
            text = fin.read().decode("utf-8").replace("\r\n", "\n")
        return {"id": "person", "name": "Person profile",
                "description": ("A person named in the documents: role, team and how to reach them. "
                                "Save it in the source folder and rebuild to show it on the person's page."),
                "color": "#6d28d9", "icon": "user", "text": text}

    def editor_keys(self) -> dict:
        """Completion data {Key: [{"v": value, "c": count}]} from the repository's documents."""
        keys_data = {}
        all_docs = self.srvdtb.get_documents()
        for key in self.srvdtb.get_theme_keys():
            counter = Counter()
            for doc_id in all_docs:
                for val in self.srvdtb.get_values(doc_id, key):
                    if val:
                        counter[val] += 1
            if counter:
                keys_data[key] = [{"v": v, "c": c} for v, c in sorted(counter.items())]
        return keys_data

    def skeleton_set(self) -> tuple[str, list[dict]]:
        """Return (source, categories) of the first skeleton folder that holds a *-SKELETON.md file.

        source is "overrides", "theme" or "common". Each category has id, name,
        description, color, icon and text. Sets are never merged.
        """
        overrides = getattr(self.srvbes, "overrides_dir", None)
        candidates = []
        if overrides:
            candidates.append(("overrides", os.path.join(overrides, "templates", "skeletons")))
        theme_templates = self.srvbes.get_dict("runtime")["theme"]["templates"]
        candidates.append(("theme", os.path.join(theme_templates, "skeletons")))
        candidates.append(("common", os.path.join(ENV["GPATH"]["TEMPLATES"], "skeletons")))
        for source, folder in candidates:
            files = sorted(f for f in os.listdir(folder) if f.endswith(SUFFIX)) if os.path.isdir(folder) else []
            if files:
                return source, self._read_skeleton_set(folder, files)
        return "common", []

    def _read_skeleton_set(self, folder: str, files: list[str]) -> list[dict]:
        """Build the categories of one skeleton folder, in skeletons.json order when it exists."""
        listing = os.path.join(folder, "skeletons.json")
        has_json = os.path.exists(listing)
        if has_json:
            entries = self._read_skeleton_listing(listing)
            for entry in entries:
                entry["file"] = f"{entry['id'].upper()}{SUFFIX}"
        else:
            entries = []
            ids = {}
            for name in files:
                cat_id = name[:-len(SUFFIX)].lower()
                if not SKELETON_ID.match(cat_id):
                    raise ThemeError(f"{os.path.join(folder, name)}: id '{cat_id}' must match ^[a-z][a-z0-9-]*$")
                if cat_id in ids:
                    raise ThemeError(f"{folder}: {ids[cat_id]} and {name} give the same id '{cat_id}'")
                ids[cat_id] = name
                entries.append({"id": cat_id, "file": name})
            entries.sort(key=lambda e: e["id"])
        categories = []
        for entry in entries:
            path = os.path.join(folder, entry["file"])
            if not os.path.isfile(path):
                raise ThemeError(f"{listing}: id '{entry['id']}' has no file {entry['file']}")
            with open(path, "rb") as fin:
                # LF newlines, as the editor writes them, also for a skeleton saved with CRLF on Windows.
                text = fin.read().decode("utf-8").replace("\r\n", "\n")
            categories.append({
                "id": entry["id"],
                "name": entry.get("name") or entry["id"][:1].upper() + entry["id"][1:],
                "description": entry.get("description") or "",
                "color": entry.get("color") or "",
                "icon": entry.get("icon") or "",
                "text": text,
            })
        if has_json:
            listed = {e["file"] for e in entries}
            for name in files:
                if name not in listed:
                    self.log.warning(f"[BUILDER] SKELETON_UNLISTED file={name}")
        return categories

    def _read_skeleton_listing(self, listing: str) -> list[dict]:
        """Read and check skeletons.json; raise ThemeError naming the file."""
        try:
            with open(listing, encoding="utf-8") as fin:
                entries = json.load(fin)
        except (OSError, ValueError) as error:
            raise ThemeError(f"{listing}: cannot read skeletons.json: {error}") from error
        if not isinstance(entries, list):
            raise ThemeError(f"{listing}: must be a list of objects")
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise ThemeError(f"{listing}: every entry needs a string 'id'")
            if not SKELETON_ID.match(entry["id"]):
                raise ThemeError(f"{listing}: id '{entry['id']}' must match ^[a-z][a-z0-9-]*$")
            if entry["id"] in seen:
                raise ThemeError(f"{listing}: id '{entry['id']}' appears twice")
            seen.add(entry["id"])
            for key in ("name", "description", "color", "icon"):
                if key in entry and not isinstance(entry[key], str):
                    raise ThemeError(f"{listing}: '{key}' of id '{entry['id']}' must be a string")
        return entries
