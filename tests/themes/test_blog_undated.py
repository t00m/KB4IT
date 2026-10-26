"""A blog post without Date does not stop the blog (OC-04), and unexpected errors name their type."""

import sys

from kb4it.core import main as kb4it_main
from tests.helpers import page, run_kb4it


def test_undated_post_builds_and_is_listed_last(tmp_path, home):
    """The audit reproduction of COR-08: exit 1 with only "Error: 'Date'"."""
    repo = tmp_path / "blog"
    assert run_kb4it("create", "blog", repo, cwd=tmp_path, home=home).returncode == 0
    source = repo / "source"
    excerpt = "## Excerpt\n\nShort.\n\n## Body\n\nText."
    # By name the undated post would come first; by date it must come last.
    (source / "aa-undated.md").write_text(page("Undated post", excerpt, Category="Post", Tag="misc"), encoding="utf-8")
    (source / "zz-dated.md").write_text(page("Dated post", excerpt, Category="Post", Tag="misc", Date="2026-01-01"),
                                        encoding="utf-8")
    result = run_kb4it("build", repo / "config" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    warnings = [line for line in result.stdout.splitlines() if "DOC_UNDATED" in line]
    assert len(warnings) == 1 and "doc=aa-undated.md" in warnings[0]
    target = repo / "target"
    index = (target / "index.html").read_text(encoding="utf-8")
    assert 0 <= index.find("Dated post") < index.find("Undated post")
    post = (target / "aa-undated.html").read_text(encoding="utf-8")
    assert "events_.html" not in post and 'data-uk-icon="calendar"' not in post
    assert 'data-uk-icon="calendar"' in (target / "zz-dated.html").read_text(encoding="utf-8")


def test_unexpected_error_names_type_and_log(tmp_path, monkeypatch, capsys):
    config = tmp_path / "repo" / "config" / "repo.json"
    log_file = tmp_path / "repo" / "var" / "log" / "kb4it.log"
    log_file.parent.mkdir(parents=True)
    config.parent.mkdir(parents=True)
    config.write_text("{}", encoding="utf-8")
    log_file.write_text("", encoding="utf-8")

    class Boom:
        def __init__(self, params):
            pass

        def run(self):
            raise KeyError("Date")

    monkeypatch.setattr(kb4it_main, "KB4IT", Boom)
    monkeypatch.setattr(sys, "argv", ["kb4it", "build", str(config)])
    try:
        kb4it_main.main()
    except SystemExit as exit_:
        assert exit_.code == 1
    out = capsys.readouterr().out
    assert f"Error: KeyError: 'Date' (see {log_file})" in out
