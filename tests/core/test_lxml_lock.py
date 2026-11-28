"""lxml work of the compile threads runs one thread at a time (lxml 6.2.0 crashes on macOS otherwise)."""

import threading

import pytest

from kb4it.core.html import enhance_blocks, enhance_images
from kb4it.core.html.lxmllock import LXML_LOCK
from kb4it.core.search import extract_sections
from tests.helpers import ROOT

BODY = "<p>x</p><pre><code>print(1)</code></pre>"


def test_enhance_blocks_waits_for_the_lock():
    done = threading.Event()
    worker = threading.Thread(target=lambda: (enhance_blocks(BODY), done.set()))
    with LXML_LOCK:
        worker.start()
        assert not done.wait(0.3), "enhance_blocks ran while another thread held the lxml lock"
    worker.join(5)
    assert done.is_set()


@pytest.mark.parametrize("func", [enhance_blocks, enhance_images, extract_sections])
def test_core_html_functions_hold_the_lock(func):
    assert hasattr(func, "__wrapped__"), func.__name__


def test_bundled_themes_take_the_lock():
    techdoc = (ROOT / "kb4it/resources/themes/techdoc/logic/theme.py").read_text(encoding="utf-8")
    assert "with LXML_LOCK:" in techdoc
    apphelp = (ROOT / "kb4it/resources/themes/apphelp/logic/apphelp_html.py").read_text(encoding="utf-8")
    assert "@lxml_serialized\ndef transform(" in apphelp


def test_parallel_pages_give_the_same_html():
    expected = enhance_blocks(BODY)
    results = []
    threads = [threading.Thread(target=lambda: results.append(enhance_blocks(BODY))) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert results == [expected] * 8
