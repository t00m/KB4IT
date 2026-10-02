import json
import re

from tests.helpers import page, run_kb4it, write_repo

VOCAB = {"Feature": ["Backup", "Rename", "Import & export"], "Level": ["basic", "advanced"]}


def help_page(title, body="Text.", **keys):
    base = {"Kind": "howto", "Section": "How-to", "Order": "10", "Summary": "A summary.", "Feature": "Backup"}
    base.update(keys)
    return page(title, body, **base)


def build(tmp_path, home, pages, strict=True, **config):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "apphelp", pages, publish_sources=False,
                     apphelp={"strict": strict, "vocabulary": VOCAB}, **config)
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    return repo, result


def test_basic_site(tmp_path, home):
    repo, result = build(tmp_path, home, {
        "backup.md": help_page("Back up", "## Restore {#restore}\n\nSee [rename](rename.md#how).",
                               HelpId="backup-dialog=#restore"),
        "rename.md": help_page("Rename", "## How {#how}\n\nSteps.", Feature="Rename", Order="20"),
    })
    assert result.returncode == 0, result.stdout
    target = repo / "target"
    for name in ("index.html", "topics.html", "search.html", "go.html", "404.html",
                 "backup.html", "rename.html", ".nojekyll", "search-index.js", "helpids.js"):
        assert (target / name).exists(), name
    for name in ("Kind.html", "Feature.html", "Feature_Backup.html", "all.html", "stats.html"):
        assert not (target / name).exists(), name
    backup = (target / "backup.html").read_text()
    assert 'href="rename.html#how"' in backup
    assert 'href="topics.html#feature-backup"' in backup
    assert 'aria-current="page"' in backup
    assert "ah-related" in backup
    assert "window.APPHELP_HELPIDS" in (target / "helpids.js").read_text()
    assert '"backup-dialog": "backup.html#restore"' in (target / "helpids.js").read_text()
    assert not (target / "sources").exists()
    assert not list(target.rglob("*.py"))


def test_special_characters_are_escaped(tmp_path, home):
    repo, result = build(tmp_path, home, {
        "io.md": help_page("Use <kbd> & \"quotes\" en camión", Feature="Import & export",
                           Summary="Move data in & out."),
    })
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "io.html").read_text()
    assert "Use &lt;kbd&gt; &amp; &#34;quotes&#34; en camión" in html or \
           "Use &lt;kbd&gt; &amp; &quot;quotes&quot; en camión" in html
    assert 'href="topics.html#feature-import-export"' in html
    assert 'id="feature-import-export"' in (repo / "target" / "topics.html").read_text()
    assert "ANCHOR_MISSING" not in result.stdout


def test_strict_metadata_failure_lists_every_problem(tmp_path, home):
    bad = help_page("Bad", Feature="Backups")
    no_summary = page("No summary", Kind="howto", Section="How-to", Order="1", Feature="Backup")
    _repo, result = build(tmp_path, home, {"bad.md": bad, "nosum.md": no_summary})
    assert result.returncode != 0
    assert "META_UNKNOWN doc=bad.md key=Feature value=Backups" in result.stdout
    assert "META_MISSING doc=nosum.md key=Summary" in result.stdout


def test_non_strict_unknown_kind_still_builds(tmp_path, home):
    repo, result = build(tmp_path, home, {"g.md": help_page("Guide", Kind="guide")}, strict=False)
    assert result.returncode == 0, result.stdout
    assert "META_INVALID doc=g.md key=Kind value=guide" in result.stdout
    assert 'class="ah-badge ah-badge-guide">guide<' in (repo / "target" / "g.html").read_text()


def test_undated_pages_are_in_navigation(tmp_path, home):
    repo, result = build(tmp_path, home, {
        "a.md": help_page("A", Order="1"), "b.md": help_page("B", Order="2"),
    })
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "a.html").read_text()
    assert 'href="b.html"' in html
    assert "DATE_INVALID" not in result.stdout


def test_relative_links_only(tmp_path, home):
    repo, result = build(tmp_path, home, {"a.md": help_page("A", "[b](b.md)"), "b.md": help_page("B")})
    assert result.returncode == 0, result.stdout
    for path in (repo / "target").glob("*.html"):
        for value in re.findall(r'(?:href|src)="([^"]*)"', path.read_text()):
            assert not value.startswith("/"), (path.name, value)
            assert not value.split("#")[0].split("?")[0].endswith(".md"), (path.name, value)


def test_contract_failure(tmp_path, home):
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    (repo / "config" / "contract.txt").write_text("backup-dialog\nmissing-id\nbackup.html#nope\n")
    cfg = write_repo(repo, "apphelp", {"backup.md": help_page("Back up", "## Restore {#restore}\n\nx",
                                                              HelpId="backup-dialog=#restore")},
                     apphelp={"vocabulary": VOCAB})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode != 0
    assert "CONTRACT_MISSING entry=missing-id" in result.stdout
    assert "CONTRACT_MISSING entry=backup.html#nope" in result.stdout
    assert "CONTRACT_MISSING entry=backup-dialog" not in result.stdout


def test_helpid_to_missing_anchor_fails_strict(tmp_path, home):
    _repo, result = build(tmp_path, home, {"a.md": help_page("A", HelpId="x=#nowhere")})
    assert result.returncode != 0
    assert "HELPID_TARGET_MISSING id=x" in result.stdout


def test_anchor_warning(tmp_path, home):
    _repo, result = build(tmp_path, home, {"a.md": help_page("A", "[b](b.md#nope)"), "b.md": help_page("B")})
    assert result.returncode == 0, result.stdout
    assert "ANCHOR_MISSING from=a.html to=b.html#nope" in result.stdout


def test_explicit_missing_contract_file_warns(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "apphelp", {"backup.md": help_page("Back up")},
                     apphelp={"vocabulary": VOCAB, "contract": "config/nope.txt"})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "CONTRACT_FILE_MISSING path=" in result.stdout


def test_default_missing_contract_file_is_silent(tmp_path, home):
    _repo, result = build(tmp_path, home, {"a.md": help_page("A")})
    assert result.returncode == 0, result.stdout
    assert "CONTRACT_FILE_MISSING" not in result.stdout
