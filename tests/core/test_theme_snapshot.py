"""scripts/devel/theme_snapshot.py --content: stable, normalised page copies for before/after diffs."""

import importlib.util

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("theme_snapshot", ROOT / "scripts" / "devel" / "theme_snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def test_normalise_hides_build_dates_times_and_version():
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    text = f"Built 2026-10-15 09:41:07 by KB4IT {version} on Oct 15, 2026 at 10:00:01"
    out = snapshot.normalise(text)
    assert version not in out and "09:41" not in out and "10:00:01" not in out
    assert "<VERSION>" in out and "<DATETIME>" in out


def test_normalise_keeps_document_dates():
    assert snapshot.normalise("Date: 2026-10-14") == "Date: 2026-10-14"


def test_fixtures_exist():
    names = {p.name for p in snapshot.FIXTURES.glob("*.md")}
    assert {"rich.md", "hostile.md"} <= names


def test_every_app_is_snapshotted_with_content():
    pairs = list(snapshot.apps(content=True))
    assert ("techdoc", "sapbasis") in pairs and ("apphelp", "default") in pairs
    assert list(snapshot.apps(content=False)) == [p for p in pairs if p[1] == "default" and p[0] != "apphelp"]


def test_normalise_maps_old_and_new_vendor_paths_to_one_token():
    pairs = [("resources/themes/techdoc/framework/Highlight/highlight.js", "resources/vendor/highlight/highlight.js"),
             ("resources/themes/blog/framework/uikit/css/uikit.min.css", "resources/vendor/uikit/css/uikit.min.css"),
             ("resources/themes/techdoc/framework/datatables/js/x.js", "resources/vendor/datatables/js/x.js"),
             ("resources/common/js/kb4it-search.js", "resources/vendor/search/js/kb4it-search.js"),
             ("resources/common/css/kb4it-search.css", "resources/vendor/search/css/kb4it-search.css"),
             ("resources/themes/apphelp/framework/apphelp/js/search.js", "resources/vendor/search/js/kb4it-search.js")]
    for old, new in pairs:
        assert snapshot.normalise(f'src="{old}"') == snapshot.normalise(f'src="{new}"'), (old, new)
    assert snapshot.normalise('src="resources/themes/techdoc/framework/kb4it/js/page.js"') == \
        'src="resources/themes/techdoc/framework/kb4it/js/page.js"', "a theme's own files keep their path"


def test_normalise_maps_the_moved_kit_scripts():
    for old, new in (("resources/themes/techdoc/framework/kb4it/js/datatable-filter.js",
                      "resources/vendor/tablefilter/js/datatable-filter.js"),):
        assert snapshot.normalise(f'src="{old}"') == snapshot.normalise(f'src="{new}"'), (old, new)
