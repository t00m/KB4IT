"""Markup of the sample sites: valid structure and accessible basics (HT-01, HT-02)."""

import re
import shutil

import pytest

from tests.helpers import FIXTURES, run_kb4it

THEMES = ["techdoc", "blog", "bookshelf", "apphelp"]

# The COR-07 and MD-01 documents of the audit, next to the rich and hostile fixtures.
EXTRA_DOCS = {
    "cor07.md": "---\nTag: code\n---\n\n```bash\n# install the tool\napt install x\n```\n\n# Real title\n\nText.\n",
    "md01.md": "---\nTag: code\n---\n\n# Note with code\n\n!!! note\n    ```python\n    y = 2\n    ```\n",
}

START_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)((?:\s+[^\s=>/\"']+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>\"']+))?)*)\s*/?>")
ATTRIBUTE = re.compile(r"([^\s=>/\"']+)(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>\"']+))?")


@pytest.fixture(scope="module")
def sites(tmp_path_factory):
    base = tmp_path_factory.mktemp("sites")
    home = base / "home"
    home.mkdir()
    built = {}
    for theme in THEMES:
        repo = base / theme
        assert run_kb4it("create", theme, repo, cwd=base, home=home).returncode == 0
        if theme != "apphelp":
            for doc in (FIXTURES / "audit").glob("*.md"):
                shutil.copy(doc, repo / "source" / doc.name)
            for name, text in EXTRA_DOCS.items():
                (repo / "source" / name).write_text(text, encoding="utf-8")
        result = run_kb4it("build", repo / "config" / "repo.json", cwd=base, home=home)
        assert result.returncode == 0, result.stdout
        built[theme] = sorted((repo / "target").glob("*.html"))
    return built


def _start_tags(page):
    text = re.sub(r"<!--.*?-->|<script\b.*?</script>|<textarea\b.*?</textarea>", "", page.read_text(encoding="utf-8"),
                  flags=re.DOTALL)
    for match in START_TAG.finditer(text):
        yield match.group(1).lower(), [m.group(1).lower() for m in ATTRIBUTE.finditer(match.group(2))], match.group(0)


@pytest.mark.parametrize("theme", THEMES)
def test_no_empty_target_and_no_duplicate_attribute(sites, theme):
    problems = []
    for page in sites[theme]:
        for tag, names, raw in _start_tags(page):
            if len(names) != len(set(names)):
                problems.append(f"{page.name}: duplicate attribute in {raw[:120]}")
        if 'target=""' in page.read_text(encoding="utf-8"):
            problems.append(f'{page.name}: target=""')
    assert problems == []
