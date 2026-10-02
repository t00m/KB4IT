import json

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def test_undated_documents_are_kept(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {
        "a.md": page("A", Date="2026-01-02"),
        "b.md": page("B", Tag="x"),
        "c.md": page("C", Date="2026-01-01"),
        "d.md": page("D", Tag="y"),
    }, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    docs = json.loads((repo / "target" / "documents.json").read_text())
    assert docs == ["a.md", "c.md", "b.md", "d.md"]
    assert "DATE_INVALID" not in result.stdout


def test_techdoc_datatable_lists_undated_documents(tmp_path, home):
    result = run_kb4it("create", "techdoc", "newrepo", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    repo = tmp_path / "newrepo"
    (repo / "source" / "undated.md").write_text(page("Undated", Category="Misc"), encoding="utf-8")
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "all.html").read_text(encoding="utf-8")
    assert "undated.html" in html
    assert html.count("<tr") == html.count("</tr>")
