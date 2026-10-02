import re

import pytest

from tests.helpers import APPHELP

CSS = (APPHELP / "framework" / "apphelp" / "css" / "apphelp.css").read_text(encoding="utf-8")
PAIRS = [("ah-fg", "ah-bg"), ("ah-fg", "ah-bg-alt"), ("ah-muted", "ah-bg"), ("ah-muted", "ah-bg-alt"),
         ("ah-link", "ah-bg"), ("ah-link", "ah-bg-alt"), ("ah-fg", "ah-chip-bg"), ("ah-link", "ah-chip-bg"),
         ("ah-fg", "ah-code-bg")]


def block(selector):
    match = re.search(r"(?m)^\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert match, selector
    return dict(re.findall(r"--(ah-[a-z-]+):\s*(#[0-9a-fA-F]{6})", match.group(1)))


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


LIGHT = block(":root")
DARK = {**LIGHT, **block(':root[data-theme="dark"]')}


@pytest.mark.parametrize("scheme", [LIGHT, DARK], ids=["light", "dark"])
@pytest.mark.parametrize("fg, bg", PAIRS)
def test_contrast_aa(scheme, fg, bg):
    assert ratio(scheme[fg], scheme[bg]) >= 4.5, (fg, bg, scheme[fg], scheme[bg])


def test_media_query_dark_matches_forced_dark():
    assert block(':root:not([data-theme="light"])') == block(':root[data-theme="dark"]')


def test_no_external_resources():
    assert not re.search(r"url\(\s*['\"]?(https?:)?//", CSS)
    assert "@import" not in CSS


def test_print_resets_light_tokens():
    match = re.search(r"@media print \{(.*?)\n\}", CSS, re.S)
    assert match
    tokens = dict(re.findall(r"--(ah-[a-z-]+):\s*(#[0-9a-fA-F]{6})", match.group(1)))
    assert tokens["ah-fg"] == "#1e1e1e"
    assert tokens["ah-bg"] == "#ffffff"
