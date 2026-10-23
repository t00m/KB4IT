"""sync_file, sync_tree and prune_tree: copy only new or changed files, delete what the source no longer has."""

import os

from kb4it.core.files import prune_tree, sync_file, sync_tree


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_sync_file_copies_then_skips_an_unchanged_file(tmp_path):
    source = _write(tmp_path / "a.txt", "one")
    dest = tmp_path / "out.txt"
    assert sync_file(str(source), str(dest)) is True
    assert os.stat(dest).st_mtime_ns == os.stat(source).st_mtime_ns
    assert sync_file(str(source), str(dest)) is False


def test_sync_file_copies_a_same_size_file_with_another_time(tmp_path):
    source = _write(tmp_path / "a.txt", "one")
    dest = tmp_path / "out.txt"
    sync_file(str(source), str(dest))
    source.write_text("two", encoding="utf-8")
    os.utime(source, ns=(os.stat(dest).st_atime_ns, os.stat(dest).st_mtime_ns + 1_000_000))
    assert sync_file(str(source), str(dest)) is True
    assert dest.read_text(encoding="utf-8") == "two"


def test_sync_tree_mirrors_and_counts(tmp_path):
    source, dest = tmp_path / "src", tmp_path / "dest"
    _write(source / "a.css", "a")
    _write(source / "sub" / "b.js", "b")
    _write(dest / "old.css", "old")
    _write(dest / "gone" / "c.js", "c")
    copied, deleted, files = sync_tree(str(source), str(dest))
    assert (copied, deleted) == (2, 2)
    assert files == {os.path.join(str(dest), "a.css"), os.path.join(str(dest), "sub", "b.js")}
    assert sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*")) == ["a.css", "sub", "sub/b.js"]
    assert sync_tree(str(source), str(dest))[:2] == (0, 0)


def test_sync_tree_keeps_listed_paths(tmp_path):
    source, dest = tmp_path / "src", tmp_path / "dest"
    _write(source / "a.css", "a")
    kept = _write(dest / "user" / "logo.png", "png")
    sync_tree(str(source), str(dest), keep={str(kept)})
    assert kept.read_text(encoding="utf-8") == "png"


def test_sync_tree_without_mirror_deletes_nothing(tmp_path):
    source, dest = tmp_path / "src", tmp_path / "dest"
    _write(source / "a.css", "a")
    extra = _write(dest / "extra.txt", "x")
    assert sync_tree(str(source), str(dest), mirror=False)[:2] == (1, 0)
    assert extra.exists()


def test_sync_tree_replaces_a_folder_by_a_file_and_back(tmp_path):
    source, dest = tmp_path / "src", tmp_path / "dest"
    _write(source / "x", "file")
    _write(dest / "x" / "inner.txt", "dir")
    sync_tree(str(source), str(dest))
    assert (dest / "x").read_text(encoding="utf-8") == "file"
    (source / "x").unlink()
    _write(source / "x" / "inner.txt", "dir again")
    sync_tree(str(source), str(dest))
    assert (dest / "x" / "inner.txt").read_text(encoding="utf-8") == "dir again"


def test_missing_source_empties_the_mirror(tmp_path):
    dest = tmp_path / "dest"
    _write(dest / "a.css", "a")
    assert sync_tree(str(tmp_path / "nothing"), str(dest))[:2] == (0, 1)
    assert list(dest.iterdir()) == []


def test_prune_tree_removes_links_without_following_them(tmp_path):
    outside = _write(tmp_path / "outside" / "keep.txt", "keep")
    dest = tmp_path / "dest"
    dest.mkdir()
    os.symlink(outside.parent, dest / "link")
    assert prune_tree(str(dest), set()) == 1
    assert outside.exists() and not (dest / "link").exists()


def test_sync_tree_never_overwrites_a_kept_path(tmp_path):
    source, dest = tmp_path / "src", tmp_path / "dest"
    _write(source / "a.css", "theme")
    kept = _write(dest / "a.css", "repository")
    assert sync_tree(str(source), str(dest), keep={str(kept)})[:2] == (0, 0)
    assert kept.read_text(encoding="utf-8") == "repository"
