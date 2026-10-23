"""The Add page (add.html) of the editor: the `editor` setting and its stale page."""

import json
import os
import re

from kb4it.core.env import ENV
from kb4it.core.exceptions import ConfigError, ThemeError

SUFFIX = "-SKELETON.md"
SKELETON_ID = re.compile(r"^[a-z][a-z0-9-]*$")


def check_editor_setting(repo: dict) -> None:
    """Raise ConfigError when repo.json 'editor' is set to anything but true or false."""
    if "editor" in repo and not isinstance(repo["editor"], bool):
        raise ConfigError("repo.json 'editor' must be true or false")


class AddPageMixin:
    """Builder part that decides whether the Add page exists and which skeletons it offers."""

    def editor_enabled(self) -> bool:
        """repo.json 'editor' when set, otherwise the theme default ("editor" in theme.json, false if missing)."""
        theme = self.srvbes.get_dict("theme") or {}
        repo = self.srvbes.get_dict("repo") or {}
        if "editor" in repo:
            return repo["editor"] is True
        return theme.get("editor") is True

    def remove_stale_add_page(self) -> None:
        """Remove add.html left by an earlier build from the target and the cache."""
        for folder in ("target", "cache"):
            path = os.path.join(self.srvbes.get_path(folder), "add.html")
            if os.path.exists(path):
                os.unlink(path)

    def log_add_page(self) -> None:
        """Log whether the Add page is built."""
        self.log.info(f"[BUILDER] ADD_PAGE enabled={self.editor_enabled()}")

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
        if os.path.exists(listing):
            entries = self._read_skeleton_listing(listing)
        else:
            entries = []
            for name in files:
                cat_id = name[:-len(SUFFIX)].lower()
                entries.append({"id": cat_id, "name": cat_id[:1].upper() + cat_id[1:]})
            entries.sort(key=lambda e: e["id"])
        categories = []
        for entry in entries:
            name = f"{entry['id'].upper()}{SUFFIX}"
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                raise ThemeError(f"{listing}: id '{entry['id']}' has no file {name}")
            with open(path, "rb") as fin:
                text = fin.read().decode("utf-8")
            categories.append({
                "id": entry["id"],
                "name": entry.get("name") or entry["id"][:1].upper() + entry["id"][1:],
                "description": entry.get("description") or "",
                "color": entry.get("color") or "",
                "icon": entry.get("icon") or "",
                "text": text,
            })
        if os.path.exists(listing):
            listed = {f"{c['id'].upper()}{SUFFIX}" for c in categories}
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
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise ThemeError(f"{listing}: every entry needs a string 'id'")
            if not SKELETON_ID.match(entry["id"]):
                raise ThemeError(f"{listing}: id '{entry['id']}' must match ^[a-z][a-z0-9-]*$")
        return entries
