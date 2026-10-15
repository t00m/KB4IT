"""State belongs to one build: nothing a build sets leaks into the next one in the same process (AR-05, ARC-06)."""

from kb4it.services.builder import Builder


class _App:
    def get_service(self, name):
        return object()


def _started_builder():
    builder = Builder()
    builder.start(_App())
    return builder


def test_builders_do_not_share_theme_variables():
    first, second = _started_builder(), _started_builder()
    first.theme_var["x"] = 1
    assert second.theme_var == {}
    assert "theme_var" not in vars(Builder)
    assert first.templates is not second.templates
