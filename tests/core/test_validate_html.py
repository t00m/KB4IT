"""scripts/devel/validate_html.py reads vnu's JSON, keeps uk-* attributes and warnings, ignores only the dialog notice (TS-02)."""

import importlib.util

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("validate_html", ROOT / "scripts" / "devel" / "validate_html.py")
validate_html = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_html)


def test_reads_every_report_and_keeps_uikit_attributes_and_warnings():
    out = ('Picked up JAVA_TOOL_OPTIONS\n'
           '{"messages":[{"type":"error","message":"Attribute \'uk-icon\' not allowed on element \'span\'."}]}\n'
           '{"messages":[{"type":"error","message":"Stray end tag \\"div\\"."},'
           '{"type":"info","subType":"warning","message":"Section lacks heading."},'
           '{"type":"info","subType":"warning","message":"The \'dialog\' element is not supported in all browsers."}]}')
    messages = validate_html._messages(out)
    assert len(messages) == 4
    kept = [m["message"] for m in messages if not validate_html.IGNORED.match(m["message"])]
    assert kept == ["Attribute 'uk-icon' not allowed on element 'span'.", 'Stray end tag "div".', "Section lacks heading."]


def test_no_report_is_not_a_clean_result():
    assert validate_html._messages("java: command not found") is None
    assert validate_html._messages("") == []
