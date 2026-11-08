"""techdoc settings (P5): theme.json, then the "techdoc" block of repo.json."""

from dataclasses import dataclass, field


@dataclass
class TechdocConfig:
    header_keys: dict = field(default_factory=dict)   # badges and links of the document header strip
    info_groups: list = field(default_factory=list)   # property groups of the info card
    info_tabs: dict = field(default_factory=dict)     # tabs of the info card and whether they print
    toc_sidebar: bool = False                         # sticky table of contents; repo.json "toc_sidebar" wins
    table_filter: bool = True                         # search and sort on long document tables
    quality: dict = field(default_factory=dict)       # quality profile overrides, see quality.profile()
