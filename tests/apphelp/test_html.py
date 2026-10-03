import re

import markdown

from apphelp_config import DEFAULT_LABELS
from apphelp_html import transform
from kb4it.services.compiler import _md_toc_block, _restructure_md_sections


def compile_md(text):
    md = markdown.Markdown(extensions=["extra", "admonition", "toc", "sane_lists"])
    html = md.convert(text)
    toc = _md_toc_block(md.toc)
    return _restructure_md_sections(toc + "\n" + html if toc else html)


def test_toc_block_removed_and_toc_returned():
    html, toc = transform(compile_md("Intro.\n\n## One {#one}\n\nA\n\n### Sub\n\nB\n\n## Two\n\nC\n"), "howto")
    assert 'id="toc"' not in html
    assert toc == [{"level": 2, "id": "one", "text": "One"},
                   {"level": 3, "id": "sub", "text": "Sub"},
                   {"level": 2, "id": "two", "text": "Two"}]
    assert html.startswith("<p>Intro.</p>")


def test_images_and_code():
    html, _ = transform(compile_md("![x](resources/a.png)\n\n```\nls -l\n```\n\nafter\n"), "howto")
    assert 'loading="lazy"' in html
    assert '<div class="ah-code"><button class="ah-copy" type="button">Copy</button><pre>' in html
    assert "after" in html


def test_faq_becomes_details():
    html, toc = transform(compile_md("## Where is it? {#where}\n\nHere.\n\n## Why? {#why}\n\nBecause.\n"), "reference", "faq")
    assert '<details class="ah-faq" id="where"><summary>Where is it?</summary>' in html
    assert '<div class="ah-faq-answer"><p>Here.</p></div></details>' in re.sub(r">\s+<", "><", html)
    assert "<h2" not in html
    assert [t["id"] for t in toc] == ["where", "why"]


def test_troubleshooting_classes():
    text = "## Empty list {#empty}\n\n### Cause\n\nNo repo.\n\n### Fix\n\nCreate one.\n"
    html, _ = transform(compile_md(text), "howto", "troubleshooting", DEFAULT_LABELS)
    assert '<h3 id="cause" class="ah-cause">' in html or '<h3 class="ah-cause" id="cause">' in html
    assert "ah-fix" in html


def test_tutorial_prerequisite_note():
    html, _ = transform(compile_md("!!! note \"What you need\"\n    An account.\n\n## Step\n\nGo.\n"), "tutorial")
    assert "admonition note ah-prereq" in html


def test_empty_fragment():
    assert transform("", "howto") == ("", [])
