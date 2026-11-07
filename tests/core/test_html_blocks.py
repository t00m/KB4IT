"""Body rewrites shared by the themes (kb4it.core.html)."""

import lxml.html

from kb4it.core.html import enhance_blocks, enhance_images, lazy_images, wrap_code


def test_wrap_code_simple_markup():
    root = lxml.html.fragment_fromstring("<pre><code>x</code></pre>", create_parent="div")
    wrap_code(root.find("pre"), "ah-code", "ah-copy")
    assert lxml.html.tostring(root.find("div"), encoding="unicode") == \
        '<div class="ah-code"><button class="ah-copy" type="button">Copy</button><pre><code>x</code></pre></div>'


def test_lazy_images_sets_loading():
    root = lxml.html.fragment_fromstring('<p><img src="a.png"></p>', create_parent="div")
    lazy_images(root)
    assert root.find(".//img").get("loading") == "lazy"


def test_plain_body_passes_through():
    assert enhance_blocks("<p>Text.</p>") == "<p>Text.</p>"
    assert enhance_images("<p>Text.</p>", "/nowhere") == ("<p>Text.</p>", [])
