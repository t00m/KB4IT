"""The public API for themes.

A theme imports from this module only:

    from kb4it.theme import BaseTheme

    class Theme(BaseTheme):
        features = ("documents", "search")

        def build(self, site):
            site.page("index", "Home", self.render("PAGE_INDEX", documents=list(site.documents)))

Anything else in KB4IT is internal and may change in any release; theme.internals
reaches it when this module does not cover a need yet. See "Write a theme" in the help.
"""

from kb4it.core.checks import Problem
from kb4it.core.exceptions import ThemeError
from kb4it.core.log import q
from kb4it.core.util import slugify
from kb4it.theme.base import BaseTheme
from kb4it.theme.feature import Feature
from kb4it.theme.features import FEATURES
from kb4it.theme.site import Doc, Site, Table, page_name

__all__ = ["FEATURES", "BaseTheme", "Doc", "Feature", "Problem", "Site", "Table", "ThemeError", "page_name", "q",
           "slugify"]
