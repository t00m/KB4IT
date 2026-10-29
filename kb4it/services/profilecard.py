#!/usr/bin/python
"""
Profile card service: the profile of a person on the page of a people key value (see core/people.py).

# File: profilecard.py
# Author: Tomás Vírseda
# License: GPL v3
"""

import os
from urllib.parse import quote

from kb4it.core.mdconfig import load_settings, sanitize_html
from kb4it.core.people import PeopleSettings, Profile, person_page, person_tip
from kb4it.core.util import SOURCE_ENCODING

# Keys shown first on the card, in this order; the others follow in alphabetical order.
CARD_ORDER = ("Role", "Team", "Email", "Phone", "Chat", "Url", "Location")


def _href(key, value) -> str:
    if key == "Email":
        return f"mailto:{value}"
    if key == "Phone":
        return "tel:" + "".join(value.split())
    if key == "Url" and value.startswith(("http://", "https://")):
        return value
    return ""


class ProfileCardMixin:
    """Profile card methods of Builder."""

    def people_settings(self) -> PeopleSettings:
        """The checked repo.json "people" block (Backend loads it with the configuration)."""
        return getattr(self.srvbes, "people", None) or PeopleSettings()

    def person_tip(self, key: str, value: str) -> str:
        """Role and team of the person a people key value names, for the tooltip of the name on document pages."""
        settings = self.people_settings()
        people = getattr(self.srvdtb, "people", None)
        if key not in settings.keys or people is None or not value:
            return ""
        return person_tip(people.lookup(value), settings)

    def profile_rows(self, profile: Profile) -> list[dict]:
        """{key, value, href} of each visible profile key, in card order."""
        private = set(self.people_settings().private)
        keys = [k for k in CARD_ORDER if k in profile.values]
        keys += sorted(k for k in profile.values if k not in CARD_ORDER)
        return [{"key": key, "value": value, "href": _href(key, value)}
                for key in keys if key not in private for value in profile.values[key]]

    def _profile_body(self, profile: Profile) -> str:
        settings = getattr(self.srvbes, "markdown", None) or load_settings(self.srvbes.get_dict("repo"))
        md = settings.new_markdown()
        md.kb4it_redirects = dict(getattr(self.srvbes.get_plan(), "profile_pages", None) or {})
        body = md.convert(profile.body)
        return sanitize_html(body) if settings.sanitize else body

    def profile_actions(self, value: str, profile: Profile | None) -> dict:
        """Create and Edit links to the Add page, while the editor is on; the texts travel in the address."""
        if not self.editor_enabled():
            return {"create": "", "edit": ""}
        if profile is None:
            return {"create": f"add.html#new=person&Person={quote(value, safe='')}", "edit": ""}
        # The edit link carries the whole source: a profile with a private value gets none.
        private = set(self.people_settings().private)
        if any(profile.values.get(key) for key in private):
            return {"create": "", "edit": ""}
        path = os.path.join(self.srvbes.get_path("source"), profile.doc_id)
        try:
            with open(path, encoding=SOURCE_ENCODING) as fh:
                text = fh.read()
        except OSError:
            return {"create": "", "edit": ""}
        return {"create": "", "edit": f"add.html#edit={quote(profile.doc_id, safe='')}&text={quote(text, safe='')}"}

    def profile_card(self, key: str, value: str) -> str:
        """HTML of the profile card for a value page, or an empty string.

        A person without a profile gets a card only while the editor is on, to offer Create profile.
        """
        settings = self.people_settings()
        people = getattr(self.srvdtb, "people", None)
        if key not in settings.keys or people is None:
            return ""
        profile = people.lookup(value)
        actions = self.profile_actions(value, profile)
        if profile is None:
            if not actions["create"]:
                return ""
            var = {"person": value, "rows": [], "body": "", "alias_of": None, "actions": actions}
            return self.render_template("HTML_PROFILE_CARD", var)
        # An alias page points to the page of the Person name.
        alias_of = None if value == profile.person else {"href": person_page(profile.person, settings),
                                                          "name": profile.person}
        var = {"person": profile.person, "rows": self.profile_rows(profile), "body": self._profile_body(profile),
               "alias_of": alias_of, "actions": actions}
        return self.render_template("HTML_PROFILE_CARD", var)
