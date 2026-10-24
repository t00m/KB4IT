"""techdoc techdoc_media.py: image sizes, alt text rule and the rewrite of document images."""

import importlib.util
import struct

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
