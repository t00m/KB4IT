"""A document's date links to its events day page only when that document is on one (themekit)."""

from types import SimpleNamespace

from kb4it.services.themekit import DocumentTheme


class _Theme(DocumentTheme):
    def event_documents(self):
        """Override: one event document."""
        self.calls = getattr(self, "calls", 0) + 1
        return ["event.md"]


def _theme(cls=_Theme):
    theme = cls.__new__(cls)
    theme.srvdtb = SimpleNamespace(get_doc_timestamp=lambda doc: "2026-01-10 10:00:00")
    return theme


def test_has_event_page_follows_event_documents_once():
    theme = _theme()
    assert theme.has_event_page("event.md") and not theme.has_event_page("other.md")
    assert theme.calls == 1, "the list is read once per build"


def test_default_theme_has_no_event_pages():
    theme = DocumentTheme.__new__(DocumentTheme)
    assert theme.event_documents() == [] and not theme.has_event_page("x.md")


def test_date_cell_links_only_an_event_document():
    theme = _theme()
    assert 'href="events_20260110.html"' in theme.datatable_date_cell("2026-01-10 10:00:00", "event.md")
    cell = theme.datatable_date_cell("2026-01-10 10:00:00", "other.md")
    assert "<a " not in cell and "2026-01-10 10:00" in cell and cell.startswith('<td class="uk-text-left">')


def test_old_one_argument_override_still_works():
    class _Old(_Theme):
        def datatable_date_cell(self, timestamp):
            """Override: a theme written before the doc_id argument."""
            return f"<td>{timestamp}</td>"

    theme = _theme(_Old)
    assert theme.date_cell("2026-01-10", "event.md") == "<td>2026-01-10</td>"
