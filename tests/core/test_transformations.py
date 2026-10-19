"""Every transformation source can match what the compiler produces (AR-04, ARC-05)."""

import pytest

from kb4it.core.env import ENV
from kb4it.core.mdconfig import load_settings
from kb4it.services import compiler
from kb4it.services.builder import Builder

# Every construct the default extensions and PyMdown produce, plus raw HTML that documents may hold.
DOCUMENT = """Intro with a [link](https://example.org) and an ![image](a.png).

<img src="raw.png" alt="raw HTML image">

## Second level

| A | B |
|:--|--:|
| 1 | 2 |

```python
print("fenced")
```

    indented code

### Third level

!!! note
    A note.

!!! warning "Careful"
    A warning.

#### Fourth level

Footnote[^1].

##### Fifth level

- [x] done
- [ ] open

[^1]: The note.
"""


def _compiled(extensions):
    settings = load_settings({"markdown": {"extensions": extensions}})
    md = settings.new_markdown()
    html = compiler._restructure_md_sections(md.convert(DOCUMENT))
    return (compiler._md_toc_block(md.toc) or "") + html


@pytest.mark.parametrize("extensions", [[], ["pymdownx.superfences", "pymdownx.tasklist", "pymdownx.details"]])
def test_every_transformation_source_occurs(extensions):
    if extensions:
        pytest.importorskip("pymdownx")
    html = _compiled(extensions)
    common = ENV["GPATH"]["TEMPLATES"]
    missing = []
    for name in Builder._XFORM_NAMES:
        with open(f"{common}/{name}_MD.tpl", encoding="utf-8") as fh:
            pattern = fh.read()
        if not pattern or pattern not in html:
            missing.append(name)
    assert missing == [], "transformation sources the compiler never produces"
