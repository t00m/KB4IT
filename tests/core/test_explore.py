"""kb4it keys: properties, values and documents read from the sources."""

import os

import pytest

from kb4it.core.explore import run_keys
from tests.helpers import page, run_kb4it, write_repo


@pytest.fixture
def kb(tmp_path):
    return write_repo(tmp_path / "kb", "techdoc", {
        "a.md": page("Alpha", Tag="Backup, linux", Status="Open"),
        "b.md": page("Beta", Tag="backup", Status="Closed"),
        "c.md": page("Gamma", Tag="linux"),
    })


def keys(config, *words):
    params = {"project": str(config), "key": None, "value": None}
    params.update(zip(("key", "value"), words))
    return run_keys(params)


def test_level_one_counts_and_hides_title(kb, capsys):
    assert keys(kb) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "    2  Status" in lines
    assert "    3  Tag" in lines
    assert not any(line.endswith("Title") for line in lines)
    assert lines == sorted(lines, key=lambda line: line.split()[1])


def test_level_two_values(kb, capsys):
    assert keys(kb, "Tag") == 0
    assert capsys.readouterr().out.splitlines() == ["    1  Backup", "    1  backup", "    2  linux"]


def test_level_three_paths(kb, capsys):
    assert keys(kb, "Tag", "linux") == 0
    source = kb.parent.parent / "source"
    assert capsys.readouterr().out.splitlines() == [str(source / "a.md"), str(source / "c.md")]


def test_case_insensitive_key_and_value(kb, capsys):
    assert keys(kb, "tag", "BACKUP") == 0
    out = capsys.readouterr().out.splitlines()
    assert [os.path.basename(line) for line in out] == ["a.md", "b.md"]


def test_title_on_request(kb, capsys):
    assert keys(kb, "Title") == 0
    assert "    1  Alpha" in capsys.readouterr().out.splitlines()


def test_unknown_key_or_value_exits_1(kb, capsys):
    assert keys(kb, "Nope") == 1
    assert keys(kb, "Tag", "nope") == 1
    assert "Nope" in capsys.readouterr().err


def test_invalid_documents_counted_on_stderr(kb, capsys):
    source = kb.parent.parent / "source"
    (source / "nofront.md").write_text("# No front matter\n", encoding="utf-8")
    (source / "binary.md").write_bytes(b"---\nTag: x\n---\n\n# Bad \xff\xfe\n")
    assert keys(kb) == 0
    captured = capsys.readouterr()
    err = [line for line in captured.err.splitlines() if line.strip()]
    assert len(err) == 1
    assert "2" in err[0] and "kb4it verify" in err[0]


def test_keys_from_the_command_line_writes_no_log(kb, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = run_kb4it("keys", kb, "Tag", cwd=tmp_path, home=home, split_streams=True)
    assert result.returncode == 0, result.stderr
    assert "    2  linux" in result.stdout.splitlines()
    assert not (kb.parent.parent / "var").exists()


def test_missing_source_folder_exits_1(kb, capsys):
    import shutil
    shutil.rmtree(kb.parent.parent / "source")
    assert keys(kb) == 1
    assert "source" in capsys.readouterr().err
