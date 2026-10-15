"""PyMdown superfences: fences inside admonitions, highlighted the way the highlight mode says (OC-05, MD-03)."""

import pytest

from kb4it.core.mdconfig import load_settings

pytest.importorskip("pymdownx")

MD01 = "!!! note\n    ```python\n    y = 2\n    ```\n"


def _html(text, **block):
    settings = load_settings({"markdown": {"extensions": ["pymdownx.superfences"], **block}})
    return settings.new_markdown().convert(text)


def test_client_mode_gives_plain_language_classes():
    html = _html(MD01)
    assert '<code class="language-python">y = 2</code>' in html
    assert 'class="n"' not in html  # no Pygments markup
    assert 'class="admonition note"' in html


def test_none_mode_gives_plain_code_too():
    assert 'class="language-python"' in _html(MD01, highlight="none")


def test_pygments_mode_gives_pygments_markup():
    html = _html(MD01, highlight="pygments")
    assert '<div class="highlight">' in html and '<span class="n">y</span>' in html


def test_user_setting_wins():
    settings = load_settings({"markdown": {"extensions": ["pymdownx.superfences"],
                                           "extension_configs": {"pymdownx.highlight": {"use_pygments": True}}}})
    assert '<span class="n">y</span>' in settings.new_markdown().convert(MD01)


def test_without_superfences_nothing_changes():
    settings = load_settings({})
    assert "pymdownx.highlight" not in settings.all_configs()
    assert "pymdownx.highlight" not in [e for e in settings.all_extensions() if isinstance(e, str)]
