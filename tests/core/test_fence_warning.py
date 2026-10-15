"""kb4it verify warns about fences python-markdown cannot see without superfences (OC-05, MD-01)."""

import pytest

from kb4it.core.util import fences_in_blocks
from tests.helpers import page, run_kb4it, write_repo

MD01 = "!!! note\n    ```python\n    y = 2\n    ```\n"


def test_fences_in_blocks():
    assert fences_in_blocks(MD01) == [2, 4]
    assert fences_in_blocks("\t~~~\n\tx\n\t~~~\n") == [1, 3]
    assert fences_in_blocks("```\n    ```\n```\n") == []  # inside a top-level fence it is code
    assert fences_in_blocks("    code\n\n```bash\nls\n```\n") == []


def test_verify_warns_without_superfences(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"note.md": page("Note", MD01, Tag="x")})
    result = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout  # a warning, not a failure
    lines = (tmp_path / "repo" / "source" / "note.md").read_text(encoding="utf-8").splitlines()
    fences = [str(n) for n, line in enumerate(lines, start=1) if line.strip().startswith("```")]
    assert f"MD_FENCE_IN_BLOCK doc=note.md lines={','.join(fences)}" in result.stdout


def test_verify_is_quiet_with_superfences(tmp_path, home):
    pytest.importorskip("pymdownx")
    cfg = write_repo(tmp_path / "repo", "techdoc", {"note.md": page("Note", MD01, Tag="x")},
                     markdown={"extensions": ["pymdownx.superfences"]})
    result = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "MD_FENCE_IN_BLOCK" not in result.stdout


def test_superfences_renders_the_md01_example_in_both_modes(tmp_path, home):
    pytest.importorskip("pymdownx")
    for mode in ("client", "pygments"):
        repo = tmp_path / mode
        cfg = write_repo(repo, "techdoc", {"note.md": page("Note", MD01, Tag="x")},
                         markdown={"extensions": ["pymdownx.superfences"], "highlight": mode})
        assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
        html = (repo / "target" / "note.html").read_text(encoding="utf-8")
        assert "<code>python" not in html and "<pre" in html, mode
