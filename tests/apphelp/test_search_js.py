import json
import os
import shutil
import subprocess

import pytest

from tests.helpers import APPHELP

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")

SCRIPT = r"""
const fs = require("fs");
global.window = global;
eval(fs.readFileSync(process.env.SEARCH_JS, "utf8"));
const input = JSON.parse(fs.readFileSync(0, "utf8"));
const engine = new window.AppHelpSearch.Engine(input.records);
const searches = input.queries.map(q => engine.search(q.q, q.filters || {}).map(r => r.url));
const links = input.links.map(l => window.AppHelpSearch.withParams(l[0], l[1]));
console.log(JSON.stringify({searches, links}));
"""

RECORDS = [
    {"u": "backup.html", "t": "Back up a repository", "s": "Copy all documents to a safe place.",
     "k": "howto", "c": "How-to", "f": {"Kind": ["howto"], "Feature": ["Backup"]}, "w": ["save copy"],
     "g": [], "x": [["", "", "Intro text."],
                    ["restore", "Restore a backup", "Use the camión option to restore files."]]},
    {"u": "rename.html", "t": "Rename documents", "s": "Change the name of a document.",
     "k": "howto", "c": "How-to", "f": {"Kind": ["howto"], "Feature": ["Rename"]}, "w": ["retitle"],
     "g": [], "x": [["", "", "Pick a document."]]},
]


def run(queries, links):
    env = dict(os.environ, SEARCH_JS=str(APPHELP / "framework" / "apphelp" / "js" / "search.js"))
    payload = json.dumps({"records": RECORDS, "queries": queries, "links": links})
    out = subprocess.run([NODE, "-e", SCRIPT], input=payload, env=env, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_search_engine():
    result = run([
        {"q": "camion"},
        {"q": "retit"},
        {"q": "rename backup"},
        {"q": "", "filters": {"Feature": ["Rename"]}},
        {"q": "document"},
        {"q": "RESTORE"},
    ], [])
    assert result["searches"] == [
        ["backup.html#restore"],
        ["rename.html"],
        [],
        ["rename.html"],
        ["rename.html", "backup.html"],
        ["backup.html#restore"],
    ]


def test_with_params_keeps_fragment_last():
    result = run([], [
        ["b.html#y", "?embed=1&theme=dark&id=x"],
        ["b.html?q=a#y", "?embed=1"],
        ["#local", "?embed=1"],
        ["https://example.com/", "?embed=1"],
        ["b.html", ""],
    ])
    assert result["links"] == [
        "b.html?embed=1&theme=dark#y",
        "b.html?q=a&embed=1#y",
        "#local",
        "https://example.com/",
        "b.html",
    ]


def test_fold_removes_accents_and_case():
    env = dict(os.environ, SEARCH_JS=str(APPHELP / "framework" / "apphelp" / "js" / "search.js"))
    script = ('global.window = global; eval(require("fs").readFileSync(process.env.SEARCH_JS, "utf8"));'
              'console.log(JSON.stringify([window.AppHelpSearch.fold("é"), window.AppHelpSearch.fold("CAMIÓN")]));')
    out = subprocess.run([NODE, "-e", script], env=env, capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == ["e", "camion"]


def test_search_js_has_no_raw_combining_characters():
    path = APPHELP / "framework" / "apphelp" / "js" / "search.js"
    assert "̀" not in path.read_text(encoding="utf-8")
