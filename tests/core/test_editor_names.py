"""ED-06 and ED-10: the shared table of name rules, checked against the Python functions."""

import json
from pathlib import Path

from kb4it.core.files import valid_filename
from kb4it.core.util import slugify

TABLE = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "editor" / "names.json").read_text(encoding="utf-8")
)


def test_python_matches_shared_table():
    assert TABLE["valid_filename"] and TABLE["slugify"]
    for value, expected in TABLE["valid_filename"]:
        assert valid_filename(value) == expected, value
    for value, expected in TABLE["slugify"]:
        assert slugify(value) == expected, value
