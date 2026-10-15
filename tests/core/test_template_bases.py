"""Template bases: templates that several themes share, chosen with "template_base" in theme.json (AR-01)."""

import os

import pytest

from kb4it.core.exceptions import ThemeError
from kb4it.services import builder
from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_lookup_order_with_a_base():
    paths = builder._template_candidates("X", "/theme", "/common", "/repo/overrides", "/base")
    assert paths == [os.path.join("/repo/overrides", "templates", "X.tpl"), os.path.join("/theme", "X.tpl"),
                     os.path.join("/base", "X.tpl"), os.path.join("/common", "X.tpl")]


def test_lookup_order_without_a_base_is_unchanged():
    assert builder._template_candidates("X", "/theme", "/common") == [os.path.join("/theme", "X.tpl"),
                                                                       os.path.join("/common", "X.tpl")]


def test_template_base_dir(tmp_path, monkeypatch):
    (tmp_path / "shared" / "templates").mkdir(parents=True)
    monkeypatch.setattr(builder, "ENV", {"GPATH": {"BASES": str(tmp_path)}})
    assert builder.template_base_dir({}) is None
    assert builder.template_base_dir({"template_base": "shared"}) == str(tmp_path / "shared" / "templates")
    for bad in ("nope", "../shared", "", 3):
        with pytest.raises(ThemeError, match="template_base"):
            builder.template_base_dir({"template_base": bad})


def test_unknown_base_stops_the_build(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", template_base="no-such-base")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "'template_base' 'no-such-base' is not one of" in result.stdout
