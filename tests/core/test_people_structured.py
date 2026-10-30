"""Author profiles in the structured data: one schema.org Person per person, a ProfilePage on their page."""

import json
import re

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.people import first_paragraph, load_people
from kb4it.core.structured import person_node, profile_page_node
from tests.core.test_profile_card import JANE, doc, html, site

SITE = "https://kb.example.org/"


def jsonld(text):
    found = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL)
    return json.loads(found.group(1))["@graph"] if found else []


def test_person_node_maps_profile_keys():
    node = person_node(name="Jane Doe", iri=SITE + "Author_Jane_Doe.html#person", aliases=["J. Doe"],
                       values={"Role": ["DBA"], "Team": ["SAP Basis"], "Email": ["j@x.org"]},
                       mapping={"Role": "jobTitle", "Team": "memberOf:Organization", "Email": "email"}, description="Bio.")
    assert node == {"@type": "Person", "@id": SITE + "Author_Jane_Doe.html#person", "name": "Jane Doe",
                    "alternateName": "J. Doe", "description": "Bio.", "jobTitle": "DBA",
                    "memberOf": {"@type": "Organization", "name": "SAP Basis"}, "email": "j@x.org"}
    page = profile_page_node(person=node, lang="en", url=SITE + "Author_Jane_Doe.html", website_id=SITE + "#website")
    assert page["@type"] == "ProfilePage" and page["mainEntity"]["@id"] == node["@id"]


def test_first_paragraph_skips_headings_and_markup():
    assert first_paragraph("# Jane\n\nRuns the **rota**, see [the list](a.md).\n\nMore.") == "Runs the rota, see the list."


@pytest.mark.parametrize("block, words", [
    ({"map": []}, "'people.map' must be an object"),
    ({"map": {"Alias": "name"}}, "Alias is mapped by KB4IT"),
    ({"map": {"Badge": "name"}}, "name is set by KB4IT"),
    ({"map": {"Badge": "Bad"}}, "must look like"),
])
def test_bad_people_map(block, words):
    with pytest.raises(ConfigError, match=re.escape(words)):
        load_people({"people": block})


def test_people_map_is_read():
    assert load_people({"people": {"map": {"Badge": "identifier", "Url": None}}}).map == {"Badge": "identifier", "Url": None}


def test_documents_point_to_the_person_with_aliases_resolved(tmp_path, home):
    jane = JANE.replace("---\n", "---\nAlias: J. Doe\n", 1)
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="J. Doe"), "b.md": doc("Beta", Author="Bob"),
                                   "PERSON-JANE-DOE.md": jane}, site_url=SITE)
    article = jsonld(html(target, "a.html"))[0]
    assert article["author"] == {"@type": "Person", "@id": SITE + "Author_Jane_Doe.html#person", "name": "Jane Doe"}
    assert jsonld(html(target, "b.html"))[0]["author"]["@id"] == SITE + "Author_Bob.html#person"


def test_person_page_has_a_profile_page(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": JANE},
                  site_url=SITE, people={"private": ["Phone"], "map": {"Badge": "identifier"}})
    nodes = jsonld(html(target, "Author_Jane_Doe.html"))
    page = next(n for n in nodes if n["@type"] == "ProfilePage")
    person = page["mainEntity"]
    assert person["@id"] == SITE + "Author_Jane_Doe.html#person" and person["jobTitle"] == "Basis admin"
    assert person["email"] == "j@x.org" and person["identifier"] == "42" and person["description"] == "Bio with bold."
    assert "telephone" not in person
    assert not any(n["@type"] == "ProfilePage" for n in jsonld(html(target, "Tag_x.html")))


def test_without_site_url_the_person_has_no_id(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": JANE})
    assert jsonld(html(target, "a.html"))[0]["author"] == {"@type": "Person", "name": "Jane Doe"}


def test_person_iri_with_and_without_person_pages():
    from types import SimpleNamespace

    from kb4it.core.people import PeopleSettings
    from kb4it.services.headmeta import HeadMetaMixin

    mixin = HeadMetaMixin()
    mixin.srvbes = SimpleNamespace(site_url=SITE, people=PeopleSettings())
    assert mixin.person_iri("Jane Doe") == SITE + "Author_Jane_Doe.html#person"
    mixin.person_pages = False
    assert mixin.person_iri("Jane Doe") == SITE + "#person-Jane_Doe"
    mixin.srvbes.site_url = ""
    assert mixin.person_iri("Jane Doe") == ""
