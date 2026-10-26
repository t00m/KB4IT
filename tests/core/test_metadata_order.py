"""kbdict.json lists the values of a document sorted and without repeats, and the documents of a value sorted
without regard to case."""

import json

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_kbdict_values_and_documents_are_sorted(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    pages = {
        "beta.md": page("Beta", Date="2026-01-02", Tag="zeta, alpha, zeta, Mid"),
        "Alpha.md": page("Alpha", Date="2026-01-01", Tag="alpha, alpha"),
        "gamma.md": page("Gamma", Date="2026-01-03", Tag="Mid, alpha"),
        "ALPHA2.md": page("Alpha 2", Date="2026-01-04", Tag="alpha"),
    }
    cfg = write_repo(repo, "mini", pages, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    kbdict = json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))

    assert kbdict["document"]["beta.md"]["Tag"] == ["Mid", "alpha", "zeta"]
    assert kbdict["document"]["Alpha.md"]["Tag"] == ["alpha"]
    tags = kbdict["metadata"]["Tag"]
    assert tags["alpha"] == sorted(tags["alpha"], key=str.lower)
    assert {d.lower() for d in tags["alpha"]} == {"alpha.md", "alpha2.md", "beta.md", "gamma.md"}
    assert tags["Mid"] == ["beta.md", "gamma.md"]
    assert set(tags["zeta"]) == {"beta.md"}
