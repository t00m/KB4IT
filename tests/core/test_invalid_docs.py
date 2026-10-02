import json

import pytest

from kb4it.core.util import get_document_attributes
from tests.helpers import mini_theme, page, run_kb4it, write_repo

BROKEN = "---\nFeature: Docs\nKind: howto\nOrder: 20\nSection: Start\nSummary: Broken: a colon inside the value.\n---\n\n# Broken page\n"


@pytest.mark.parametrize("text, reason", [
    (BROKEN, "yaml_error line=6 col=16 mapping values are not allowed here"),
    ("# No frontmatter\n", "missing_frontmatter"),
    ("---\nTag: a\n\n# Never closed\n", "missing_frontmatter_close"),
    ("---\n- a\n- b\n---\n\n# A list\n", "invalid_frontmatter"),
])
def test_invalid_reasons(tmp_path, text, reason):
    path = tmp_path / "doc.md"
    path.write_text(text, encoding="utf-8")
    keys, valid, got = get_document_attributes(str(path))
    assert (keys, valid, got) == ({}, False, reason)


def _mini_build(tmp_path, home, command="build", **config):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"good.md": page("Good", Date="2026-01-01"), "broken.md": BROKEN},
                     theme_path=str(theme), **config)
    return repo, run_kb4it(command, cfg, cwd=repo, home=home)


def test_invalid_document_is_reported_in_summary(tmp_path, home):
    repo, result = _mini_build(tmp_path, home)
    assert result.returncode == 0, result.stdout
    assert "DOC_INVALID doc=broken.md reason=yaml_error line=6 col=16" in result.stdout
    assert "docs_total=2 compiled=1 skipped=0 invalid=1" in result.stdout
    assert json.loads((repo / "target" / "documents.json").read_text()) == ["good.md"]


def test_fail_on_invalid_stops_the_build(tmp_path, home):
    _repo, result = _mini_build(tmp_path, home, fail_on_invalid=True)
    assert result.returncode != 0
    assert "1 invalid document(s)" in result.stdout
    assert "broken.md" in result.stdout


def test_verify_exits_1_with_an_invalid_document(tmp_path, home):
    _repo, result = _mini_build(tmp_path, home, command="verify")
    assert result.returncode == 1, result.stdout
    assert "broken.md" in result.stdout


def test_verify_exits_0_when_everything_is_valid(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"good.md": page("Good", Date="2026-01-01")}, theme_path=str(theme))
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "All source documents are conformant." in result.stdout
