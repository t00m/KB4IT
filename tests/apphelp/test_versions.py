"""Versioned help: each version in its own folder, latest/ and the root files, and the switcher."""

import json

from tests.helpers import page, run_kb4it, write_repo


def _build(repo, cfg, tmp_path, home, version, latest=""):
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["version"] = version
    conf["apphelp"]["versions"] = {"enabled": True, "latest": latest} if latest else {"enabled": True}
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return result


def test_two_versions_side_by_side(tmp_path, home):
    pages = {"start.md": page("Start", "Version one text.", DocType="Tutorial", HelpId="start"),
             "old.md": page("Old page", "Only in 0.8.", DocType="Reference")}
    cfg = write_repo(tmp_path / "help", "apphelp", pages, apphelp={"strict": False})
    repo = tmp_path / "help"
    _build(repo, cfg, tmp_path, home, "0.8")
    (repo / "source" / "old.md").unlink()
    (repo / "source" / "start.md").write_text(page("Start", "Version two text.", DocType="Tutorial", HelpId="start"),
                                              encoding="utf-8")
    result = _build(repo, cfg, tmp_path, home, "0.9")
    assert "[VERSIONS] PUBLISHED current=0.9 latest=0.9 all=0.9,0.8" in result.stdout

    site = repo / "target"
    assert "Version one text." in (site / "0.8" / "start.html").read_text(encoding="utf-8")
    assert "Version two text." in (site / "0.9" / "start.html").read_text(encoding="utf-8")
    assert "Version two text." in (site / "latest" / "start.html").read_text(encoding="utf-8")
    assert not (site / "latest" / ".kb4it-version").exists()
    versions = json.loads((site / "versions.json").read_text(encoding="utf-8"))
    assert versions["latest"] == "0.9"
    assert [v["label"] for v in versions["versions"]] == ["0.9", "0.8"]
    assert "old.html" in versions["versions"][1]["pages"] and "old.html" not in versions["versions"][0]["pages"]
    assert 'url=latest/index.html' in (site / "index.html").read_text(encoding="utf-8")
    assert '"start": "latest/start.html"' in (site / "helpids.js").read_text(encoding="utf-8")
    html = (site / "0.9" / "start.html").read_text(encoding="utf-8")
    assert 'id="ah-version"' in html and 'data-current="0.9"' in html and 'src="../versions.js"' in html


def test_latest_can_be_pinned_and_versions_need_a_label(tmp_path, home):
    cfg = write_repo(tmp_path / "help", "apphelp", {"a.md": page("A", DocType="Reference")}, apphelp={"strict": False})
    repo = tmp_path / "help"
    _build(repo, cfg, tmp_path, home, "1.0")
    result = _build(repo, cfg, tmp_path, home, "1.1-beta", latest="1.0")
    assert "latest=1.0" in result.stdout
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf.pop("version")
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    failed = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert failed.returncode == 1 and "need the 'version' key" in failed.stdout


def test_version_order():
    from apphelp_versions import version_key
    assert sorted(["0.9", "0.10", "0.8.1", "1.0"], key=version_key, reverse=True) == ["1.0", "0.10", "0.9", "0.8.1"]
