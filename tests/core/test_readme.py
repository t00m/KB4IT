"""The About KB4IT page shows the README: title as a line, no badges, links to the repository."""

from kb4it.core import readme
from kb4it.core.readme import REPO_FILES_URL, about_markdown, readme_text

SAMPLE = """# KB4IT - A tagline

[![PyPI](https://img.shields.io/pypi/v/KB4IT)](https://pypi.org/project/KB4IT/)
![License](https://img.shields.io/badge/license-GPL-blue)

See the [help](https://t00m.github.io/KB4IT/), the [licence](LICENSE) and [a section](#usage).

```markdown
# Not a title
[a link](other.md)
```

## Usage
"""


def test_title_becomes_a_line_and_badges_go():
    text = about_markdown(SAMPLE)
    assert text.startswith("KB4IT - A tagline\n")
    assert "shields.io" not in text


def test_relative_links_point_to_the_repository():
    text = about_markdown(SAMPLE)
    assert f"[licence]({REPO_FILES_URL}LICENSE)" in text
    assert "[help](https://t00m.github.io/KB4IT/)" in text and "[a section](#usage)" in text


def test_code_blocks_are_kept_as_written():
    text = about_markdown(SAMPLE)
    assert "# Not a title\n[a link](other.md)\n" in text


def test_empty_readme_gives_nothing():
    assert about_markdown("") == ""


def test_source_checkout_reads_the_readme_file():
    assert readme_text().startswith("# KB4IT")


def test_installed_package_reads_the_description(tmp_path, monkeypatch):
    monkeypatch.setattr(readme, "_ROOT", tmp_path)

    class Meta(dict):
        def get_payload(self):
            return "# From metadata\n"

    monkeypatch.setattr(readme.importlib.metadata, "metadata", lambda name: Meta())
    assert readme_text() == "# From metadata\n"
