"""No Python module of KB4IT is over 600 lines (AR-02, ARC-02)."""

from tests.helpers import ROOT

MAX_LINES = 600


def test_no_module_over_600_lines():
    package = ROOT / "kb4it"
    too_long = {}
    for path in sorted(package.rglob("*.py")):
        if "framework" in path.relative_to(package).parts:  # bundled third-party files of the themes
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > MAX_LINES:
            too_long[str(path.relative_to(ROOT))] = lines
    assert too_long == {}, "split these modules by concern"
