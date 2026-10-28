"""Structured data: the repo.json "seo" block and the JSON-LD of a page."""

import json

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.structured import (DEFAULT_MAP, SeoSettings, document_node, graph, iso_date, load_seo, merged_map,
                                   render_jsonld, website_node)

SAMPLE = {
    "Author": ["Tomás Vírseda"], "Date": ["2026-10-23"], "DocType": ["How-to guide"],
    "Tag": ["service", "binding", "certificate", "configuration"], "Topic": ["Security", "Connectivity"],
    "Category": ["Procedure"], "Scope": ["SAP Administration", "Security"], "Project": ["SAP Basis Maintenance"],
    "Product": ["SAP ERP", "SAP BTP"], "Protocol": ["SSL", "X.509"], "Status": ["Completed"], "WorkType": ["Knowledge"],
}


def test_no_seo_block():
    assert load_seo({}) == SeoSettings()


def test_seo_block():
    seo = load_seo({"seo": {"lang": "es-ES", "structured_data": False, "map": {"Team": "contributor:Organization",
                                                                               "Scope": None}}})
    assert seo == SeoSettings(structured_data=False, lang="es-ES",
                              map={"Team": "contributor:Organization", "Scope": None})


@pytest.mark.parametrize("block, word", [
    ([], "object"), ({"index": True}, "unknown key 'index'"), ({"structured_data": "yes"}, "true or false"),
    ({"lang": "english language"}, "language tag"), ({"lang": 3}, "language tag"), ({"map": []}, "seo.map"),
    ({"map": {"Team": 3}}, "seo.map.Team"), ({"map": {"Team": "Contributor"}}, "property:Type"),
    ({"map": {"Team": "contributor:organization"}}, "property:Type"), ({"map": {"Title": "name"}}, "mapped by KB4IT"),
    ({"map": {"Team": "headline"}}, "set by KB4IT"),
])
def test_bad_seo_block(block, word):
    with pytest.raises(ConfigError, match=word):
        load_seo({"seo": block})


def test_merged_map_later_wins_and_none_removes():
    assert merged_map({"A": "a", "B": "b"}, {"B": None, "C": "c:Thing"}) == {"A": "a", "C": "c:Thing"}


@pytest.mark.parametrize("raw, iso", [("2026-10-23", "2026-10-23"), ("2026-10-23 14:30", "2026-10-23T14:30:00"),
                                      ("20261023", "2026-10-23"), ("soon", "")])
def test_iso_date(raw, iso):
    assert iso_date(raw) == iso


def test_document_node_of_the_sample():
    node = document_node(title="Update Peppol/DRCCE Service Binding", description="Keep it up to date.",
                         values=SAMPLE, mapping=merged_map(DEFAULT_MAP), default_type="TechArticle", lang="en",
                         url="https://kb.example.org/a.html", website_id="https://kb.example.org/#website")
    assert node["@type"] == ["TechArticle", "HowTo"]
    assert node["@id"] == "https://kb.example.org/a.html#article"
    assert node["headline"] == node["name"] == "Update Peppol/DRCCE Service Binding"
    assert node["datePublished"] == "2026-10-23"
    assert node["inLanguage"] == "en"
    assert node["learningResourceType"] == "How-to guide"
    assert node["author"] == {"@type": "Person", "name": "Tomás Vírseda"}
    assert node["keywords"] == "service, binding, certificate, configuration"
    assert node["genre"] == ["Procedure", "Knowledge"]
    assert node["audience"][0] == {"@type": "Audience", "audienceType": "SAP Administration"}
    assert {"@type": "DefinedTerm", "name": "X.509"} in node["mentions"]
    assert node["isPartOf"] == [{"@type": "CreativeWorkSeries", "name": "SAP Basis Maintenance"},
                                {"@id": "https://kb.example.org/#website"}]
    assert node["creativeWorkStatus"] == "Completed"


def test_document_node_without_site_url_or_doctype():
    node = document_node(title="T", description="", values={"Tag": ["x"]}, mapping={"Tag": "keywords"},
                         default_type="BlogPosting", lang="")
    assert node == {"@type": "BlogPosting", "headline": "T", "name": "T", "keywords": "x"}


def test_website_node_with_search():
    node = website_node(name="KB", description="", lang="en", url="https://x.org/", search_url="https://x.org/search.html")
    assert node["@id"] == "https://x.org/#website"
    assert node["potentialAction"]["target"]["urlTemplate"] == "https://x.org/search.html?q={search_term_string}"


def test_render_jsonld_cannot_close_the_script():
    text = render_jsonld(graph([{"name": "</script><!-- & -->"}]))
    assert "<" not in text and ">" not in text and "&" not in text
    assert json.loads(text)["@graph"][0]["name"] == "</script><!-- & -->"
