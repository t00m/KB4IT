"""Markup of the sample sites: valid structure and accessible basics (HT-01, HT-02)."""

import json
import re
import shutil

import pytest
from lxml import html as lxml_html

from kb4it.services.builder import git_ready
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



@pytest.mark.parametrize("theme", THEMES)
def test_section_blocks_use_classes(sites, theme):
    """Every document section is a block of its own: no fixed id repeated per section."""
    problems = [page.name for page in sites[theme]
                if re.search(r'id="kb-sect[1-4]"|id="kb-section-body"', page.read_text(encoding="utf-8"))]
    assert problems == []


def _markup(page):
    """Page text without comments, scripts and textareas, whose content is not markup."""
    return re.sub(r"<!--.*?-->|<script\b.*?</script>|<textarea\b.*?</textarea>", "", page.read_text(encoding="utf-8"),
                  flags=re.DOTALL)


@pytest.mark.parametrize("theme", THEMES)
def test_no_duplicate_id(sites, theme):
    problems = []
    for page in sites[theme]:
        ids = re.findall(r'\sid="([^"]*)"', _markup(page))
        repeated = sorted({i for i in ids if ids.count(i) > 1})
        if repeated:
            problems.append(f"{page.name}: {repeated}")
    assert problems == []


@pytest.mark.parametrize("theme", THEMES)
def test_valid_structure(sites, theme):
    """The errors the Nu HTML Checker found in Phase 6, checked without Java."""
    problems = []
    for page in sites[theme]:
        text = _markup(page)
        opened, closed = len(re.findall(r"<div\b", text)), len(re.findall(r"</div>", text))
        if opened != closed:
            problems.append(f"{page.name}: {opened} <div> and {closed} </div>")
        if re.search(r'\s(?:width|height)="\d+px"', text):
            problems.append(f"{page.name}: width or height in px")
        if re.search(r"<span\b[^>]*>\s*<div\b", text):
            problems.append(f"{page.name}: div inside span")
        if re.search(r"<ul\b[^>]*>\s*<ul\b", text):
            problems.append(f"{page.name}: ul inside ul")
        if re.search(r"<div\b[^>]*>\s*<style\b", text) or re.search(r"<body\b.*<style\b", text, re.DOTALL):
            problems.append(f"{page.name}: style element in the body")
    assert problems == []


@pytest.mark.parametrize("theme", THEMES)
def test_accessible_basics(sites, theme):
    """lang, exactly one h1, a real alt on every image, a main landmark, no placeholder links (HT-02)."""
    problems = []
    for page in sites[theme]:
        tree = lxml_html.fromstring(page.read_bytes())
        if not tree.get("lang"):
            problems.append(f"{page.name}: no lang")
        if len(tree.findall(".//h1")) != 1:
            problems.append(f"{page.name}: {len(tree.findall('.//h1'))} h1")
        for img in tree.iter("img"):
            if img.get("alt") is None or "{" in img.get("alt"):
                problems.append(f"{page.name}: img {img.get('src')} alt={img.get('alt')!r}")
        if tree.find(".//main") is None:
            problems.append(f"{page.name}: no main")
        if 'href="{' in page.read_text(encoding="utf-8"):
            problems.append(f'{page.name}: href="{{...}}"')
    assert problems == []


def test_git_ready():
    full = {"git": True, "git_server": "https://github.com", "git_user": "me", "git_repo": "kb",
            "git_branch": "main", "git_path": "source"}
    assert git_ready(full)
    assert git_ready({**full, "git_path": ""})  # documents at the repository root
    assert not git_ready({**full, "git": False})
    assert not git_ready({k: v for k, v in full.items() if k != "git_user"})
    assert not git_ready({**full, "git_server": "{https://{server.fqdn}"})


@pytest.mark.parametrize("theme", ["techdoc", "blog"])  # bookshelf shows no page actions
def test_edit_link_when_git_is_set(tmp_path, home, theme):
    repo = tmp_path / theme
    assert run_kb4it("create", theme, repo, cwd=tmp_path, home=home).returncode == 0
    shutil.copy(FIXTURES / "audit" / "rich.md", repo / "source" / "rich.md")
    cfg = repo / "config" / "repo.json"
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf.update(git=True, git_server="https://github.com", git_user="me", git_repo="kb", git_branch="main",
                git_path="source")
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "https://github.com/me/kb/edit/main/source/rich.md" in (repo / "target" / "rich.html").read_text(encoding="utf-8")
