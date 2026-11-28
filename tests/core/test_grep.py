"""kb4it search over the Markdown sources of one, several or all projects."""

import io
import os
import re

import pytest

from kb4it.core import projects
from kb4it.core.grep import parse_where, run_search, where_matches
from tests.helpers import page, run_kb4it, write_repo


@pytest.fixture(autouse=True)
def listing(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_FILE", tmp_path / "projects.json")


@pytest.fixture
def kb1(tmp_path):
    config = write_repo(tmp_path / "kb1", "techdoc", {
        "a.md": page("Alpha", "First line.\nRestore the backup.\nLiteral a.b( here.", Tag="backup", Status="Open"),
        "b.md": page("Beta", "Nothing to see.\nrestore later", Tag="backup", Status="Planned"),
        "c.md": page("Gamma", "restore and linux", Tag="linux", Status="Open"),
    })
    projects.register(config, pid="kb1")
    return config


@pytest.fixture
def kb2(tmp_path):
    config = write_repo(tmp_path / "kb2", "techdoc", {"z.md": page("Zeta", "Restore from tape.", Tag="tape")})
    projects.register(config, pid="kb2")
    return config


class Tty(io.StringIO):
    def isatty(self):
        return True


def search(pattern, *, p=None, where=None, regex=False, case_sensitive=False, files=False, out=None):
    out = out if out is not None else io.StringIO()
    err = io.StringIO()
    status = run_search({"pattern": pattern, "projects": p, "where": where, "regex": regex,
                         "case_sensitive": case_sensitive, "files_with_matches": files}, out=out, err=err)
    return status, out.getvalue().splitlines(), err.getvalue()


def file_of(line):
    """The file of a "file:line: text" result. A Windows path has a colon of its own (C:)."""
    return re.match(r"(.*?):\d+: ", line).group(1)


def src(config, name):
    return str(config.parent.parent / "source" / name)


def test_plain_case_insensitive(kb1):
    status, lines, _ = search("RESTORE", p=["kb1"])
    assert status == 0
    assert lines[0] == f"{src(kb1, 'a.md')}:9: Restore the backup."
    assert [file_of(line) for line in lines] == [src(kb1, n) for n in ("a.md", "b.md", "c.md")]


def test_front_matter_is_searched(kb1):
    status, lines, _ = search("Status: Planned", p=["kb1"])
    assert status == 0
    assert lines == [f"{src(kb1, 'b.md')}:3: Status: Planned"]


def test_regex_flag(kb1):
    status, lines, _ = search(r"^restore\b", p=["kb1"], regex=True)
    assert status == 0
    assert len(lines) == 3


def test_case_sensitive_flag(kb1):
    status, lines, _ = search("Restore", p=["kb1"], case_sensitive=True)
    assert [file_of(line) for line in lines] == [src(kb1, "a.md")]


def test_plain_pattern_with_regex_chars(kb1):
    status, lines, _ = search("a.b(", p=["kb1"])
    assert status == 0
    assert lines == [f"{src(kb1, 'a.md')}:10: Literal a.b( here."]


def test_bad_regex_exits_2(kb1):
    status, _lines, err = search("a(", p=["kb1"], regex=True)
    assert status == 2
    assert err


def test_files_only(kb1):
    status, lines, _ = search("restore", p=["kb1"], files=True)
    assert lines == [src(kb1, n) for n in ("a.md", "b.md", "c.md")]


def test_where_and_or(kb1):
    status, lines, _ = search("restore", p=["kb1"], where=["Status=Open", "Status=Planned", "Tag=backup"])
    assert [file_of(line) for line in lines] == [src(kb1, "a.md"), src(kb1, "b.md")]
    status, lines, _ = search("restore", p=["kb1"], where=["status=open"])
    assert [file_of(line) for line in lines] == [src(kb1, "a.md"), src(kb1, "c.md")]


def test_parse_where():
    assert parse_where("Tag=backup") == ("Tag", "backup")
    assert parse_where("Topic=a=b") == ("Topic", "a=b")
    for bad in ("Tag", "=x"):
        with pytest.raises(ValueError):
            parse_where(bad)


def test_where_matches():
    props = {"Tag": ["backup", "linux"], "Status": ["Open"]}
    assert where_matches(props, [("tag", "LINUX"), ("Status", "Closed"), ("Status", "Open")])
    assert not where_matches(props, [("Tag", "tape")])
    assert not where_matches(props, [("Missing", "x")])


def test_bad_where_exits_2(kb1):
    assert search("restore", p=["kb1"], where=["Tag"])[0] == 2


def test_all_projects_vs_p(kb1, kb2):
    _status, lines, _ = search("restore")
    files = [file_of(line) for line in lines]
    assert files[-1] == src(kb2, "z.md")
    assert src(kb1, "a.md") in files
    _status, lines, _ = search("restore", p=["kb2"])
    assert [file_of(line) for line in lines] == [src(kb2, "z.md")]
    _status, lines, _ = search("restore", p=["kb2", "kb1"])
    assert lines[0].startswith(src(kb2, "z.md"))


def test_p_takes_a_config_path(kb1):
    assert search("restore", p=[str(kb1)])[0] == 0


def test_missing_project_skipped(kb1, kb2):
    os.remove(kb2)
    status, lines, err = search("restore")
    assert status == 0
    assert "kb2" in err
    status, lines, err = search("tape")
    assert status == 1


def test_no_projects_exits_2():
    status, _lines, err = search("x")
    assert status == 2
    assert err


def test_unknown_p_exits_2(kb1):
    assert search("x", p=["nosuch"])[0] == 2


def test_no_match_exits_1(kb1):
    assert search("zzzz-nothing", p=["kb1"])[0] == 1


def test_invalid_utf8_line_does_not_crash(kb1):
    (kb1.parent.parent / "source" / "d.md").write_bytes(b"---\nTag: x\n---\n\n# D\n\nbad \xff byte\nrestore here\n")
    status, lines, _ = search("restore here", p=["kb1"])
    assert status == 0
    assert lines == [f"{src(kb1, 'd.md')}:8: restore here"]


def test_color_only_on_a_terminal(kb1, monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    _status, lines, _ = search("backup.", p=["kb1"], out=Tty())
    assert "\x1b[1;31mbackup.\x1b[0m" in lines[0]
    monkeypatch.setenv("NO_COLOR", "1")
    _status, lines, _ = search("backup.", p=["kb1"], out=Tty())
    assert "\x1b[" not in lines[0]


def test_search_from_the_command_line(kb1, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = run_kb4it("search", "restore", "-p", kb1, "--where", "Tag=linux",
                       cwd=tmp_path, home=home, split_streams=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"{src(kb1, 'c.md')}:8: restore and linux"]


def test_missing_source_folder_is_skipped_with_a_warning(kb1, tmp_path):
    import shutil
    other = write_repo(tmp_path / "nosrc", "techdoc", {})
    shutil.rmtree(other.parent.parent / "source")
    projects.register(other, pid="nosrc")
    status, _lines, err = search("restore")
    assert status == 0
    assert "nosrc" in err
