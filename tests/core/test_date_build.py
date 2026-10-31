"""Date keys in a build: resolved on every document, no value pages, timezone in the core signature."""

import json
import re

from tests.helpers import mini_theme, page, run_kb4it, write_repo


def _repo(tmp_path, pages, **config):
    config.setdefault("timezone", "UTC")
    repo = tmp_path / "repo"
    return repo, write_repo(repo, "mini", pages, theme_path=str(mini_theme(tmp_path / "mini")), **config)


def _log(repo):
    return (repo / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")


def test_invalid_date_no_longer_stops_the_build(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"a.md": page("A", Date="YYYY-MM-DD")})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert re.search(r"\[DATES\] DATE_INVALID key=Date value=YYYY-MM-DD doc=a\.md", _log(repo))


def test_date_filled_from_scheduled_start(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"c.md": page("C", ScheduledStart="2026-11-02 22:00",
                                              ScheduledEnd="2026-11-03 02:00")})
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    kbdict = json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))
    assert kbdict["metadata"]["Date"] == {"2026-11-02 22:00:00": ["c.md"]}


def test_cached_documents_get_the_same_notices(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"m.md": page("M", Start="2026-11-02 10:00")})
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    second = run_kb4it("-L", "DEBUG", "build", cfg, cwd=repo, home=home)
    assert second.returncode == 0, second.stdout
    log = _log(repo)
    assert "HEADER_CACHE doc=m.md action=reuse" in log
    assert "[DATES] DATE_END_MISSING key=End start=Start doc=m.md" in log


def test_timezone_change_rebuilds_everything(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"a.md": page("A", Date="2026-11-02")})
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["timezone"] = "Europe/Madrid"
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    assert "CORE_SIGNATURE_CHANGED" in run_kb4it("build", cfg, cwd=repo, home=home).stdout


def test_date_keys_get_no_value_pages(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"t.md": page("T", Date="2026-11-02", DueDate="2026-11-09")})
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    assert not list((repo / "target").glob("DueDate*.html"))


def test_date_key_refused_in_people_keys(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"a.md": page("A", Date="2026-11-02")}, people={"keys": ["DueDate"]})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode != 0 and "people.keys" in result.stdout


def test_date_key_refused_in_seo_map(tmp_path, home):
    repo, cfg = _repo(tmp_path, {"a.md": page("A", Date="2026-11-02")}, seo={"map": {"DueDate": "keywords"}})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode != 0 and "seo.map" in result.stdout


def _dead_date_links(html, target):
    """Links from a page to date-key value pages that the build did not write."""
    links = re.findall(r'href="((?:Date|DueDate|Start|End|ScheduledStart|ScheduledEnd)_[^"]*\.html)"', html)
    return [link for link in links if not (target / link).exists()]


def test_techdoc_document_page_has_no_dead_date_links(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"t.md": page("T", Date="2026-11-02", DueDate="2026-11-09",
                                                    Start="2026-11-02 10:00", Tag="x")}, timezone="UTC")
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    html = (repo / "target" / "t.html").read_text(encoding="utf-8")
    assert _dead_date_links(html, repo / "target") == []
    assert "2026-11-09" in html and "2026-11-09 00:00:00" not in html


def test_generic_metadata_links_no_date_key_pages():
    from kb4it.services.themekit.metadata import MetadataMixin

    class FakeDB:
        def get_values(self, doc, key):
            return {"DueDate": ["2026-11-09 00:00:00"], "Tag": ["x"]}[key]

        def get_blocked_keys(self):
            return ["Title", "SystemPage", "Date", "DueDate"]

    theme = MetadataMixin.__new__(MetadataMixin)
    theme.srvdtb = FakeDB()
    assert theme.get_html_values_from_key("p.md", "DueDate") == [("", "2026-11-09")]
    assert theme.get_html_values_from_key("p.md", "Tag") == [("Tag_x.html", "x")]
