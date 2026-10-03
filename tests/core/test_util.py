"""Unit tests of the helpers in kb4it.core.util."""

# ruff: noqa: DTZ001, DTZ007  # KB4IT works with naive local datetimes

from datetime import datetime

import pytest

from kb4it.core import util


def test_extract_sections_from_md(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\nIntro\n\n## One\n\ntext\n### Sub\n\n## Two\nend\n", encoding="utf-8")
    assert util.extract_sections_from_md(str(md)) == {
        "One": {"start": 5, "end": 9},
        "Two": {"start": 10, "end": 11},
    }


def test_extract_sections_without_h2(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\n### Only a third level\n", encoding="utf-8")
    assert util.extract_sections_from_md(str(md)) == {}


def test_copy_docs_skips_missing_files(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("a", encoding="utf-8")
    target = tmp_path / "out"
    target.mkdir()
    util.copy_docs([str(src), str(tmp_path / "missing.md")], str(target))
    assert sorted(p.name for p in target.iterdir()) == ["a.md"]


def test_copydir_merges_into_existing_tree(tmp_path):
    source = tmp_path / "src"
    (source / "sub").mkdir(parents=True)
    (source / "top.txt").write_text("new", encoding="utf-8")
    (source / "sub" / "deep.txt").write_text("deep", encoding="utf-8")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "top.txt").write_text("old", encoding="utf-8")
    (dest / "keep.txt").write_text("keep", encoding="utf-8")
    util.copydir(str(source), str(dest))
    assert (dest / "top.txt").read_text() == "new"
    assert (dest / "sub" / "deep.txt").read_text() == "deep"
    assert (dest / "keep.txt").exists()


def test_get_source_docs_finds_both_extensions(tmp_path):
    for name in ("a.md", "b.markdown", "c.txt"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    found = sorted(p.rsplit("/", 1)[1] for p in util.get_source_docs(str(tmp_path)))
    assert found == ["a.md", "b.markdown"]


def test_get_default_workers_is_half_the_cpus(monkeypatch):
    monkeypatch.setattr(util.multiprocessing, "cpu_count", lambda: 5)
    assert util.get_default_workers() == 3
    monkeypatch.setattr(util.multiprocessing, "cpu_count", lambda: 1)
    assert util.get_default_workers() == 1


def test_exec_cmd_reports_success_and_failure():
    assert util.exec_cmd(("doc.md", "true", 7)) == ("doc.md", True, 7)
    assert util.exec_cmd(("doc.md", "exit 3", 8)) == ("doc.md", False, 8)


def test_word_cloud_sizes():
    keys = {"a": [1], "b": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
    assert util.set_max_frequency(keys) == 10
    assert util.set_max_frequency({}) == 1
    assert util.get_font_size(3, 1) == 10
    assert util.get_font_size(1, 1000) == 8      # log(0.1) < 1
    assert util.get_font_size(5, 100) == 10      # log(5) = 1.6
    assert util.get_font_size(1, 10) == 18       # log(10) = 2.3
    assert util.get_font_size(3, 10) == 36       # log(30) = 3.4
    assert util.get_font_size(10, 10) == 72      # log(100) = 4.6


def test_delete_target_contents(tmp_path):
    target = tmp_path / "target"
    (target / "dir").mkdir(parents=True)
    (target / "file.html").write_text("x", encoding="utf-8")
    (target / "dir" / "inner.html").write_text("x", encoding="utf-8")
    assert util.delete_target_contents(str(target)) is False
    assert target.is_dir() and not any(target.iterdir())
    single = tmp_path / "single.txt"
    single.write_text("x", encoding="utf-8")
    assert util.delete_target_contents(str(single)) is False
    assert not single.exists()
    assert util.delete_target_contents(str(tmp_path / "missing")) is True


def test_delete_files_ignores_missing(tmp_path):
    present = tmp_path / "a.txt"
    present.write_text("x", encoding="utf-8")
    util.delete_files([str(present), str(tmp_path / "missing.txt")])
    assert not present.exists()


def test_json_round_trip(tmp_path):
    path = tmp_path / "data.json"
    util.json_save(str(path), {"b": 1, "a": [1, 2]})
    assert util.json_load(str(path)) == {"a": [1, 2], "b": 1}
    assert path.read_text().index('"a"') < path.read_text().index('"b"')


def test_hashes(tmp_path):
    assert util.get_hash_from_content("x") == util.get_hash_from_content("x")
    assert util.get_hash_from_content("x") != util.get_hash_from_content("y")
    assert util.get_hash_from_dict({"a": 1, "b": 2}) == util.get_hash_from_dict({"b": 2, "a": 1})
    assert util.get_hash_from_list([1, 2]) != util.get_hash_from_list([2, 1])
    path = tmp_path / "f.txt"
    path.write_text("content", encoding="utf-8")
    assert util.get_hash_from_file(str(path)) == util.get_hash_from_content("content")
    assert util.get_hash_from_file(str(tmp_path / "missing")) is None


def test_body_hash_ignores_frontmatter_and_title(tmp_path):
    one = tmp_path / "one.md"
    two = tmp_path / "two.md"
    one.write_text("---\nTag: a\n---\n\n# First title\n\nSame body.\n", encoding="utf-8")
    two.write_text("---\nTag: b\n---\n\n# Other title\n\nSame body.\n", encoding="utf-8")
    assert util.get_hash_from_body(str(one)) == util.get_hash_from_body(str(two))
    two.write_text("---\nTag: b\n---\n\n# Other title\n\nNew body.\n", encoding="utf-8")
    assert util.get_hash_from_body(str(one)) != util.get_hash_from_body(str(two))
    assert util.get_hash_from_body(str(tmp_path / "missing.md")) is None


def test_names():
    assert util.valid_filename("john's portrait in 2004.jpg") == "johns_portrait_in_2004.jpg"
    assert util.slugify("  Árbol de Navidad: 2026! ") == "arbol-de-navidad-2026"
    assert util.ellipsize_text("short") == "short"
    text = "a" * 50 + "b" * 50
    assert util.ellipsize_text(text, 21) == "a" * 9 + "..." + "b" * 10
    assert util.ellipsize_text(text, 20) == "a" * 8 + "..." + "b" * 8


@pytest.mark.parametrize("nbytes, expected", [
    (0, "0 B"),
    (1023, "1023 B"),
    (1024, "1.0 KB"),
    (1536 * 1024, "1.5 MB"),
    (3 * 1024 ** 3, "3.0 GB"),
    (2 * 1024 ** 4, "2.0 TB"),
])
def test_human_size(nbytes, expected):
    assert util.human_size(nbytes) == expected


@pytest.mark.parametrize("text", [
    "03/10/2026 14:30",
    "03.10.2026 14:30",
    "03-10-2026 14:30",
    "2026/10/03 14:30",
    "2026-10-03 14:30",
    "2026-10-03T14:30:00",
    "2026-10-03T14:30:00Z",
    "20261003143000",
])
def test_guess_datetime_formats(text):
    cache = util.DateCache()
    assert util.guess_datetime(text, _cache=cache) == datetime(2026, 10, 3, 14, 30)
    assert cache.has_dt(text)


def test_guess_datetime_unknown_is_cached_as_none():
    cache = util.DateCache()
    assert util.guess_datetime("not a date", _cache=cache) is None
    assert cache.has_dt("not a date") and cache.get_dt("not a date") is None
    cache.clear()
    assert not cache.has_dt("not a date")


def test_date_formatting():
    dt = datetime(2026, 10, 3, 14, 30, 5)
    assert util.string_timestamp("2026-10-03 14:30:05") == "2026-10-03 14:30:05"
    assert util.get_human_datetime(dt) == "Saturday, October 03, 2026 at 14:30"
    assert util.get_human_datetime_day(dt) == "Saturday, October 03, 2026"
    assert util.get_human_datetime_month(dt) == "October, 2026"
    assert util.get_human_datetime_year(dt) == "2026"
    cache = util.DateCache()
    assert util.get_timestamp_yyyymmdd(dt, _cache=cache) == "20261003"
    assert cache.get_ymd(dt) == "20261003"
    assert (util.get_year("20261003"), util.get_month("20261003"), util.get_day("20261003")) == (2026, 10, 3)


def test_timestamps_have_the_documented_shape():
    assert datetime.strptime(util.log_timestamp(), "%Y%m%d_%H%M%S")
    assert datetime.strptime(util.kb4it_timestamp(), "%Y-%m-%d %H:%M:%S")
    assert datetime.fromisoformat(util.now())


def test_sort_dictionary():
    assert util.sort_dictionary({"a": 1, "b": 3, "c": 2}) == [("b", 3), ("c", 2), ("a", 1)]
    assert util.sort_dictionary({"a": 1, "b": 3}, reverse=False) == [("a", 1), ("b", 3)]
