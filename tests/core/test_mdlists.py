"""Core Markdown extension: lists nested by two or three spaces nest, lists nested by four never change."""

import json
from pathlib import Path

import markdown
import pytest

from kb4it.core.mdconfig import BASE_EXTENSIONS, MarkdownSettings
from kb4it.core.mdlists import normalize_lists
from tests.helpers import ROOT

THEMES = ROOT / "kb4it" / "resources" / "themes"


def _html(text, **settings):
    return MarkdownSettings(**settings).new_markdown().convert(text)


def _plain(text):
    """What python-markdown alone makes of the text, with KB4IT's base extensions."""
    return markdown.markdown(text, extensions=BASE_EXTENSIONS)


# Written for python-markdown: four spaces per level, four more for code. These must not change.
FOUR_SPACES = {
    "nested": "- a\n    - b\n        - c\n- d\n",
    "code in an item": "1. Run:\n\n        ls -l\n\n2. Next\n",
    "note in an item": "- step\n\n    !!! note\n        Careful.\n\n- next\n",
    "flat list then text": "- a\n- b\n\ntext\n",
    "thematic breaks": "- - -\n\n* * *\n",
    "code after an item": "- a\n\n        code\n",
}


@pytest.mark.parametrize("text", FOUR_SPACES.values(), ids=FOUR_SPACES.keys())
def test_four_space_lists_render_as_python_markdown_does(text):
    assert normalize_lists(text.split("\n")) == text.split("\n")
    assert _html(text) == _plain(text)


def test_two_spaces_nest_every_level():
    html = _html("- a\n  - b\n    - c\n- d\n")
    assert html == _plain("- a\n    - b\n        - c\n- d\n")


def test_ordered_list_nested_by_three_spaces():
    html = _html("1. one\n   1. sub\n2. two\n")
    assert html == _plain("1. one\n    1. sub\n2. two\n")


def test_mixed_markers_and_a_one_space_sibling():
    assert _html("* a\n  + b\n    - c\n") == _plain("* a\n    + b\n        - c\n")
    # One space more is a sibling, as python-markdown reads it; two more is a child.
    assert normalize_lists(["- a", " - b", "  - c"]) == ["- a", " - b", "  - c"]
    assert normalize_lists(["- a", " - b", "   - c"]) == ["- a", "- b", "    - c"]


def test_content_of_a_two_space_item_moves_with_it():
    html = _html("- a\n  - b\n\n        code under b\n\n    !!! note\n        Careful.\n")
    assert "<pre><code>code under b\n</code></pre>" in html
    assert '<div class="admonition note">' in html
    assert html.index("<ul>", 1) < html.index("code under b")  # inside the nested list


def test_fenced_lines_keep_their_inner_indentation():
    lines = ["- a", "  - b", "", "    ```", "    x = 1", "      y", "    ```", "    - not an item"]
    out = normalize_lists(lines)
    assert out[3:7] == ["        ```", "        x = 1", "          y", "        ```"]
    assert out[7] == "        - not an item"  # text of b, after the fence


def test_list_ends_at_unindented_text_after_a_blank_line():
    lines = ["- a", "  - b", "", "Text.", "", "  - not moved"]
    assert normalize_lists(lines) == ["- a", "    - b", "", "Text.", "", "  - not moved"]


def test_lazy_continuation_and_nested_task_list():
    pytest.importorskip("pymdownx")
    assert normalize_lists(["- a", "wrapped", "  - b"]) == ["- a", "wrapped", "    - b"]
    html = _html("- [ ] a\n  - [x] b\n", extensions=["pymdownx.tasklist"])
    assert html.count('<ul class="task-list">') == 2
    assert html.index("checked") > html.index('<ul class="task-list">', 1)


def test_help_sources_are_left_alone():
    """The help is written with four spaces: the rewrite never touches it."""
    for path in sorted((ROOT / "help" / "source").glob("*.md")):
        lines = path.read_text(encoding="utf-8").expandtabs(4).split("\n")
        assert normalize_lists(lines) == lines, path.name


@pytest.mark.parametrize("config", sorted(THEMES.glob("*/apps/*/config/repo.json")),
                         ids=lambda p: f"{p.parents[3].name}-{p.parents[1].name}")
def test_sample_apps_turn_on_task_lists(config):
    assert "pymdownx.tasklist" in json.loads(config.read_text(encoding="utf-8"))["markdown"]["extensions"]


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_themes_style_task_lists(theme):
    css = "".join(p.read_text(encoding="utf-8") for p in (THEMES / theme).rglob("*.css") if "uikit" not in p.parts)
    assert "li.task-list-item { list-style-type: none; }" in css


def test_fenced_code_outside_a_list_is_never_rewritten():
    lines = ["```markdown", "- a", "  - b", "```", "", "- c", "  - d"]
    assert normalize_lists(lines) == ["```markdown", "- a", "  - b", "```", "", "- c", "    - d"]
