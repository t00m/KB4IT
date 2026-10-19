"""The markdown block of repo.json: extra extensions, their settings, and clear errors."""

import json

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.mdconfig import BASE_EXTENSIONS, load_settings
from tests.helpers import page, run_kb4it, write_repo

TWO_LINES = "first line\nsecond line\n"


def test_defaults_keep_the_base_dialect():
    settings = load_settings({})
    names = [e for e in settings.all_extensions() if isinstance(e, str)]
    assert names == BASE_EXTENSIONS
    assert settings.highlight == "client"


@pytest.mark.parametrize("block, message", [
    ("nope", "must be an object"),
    ({"extensions": "toc"}, "list of extension names"),
    ({"extension_configs": {"toc": 1}}, "map extension names"),
    ({"highlight": "rainbow"}, "client, pygments, none"),
    ({"extensions": ["no_such_extension_xyz"]}, "pip install no_such_extension_xyz"),
    ({"extensions": ["pymdownx.no_such"]}, "pip install pymdown-extensions"),
])
def test_bad_blocks_are_refused(block, message):
    with pytest.raises(ConfigError, match=message):
        load_settings({"markdown": block})


def test_extra_extension_reaches_the_pages(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", TWO_LINES, Tag="x")},
                     markdown={"extensions": ["md_in_html", "nl2br"]})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8")
    assert "first line<br" in html  # nl2br turns the line break inside a paragraph into <br>


def test_missing_extension_fails_build_and_verify(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")},
                     markdown={"extensions": ["pymdownx.not_there"]})
    build = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert build.returncode == 1
    assert "MD_EXTENSION_MISSING name=pymdownx.not_there hint=pip install pymdown-extensions" in build.stdout
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert verify.returncode == 1
    assert "pymdown-extensions" in verify.stdout


def test_changing_the_block_recompiles_everything(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x"), "b.md": page("B", Tag="y")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["markdown"] = {"extensions": ["nl2br"]}
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert "CORE_SIGNATURE_CHANGED" in result.stdout
    assert "COMPILED doc=a.md" in result.stdout and "COMPILED doc=b.md" in result.stdout
