"""techdoc techdoc_quality.py: the score of one document and the peer statistics."""

import importlib.util
import sys
from datetime import date

import pytest

from tests.helpers import ROOT

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
SKELETONS = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "templates" / "skeletons"
sys.path.insert(0, str(LOGIC))  # techdoc_quality imports techdoc_media
_spec = importlib.util.spec_from_file_location("techdoc_quality", LOGIC / "techdoc_quality.py")
quality = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quality)


@pytest.fixture
def prof():
    return quality.profile({})


@pytest.fixture
def skeletons():
    return quality.load_skeletons(str(SKELETONS))


@pytest.fixture
def doc(tmp_path):
    def make(text, work_type="", backlinks=0, **meta):
        return quality.DocInput(text=text, meta={k: [v] for k, v in meta.items()}, backlinks=backlinks,
                                known_docs={"a.md", "b.md"}, source_dir=str(tmp_path), work_type=work_type)
    return make


def test_findable_counts_core_keys_known_values_and_summary(prof, doc):
    full = doc("# T\n", Author="A", Date="2026-01-01", DocType="How-to guide", Category="Procedure", Status="Released",
               Tag="x", Topic="y", Scope="z", Product="p", Summary="S")
    assert sum(c.points for c in quality.findable(full, prof)) == 15
    assert sum(c.points for c in quality.findable(doc("# T\n", Status="Whatever"), prof)) == 1


def test_structured_how_to_with_skeleton_sections(prof, skeletons, doc):
    body = "# T\n\n## Introduction\n\nWhy.\n\n## Prerequisites\n\nA.\n\n## Steps\n\n1. a\n2. b\n3. c\n\n## Verification\n\nOk.\n"
    checks = quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons)
    assert sum(c.points for c in checks) == 25


def test_structured_record_uses_worktype_skeleton_times_16(prof, skeletons, doc):
    body = "# T\n\n## Overview\n\nX.\n\n## Impact\n\nY.\n\n## Rollback\n\nZ.\n"
    checks = quality.structured(doc(body, work_type="Change", Category="Record"), prof, skeletons)
    assert sum(c.points for c in checks) == 25 and not any(c.name.startswith("Fits") for c in checks)


def test_empty_sections_and_placeholders_cost_points(prof, skeletons, doc):
    body = "# T\n\n## Introduction\n\n## Steps\n\n1. Step one\n2. Step two\n3. Step three\n"
    total = sum(c.points for c in quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons))
    assert total == pytest.approx(max(0, 5 + 4 + 8 + 8 * 1 / 3 - 3 - 6))


def test_almost_empty_document_does_not_raise(prof, skeletons, doc):
    d = doc("# T\n", Category="Note")
    assert quality.findable(d, prof) and quality.structured(d, prof, skeletons)
