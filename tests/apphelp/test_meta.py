import pytest

from apphelp_config import load_config
from apphelp_meta import feature_anchor, is_classified, page_from_keys, parse_helpid, validate_all

CONFIG = load_config({"apphelp": {"vocabulary": {
    "Feature": ["Backup", "Rename"], "Level": ["basic", "advanced"]}}})


def keys(**extra):
    base = {"Title": ["Back up"], "DocType": ["How-to guide"], "Section": ["How-to"], "Order": ["10"],
            "Summary": ["Copy your documents."], "Feature": ["Backup"]}
    base.update({k: v if isinstance(v, list) else [v] for k, v in extra.items()})
    return base


def codes(problems):
    return sorted(str(p) for p in problems)


def test_valid_page_has_no_problems():
    assert validate_all({"a.md": keys(Level="basic")}, CONFIG) == []


def test_missing_keys_are_all_reported():
    broken = keys()
    del broken["Summary"]
    del broken["Feature"]
    assert codes(validate_all({"a.md": broken}, CONFIG)) == [
        "META_MISSING doc=a.md key=Feature", "META_MISSING doc=a.md key=Summary"]


def test_invalid_values():
    docs = {"a.md": keys(Order="ten", Feature=["Backups"], Level="expert",
                          Related="nope.md", HelpId="Bad Id")}
    assert codes(validate_all(docs, CONFIG)) == [
        "META_INVALID doc=a.md key=HelpId value=Bad Id",
        "META_INVALID doc=a.md key=Order value=ten",
        "META_INVALID doc=a.md key=Related value=nope.md reason=unknown_page",
        "META_UNKNOWN doc=a.md key=Feature value=Backups",
        "META_UNKNOWN doc=a.md key=Level value=expert",
    ]


def test_long_summary():
    problems = validate_all({"a.md": keys(Summary="x" * 161)}, CONFIG)
    assert codes(problems) == ["META_INVALID doc=a.md key=Summary reason=longer_than_160"]


def test_duplicate_helpid():
    docs = {"a.md": keys(HelpId="backup"), "b.md": keys(HelpId="backup=#restore")}
    assert codes(validate_all(docs, CONFIG)) == ["HELPID_DUPLICATE doc=b.md id=backup first=a.md"]


def test_feature_vocabulary_is_required():
    problems = validate_all({"a.md": keys()}, load_config({}))
    assert codes(problems) == ["META_CONFIG doc=repo.json reason=missing_feature_vocabulary"]


def test_landing_and_system_pages_are_skipped():
    docs = {"index.md": {"Title": ["Home"]}, "about_app.md": {"Title": ["About"], "SystemPage": ["Yes"]}}
    assert validate_all(docs, CONFIG) == []


def test_summary_with_comma_is_joined():
    page = page_from_keys("a.md", keys(Summary=["Copy, then check", "the result."]))
    assert page.summary == "Copy, then check, the result."


def test_quoted_since_keeps_trailing_zero():
    # YAML reads Since: "0.10" as a string; get_document_attributes keeps it as "0.10".
    assert page_from_keys("a.md", keys(Since="0.10")).since == "0.10"


def test_page_from_keys():
    page = page_from_keys("backup.md", keys(Keyword=["save", "copy"], HelpId=["backup", "restore=#restore"],
                                            Platform=["Linux"], Since="0.4", Date="2026-01-02 10:00:00"))
    assert page.url == "backup.html"
    assert (page.title, page.doctype, page.section, page.order, page.layout) == ("Back up", "howto", "How-to", 10, "")
    assert page.helpids == [("backup", ""), ("restore", "restore")]
    assert page.keywords == ["save", "copy"]
    assert page.platforms == ["Linux"]
    assert page.date == "2026-01-02 10:00:00"


def test_parse_helpid_and_anchor():
    assert parse_helpid("rename-dialog=#mass-rename") == ("rename-dialog", "mass-rename")
    assert feature_anchor("Import & export") == "feature-import-export"
    assert feature_anchor("***") == "feature-other"


def test_blank_required_values_are_missing():
    docs = {"a.md": keys(Summary=[""], DocType=["  "])}
    assert codes(validate_all(docs, CONFIG)) == [
        "DOCTYPE_MISSING doc=a.md key=DocType action=left_out", "META_MISSING doc=a.md key=Summary"]


def test_reserved_page_names_are_reported():
    docs = {name: keys() for name in ("search.md", "topics.md", "go.md", "404.md")}
    assert codes(validate_all(docs, CONFIG)) == [
        f"META_INVALID doc={name} reason=reserved_name" for name in ("404.md", "go.md", "search.md", "topics.md")]


@pytest.mark.parametrize("value, code", [
    ([], "DOCTYPE_MISSING doc=a.md key=DocType action=left_out"),
    (["howto"], "DOCTYPE_INVALID doc=a.md key=DocType value=howto allowed=Tutorial|How-to guide|Reference|Explanation action=left_out"),
    (["how-to guide"], "DOCTYPE_INVALID doc=a.md key=DocType value=how-to guide allowed=Tutorial|How-to guide|Reference|Explanation action=left_out"),
    (["Tutorial", "Reference"], "DOCTYPE_INVALID doc=a.md key=DocType value=Tutorial, Reference allowed=Tutorial|How-to guide|Reference|Explanation action=left_out"),
])
def test_type_of_document_is_strict(value, code):
    doc = keys()
    doc["DocType"] = value
    assert codes(validate_all({"a.md": doc}, CONFIG)) == [code]
    assert not is_classified(doc)


@pytest.mark.parametrize("value, short", [("Tutorial", "tutorial"), ("How-to guide", "howto"),
                                          ("Reference", "reference"), ("Explanation", "explanation")])
def test_the_four_types_of_document(value, short):
    doc = keys(DocType=value)
    assert validate_all({"a.md": doc}, CONFIG) == []
    assert page_from_keys("a.md", doc).doctype == short


def test_old_kind_key_and_unknown_layout_are_reported():
    doc = keys(Kind="faq", Layout="cards")
    assert codes(validate_all({"a.md": doc}, CONFIG)) == [
        "META_INVALID doc=a.md key=Kind reason=replaced_by_DocType_and_Layout",
        "META_INVALID doc=a.md key=Layout value=cards allowed=faq|tips|troubleshooting",
    ]


def test_layout_is_read():
    assert page_from_keys("faq.md", keys(DocType="Reference", Layout="faq")).layout == "faq"
