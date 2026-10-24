"""scripts/conv/split_category.py moves record types from Category to WorkType in the frontmatter only."""

import importlib.util

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("split_category", ROOT / "scripts" / "conv" / "split_category.py")
split = importlib.util.module_from_spec(spec)
spec.loader.exec_module(split)


def test_change_becomes_record():
    text = "---\nAuthor: A\nCategory: Change\nStatus: Open\n---\n\n# T\n\nCategory: Change stays in the body.\n"
    new, change = split.split_text(text)
    assert new == "---\nAuthor: A\nCategory: Record\nWorkType: Change\nStatus: Open\n---\n\n# T\n\nCategory: Change stays in the body.\n"
    assert change == {"category_before": "Change", "category_after": "Record", "worktype": "Change"}


def test_meeting_becomes_minutes():
    new, _ = split.split_text("---\nCategory: Meeting\n---\n\n# T\n")
    assert "Category: Minutes\nWorkType: Meeting\n" in new


def test_list_keeps_the_forms():
    new, change = split.split_text("---\nCategory: Report, Incident\n---\n\n# T\n")
    assert "Category: Report\nWorkType: Incident\n" in new
    assert change["category_after"] == "Report"


def test_forms_and_migrated_documents_are_untouched():
    for text in ("---\nCategory: Procedure, Note\n---\n\n# T\n",
                 "---\nCategory: Record\nWorkType: Change\n---\n\n# T\n",
                 "---\nAuthor: A\n---\n\n# T\n", "# No frontmatter\n"):
        assert split.split_text(text) == (text, None)


def test_crlf_and_idempotence():
    text = "---\r\nCategory: Task\r\n---\r\n\r\n# T\r\n"
    new, _ = split.split_text(text)
    assert new == "---\r\nCategory: Record\r\nWorkType: Task\r\n---\r\n\r\n# T\r\n"
    assert split.split_text(new) == (new, None)


def test_split_dir_writes_csv_and_respects_dry_run(tmp_path):
    (tmp_path / "a.md").write_text("---\nCategory: Change\n---\n\n# A\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("---\nCategory: Note\n---\n\n# B\n", encoding="utf-8")
    changes = split.split_dir(tmp_path, tmp_path / "out.csv", dry_run=True)
    assert [c["file"] for c in changes] == ["a.md"]
    assert "Category: Change" in (tmp_path / "a.md").read_text(encoding="utf-8")
    split.split_dir(tmp_path, tmp_path / "out.csv", dry_run=False)
    assert "WorkType: Change" in (tmp_path / "a.md").read_text(encoding="utf-8")
    assert (tmp_path / "out.csv").read_text(encoding="utf-8").splitlines()[0] == "file,category_before,category_after,worktype"
