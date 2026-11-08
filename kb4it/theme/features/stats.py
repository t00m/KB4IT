"""Feature stats: stats.html, numbers about the documents, their properties and links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kb4it.core.stats import collect_stats
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Site


class Stats(Feature):
    """stats.html; with the events feature on, its year and month bars link the archive pages."""

    name = "stats"
    uses = ("events",)
    options = {
        "stats_skip_keys": ("Summary",),   # free text says nothing as a count
        "reuse_unchanged_pages": False,
    }
    hooks = ("stats_keys",)
    templates = ("PAGE_STATS",)

    def stats_keys(self) -> list[str]:
        """The properties listed on the stats page."""
        return list(self.engine.srvdtb.get_theme_keys())

    def events_index(self) -> Any:
        """{year: {month: {day: [docs]}}} of the events pages, or None."""
        if self.legacy:
            return getattr(self.theme, 'events_docs', None)
        events = self.feature("events")
        return events.index if events is not None else None

    def write(self) -> None:
        engine = self.engine
        # The page shows dates and links too, so a document change makes it stale.
        if engine.srvbes.get_value('runtime', 'ncd') == 0 and self.option("reuse_unchanged_pages") and \
                engine.reuse_cached_page('stats', 'nck', 'no_changes', 'build_page_stats'):
            return
        skip = self.option("stats_skip_keys")
        keys = [key for key in self.hook("stats_keys")() if key not in skip]
        plan = engine.srvbes.get_plan()
        backlinks = (plan.backlinks if plan else None) or {}
        var = engine.get_theme_var()
        var['stats'] = collect_stats(engine.srvdtb, keys, backlinks, self.events_index())
        engine.distribute_md('stats', engine.template('PAGE_STATS').render(var=var), listing=True)
        engine.add_system_page('stats', 'Stats')

    def pages(self, site: Site) -> None:
        self.write()
