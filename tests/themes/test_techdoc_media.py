"""techdoc techdoc_media.py: image sizes, alt text rule and the rewrite of document images."""

import importlib.util
import struct

import pytest

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location(
    "techdoc_media", ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic" / "techdoc_media.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


def png(w, h):
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", w, h) + b"\x08\x02\x00\x00\x00" + b"\x00" * 4


def jpeg(w, h):
    return (b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
            + b"\xff\xc0" + struct.pack(">HBHH", 17, 8, h, w) + b"\x00" * 10)


def gif(w, h):
    return b"GIF89a" + struct.pack("<HH", w, h) + b"\x00" * 7


def test_image_size_reads_png_jpeg_gif_and_svg(tmp_path):
    for name, data, size in (("a.png", png(1100, 480), (1100, 480)), ("b.jpg", jpeg(640, 360), (640, 360)),
                             ("c.gif", gif(32, 16), (32, 16)),
                             ("d.svg", b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 420"></svg>', (900, 420)),
                             ("e.svg", b'<svg xmlns="http://www.w3.org/2000/svg" width="120px" height="40" viewBox="0 0 1 1"></svg>', (120, 40))):
        (tmp_path / name).write_bytes(data)
        assert media.image_size(str(tmp_path / name)) == size


def test_image_size_is_none_for_unknown_or_broken_files(tmp_path):
    (tmp_path / "x.png").write_bytes(b"not an image")
    assert media.image_size(str(tmp_path / "x.png")) is None
    assert media.image_size(str(tmp_path / "missing.png")) is None


def test_filename_like_alt_texts():
    assert media.is_filename_alt("SAP-BC-SC-DMS-00", "resources/images/SAP-BC-SC-DMS-00.png")
    assert media.is_filename_alt("image12", "x.png")
    assert media.is_filename_alt("", "x.png")
    assert media.is_filename_alt("Shot", "resources/images/shot.png")
    assert not media.is_filename_alt("Transaction SU01 with the user list", "x.png")
    assert not media.is_filename_alt("Diagram", "x.png")


def test_resolve_src(tmp_path):
    assert media.resolve_src("resources/images/my%20shot.png", str(tmp_path)) == str(tmp_path / "resources/images/my shot.png")
    for src in ("https://x.org/a.png", "http://x.org/a.png", "data:image/png;base64,AA", "//x.org/a.png", "/abs/a.png"):
        assert media.resolve_src(src, str(tmp_path)) is None


@pytest.fixture
def site(tmp_path):
    images = tmp_path / "resources" / "images"
    images.mkdir(parents=True)
    (images / "wide.png").write_bytes(png(1100, 480))
    (images / "icon.png").write_bytes(png(16, 16))
    for i in (1, 2, 3):
        (images / f"s{i}.png").write_bytes(png(900, 420))
    return tmp_path


def test_block_image_becomes_numbered_figure_with_lightbox_link(site):
    html, missing = media.enhance_images('<p><img alt="User list in SU01" src="resources/images/wide.png"></p>', str(site))
    assert missing == []
    assert '<figure class="kb-figure"><a class="kb-zoom" href="resources/images/wide.png" data-caption="User list in SU01">' in html
    assert 'class="kb-shot"' in html and 'width="1100"' in html and 'height="480"' in html
    assert "<figcaption>Figure 1. User list in SU01</figcaption>" in html
    assert "loading=" not in html            # the first image loads at once


def test_file_name_alt_gets_no_caption_and_second_image_is_lazy(site):
    html, _ = media.enhance_images('<p><img alt="x" src="resources/images/icon.png"></p><p><img alt="SAP-BC-00" src="resources/images/wide.png"></p>', str(site))
    assert "<figcaption>" not in html
    assert html.count('loading="lazy"') == 1 and 'decoding="async"' in html


def test_small_linked_and_inline_images_are_left_alone(site):
    for body in ('<p><img alt="Icon here" src="resources/images/icon.png"></p>',
                 '<p><a href="x.html"><img alt="Big link" src="resources/images/wide.png"></a></p>',
                 '<p>Click <img alt="the button" src="resources/images/wide.png"> to go on.</p>'):
        html, _ = media.enhance_images(body, str(site))
        assert "<figure" not in html and "kb-zoom" not in html


def test_three_images_in_a_row_make_a_gallery(site):
    body = "".join(f'<p><img alt="Step {i} of the wizard" src="resources/images/s{i}.png"></p>' for i in (1, 2, 3))
    html, _ = media.enhance_images(body, str(site))
    assert html.count('<div class="kb-gallery uk-child-width-1-2 uk-child-width-1-3@m" data-uk-grid="masonry: false">') == 1
    assert html.count('<figure class="kb-figure">') == 3
    two, _ = media.enhance_images(body.rsplit("<p>", 1)[0], str(site))
    assert "kb-gallery" not in two


def test_missing_images_become_placeholders(site):
    html, missing = media.enhance_images('<p><img alt="Gone" src="resources/images/gone.png"></p><p>See <img alt="g" src="resources/images/g2.png"> here.</p>', str(site))
    assert missing == ["resources/images/gone.png", "resources/images/g2.png"]
    assert '<figure class="kb-figure kb-img-missing">Image missing: <code>resources/images/gone.png</code></figure>' in html
    assert '<span class="kb-img-missing">Image missing: <code>resources/images/g2.png</code></span>' in html
    assert "<p><figure" not in html


def test_remote_images_are_never_missing(site):
    html, missing = media.enhance_images('<p><img alt="Remote diagram" src="https://x.org/a.png"></p>', str(site))
    assert missing == [] and 'href="https://x.org/a.png"' in html and "width=" not in html


def test_text_and_other_markup_are_kept(site):
    body = '<h2 id="s">Steps</h2><p>Run <code>a &lt; b</code>.</p><pre><code class="language-bash">ls</code></pre>'
    assert media.enhance_images(body, str(site)) == (body, [])


def test_bare_image_outside_a_paragraph_becomes_a_figure(site):
    html, _ = media.enhance_images('<h2>A</h2><img alt="Bare diagram here" src="resources/images/wide.png">\nafter', str(site))
    assert html.startswith('<h2>A</h2><figure class="kb-figure">') and html.endswith("</figure>\nafter")


def test_missing_bare_image_is_replaced(site):
    html, missing = media.enhance_images('<img alt="Gone diagram" src="resources/images/gone.png">', str(site))
    assert missing == ["resources/images/gone.png"] and "<img" not in html
