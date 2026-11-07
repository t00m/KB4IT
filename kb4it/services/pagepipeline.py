"""Page facts every theme shares: the edit link and the page title."""

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
    """Mixin of Builder: the facts of a page that every theme needs."""

    # Title of a page whose document has no Title.
    untitled_label = ""

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

    def page_title(self, doc_id: str) -> str:
        """Title of a document page, or untitled_label when the document has none."""
        return self.srvdtb.get_doc_properties(doc_id).get("Title") or self.untitled_label
