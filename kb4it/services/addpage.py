"""The Add page (add.html) of the editor: the `editor` setting and its stale page."""

import os

from kb4it.core.exceptions import ConfigError


def check_editor_setting(repo: dict) -> None:
    """Raise ConfigError when repo.json 'editor' is set to anything but true or false."""
    if "editor" in repo and not isinstance(repo["editor"], bool):
        raise ConfigError("repo.json 'editor' must be true or false")


class AddPageMixin:
    """Builder part that decides whether the Add page exists."""

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
