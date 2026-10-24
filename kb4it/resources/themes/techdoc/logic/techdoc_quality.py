"""techdoc quality: score one document in five dimensions, and compare it with its peers.

Pure functions: no access to the build, only the document's Markdown, its properties and
its backlink count. Every point comes from a named Check, so the page can explain the score.
"""

import copy
import glob
import os
import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import unquote, urlsplit

from techdoc_media import resolve_src

from kb4it.core.mdlinks import bare_link_path, rewrite_md_href

DIMENSIONS = ('findable', 'structured', 'complete', 'connected', 'current')
MAXIMA = {'findable': 15, 'structured': 25, 'complete': 25, 'connected': 15, 'current': 20}

DEFAULTS = {
    'enabled': True,
    'tiers': {'exemplary': 75, 'complete': 60, 'basic': 40},
    'targets': {'How-to guide': 150, 'Reference': 200, 'Explanation': 500, 'Tutorial': 800},
    'record_target': 60,
    'half_life': {'How-to guide': 3, 'Tutorial': 3, 'Reference': 4, 'Explanation': 8},
    'final_status': ['Released', 'Completed', 'Finished', 'Successful'],
    'retired_status': ['Obsolete', 'Deprecated', 'Withdrawn', 'Rejected'],
    'known_values': {
        'Status': ['New', 'Open', 'Draft', 'Planned', 'Completed', 'Released', 'Finished', 'Successful',
                   'Deprecated', 'Obsolete', 'Withdrawn', 'Rejected'],
        'Priority': ['Critical', 'Very high', 'High', 'Medium', 'Normal', 'Low'],
        'DocType': ['Tutorial', 'How-to guide', 'Reference', 'Explanation'],
    },
}

CORE_KEYS = ('Author', 'Date', 'DocType', 'Category', 'Status', 'Tag', 'Topic', 'Scope', 'Product')
CONTEXT = re.compile(r'description|introduction|overview|summary|objective|context|problem', re.IGNORECASE)
# Skeleton section names and the headings that count as the same section.
SYNONYMS = {
    'steps': 'steps|procedure',
    'description': 'description|overview|introduction',
    'summary': 'summary|description|overview',
    'overview': 'overview|description|introduction|information',
    'impact': 'impact|scope|risk|justification',
    'rollback': 'rollback|fallback|back-?out',
    'objective': 'objective|overview|description|introduction',
    'verification': 'verif|validation|check',
    'resolution': 'resolution|solution|fix',
}
FRONTMATTER = re.compile(r'\A---\n.*?\n---[ \t]*\n?', re.DOTALL)
FENCED = re.compile(r'^(```|~~~).*?^\1[^\n]*$', re.MULTILINE | re.DOTALL)
H2 = re.compile(r'^## +(.+?)\s*$', re.MULTILINE)
NUMBERED = re.compile(r'^\s*\d+\.\s', re.MULTILINE)
LIST_ITEM = re.compile(r'^\s*([-*]|\d+\.)\s', re.MULTILINE)
TABLE_RULE = re.compile(r'^\|?\s*:?-{3,}', re.MULTILINE)
EMPTY_SECTION = re.compile(r'^#{2,4} .+\n\s*(?=^#{1,4} |\Z)', re.MULTILINE)
LIST_MARK = re.compile(r'^\s*([-*+]|\d+[.)])\s+')
TITLE_LINE = re.compile(r'^# .*$', re.MULTILINE)
WORD = re.compile(r'\w+')
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)')
IMAGE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')
EXTERNAL = re.compile(r'\]\(https?://|<https?://')
SOURCES = re.compile(r'^## +(references|documentation|related)', re.IGNORECASE | re.MULTILINE)
MERMAID = re.compile(r'^(```|~~~)\s*mermaid', re.MULTILINE)


@dataclass
class Skeleton:
    headings: list
    placeholders: list


@dataclass
class Check:
    dim: str
    name: str
    todo: str
    points: float
    max: float

    @property
    def passed(self):
        return self.points >= self.max


@dataclass
class Assessment:
    score: int
    tier: str
    dims: dict
    checks: list
    peer: str


@dataclass
class DocInput:
    text: str
    meta: dict
    backlinks: int = 0
    known_docs: set = field(default_factory=set)
    source_dir: str = ''
    work_type: str = ''


def profile(theme_conf):
    """Return the quality settings: the defaults, updated key by key from theme.json "quality"."""
    prof = copy.deepcopy(DEFAULTS)
    for key, value in (theme_conf or {}).get('quality', {}).items():
        if isinstance(value, dict) and isinstance(prof.get(key), dict):
            prof[key].update(value)
        else:
            prof[key] = value
    return prof


def load_skeletons(folder):
    """Return the skeletons of a folder by their upper-case prefix (PROCEDURE, CHANGE, ...)."""
    found = {}
    for path in sorted(glob.glob(os.path.join(folder, '*-SKELETON.md'))):
        name = os.path.basename(path).rsplit('-SKELETON', 1)[0].upper()
        with open(path, encoding='utf-8') as fh:
            body = FRONTMATTER.sub('', fh.read().replace('\r\n', '\n'))
        headings = [h.strip().lower() for h in H2.findall(body)]
        placeholders = []
        for line in body.splitlines():
            if not line.strip() or line.lstrip().startswith(('#', '|', '```', '~~~')):
                continue
            text = LIST_MARK.sub('', line).strip()
            if len(text) >= 8 or text.lower().startswith('step '):
                placeholders.append(text)
        found[name] = Skeleton(headings, placeholders)
    return found


def values(doc, key):
    """The non-empty values of a key."""
    return [v for v in doc.meta.get(key) or [] if v]


def first(doc, key):
    found = values(doc, key)
    return found[0] if found else ''


def body_of(doc):
    """The Markdown after the frontmatter, with Unix line endings."""
    return FRONTMATTER.sub('', doc.text.replace('\r\n', '\n'), count=1)


def headings_of(body):
    return [h.strip() for h in H2.findall(body)]


def skeleton_for(doc, skeletons):
    """The skeleton a document is judged against: its WorkType for records, else its first Category."""
    name = doc.work_type or first(doc, 'Category')
    return skeletons.get(name.upper()) if name else None


def findable(doc, prof):
    """Core keys (1 each), known values (3) and a Summary (3)."""
    checks = [Check('findable', f'{key} key', f'Add the {key} key', 1 if values(doc, key) else 0, 1) for key in CORE_KEYS]
    known = prof['known_values']
    present = [key for key in known if values(doc, key)]
    ok = bool(present) and all(v in known[key] for key in present for v in values(doc, key))
    checks.append(Check('findable', 'Known values for Status, Priority and DocType',
                        'Use a known value for Status, Priority and DocType', 3 if ok else 0, 3))
    checks.append(Check('findable', 'Summary key', 'Add a Summary key', 3 if values(doc, 'Summary') else 0, 3))
    return checks


def _doctype_fit(doctype, body, heads):
    # Name, next step and whether the body has the shape of its DocType.
    numbered = len(NUMBERED.findall(body)) >= 3
    code = bool(FENCED.search(body))
    fits = {
        'How-to guide': ('Fits a how-to guide: numbered steps or a command', 'Add numbered steps or a command', numbered or code),
        'Tutorial': ('Fits a tutorial: numbered steps and a command', 'Add numbered steps and a command', numbered and code),
        'Reference': ('Fits a reference: a table or a list', 'Add a table or a list of five or more items',
                      bool(TABLE_RULE.search(body)) or len(LIST_ITEM.findall(body)) >= 5),
        'Explanation': ('Fits an explanation: three or more sections', 'Discuss it in three or more sections', len(heads) >= 3),
    }
    return fits.get(doctype, ('Fits its DocType', 'Set a DocType', False))


def structured(doc, prof, skeletons):
    """Sections, context first, DocType fit and skeleton sections; empty sections and skeleton text cost points."""
    body = body_of(doc)
    heads = headings_of(body)
    lower = [h.lower() for h in heads]
    checks = [
        Check('structured', 'Two or more sections', 'Split it into two or more sections',
              5 if len(heads) >= 2 else 3 if heads else 0, 5),
        Check('structured', 'Opens with context', 'Open with a Description or Introduction section',
              4 if heads and CONTEXT.search(heads[0]) else 0, 4),
    ]
    if not doc.work_type:
        name, todo, fits = _doctype_fit(first(doc, 'DocType'), body, heads)
        checks.append(Check('structured', name, todo, 8 if fits else 0, 8))
    skeleton = skeleton_for(doc, skeletons)
    weight = 16 if doc.work_type else 8
    if skeleton and skeleton.headings:
        share = weight / len(skeleton.headings)
        for expected in skeleton.headings:
            pattern = SYNONYMS.get(expected, re.escape(expected[:6]))
            found = any(re.search(pattern, h) for h in lower)
            checks.append(Check('structured', f'{expected.capitalize()} section', f'Add the {expected.capitalize()} section',
                                share if found else 0, share))
    else:
        checks.append(Check('structured', 'Three or more sections', 'Add a third section',
                            weight if len(heads) >= 3 else weight / 2, weight))
    empty = min(len(EMPTY_SECTION.findall(body)), 2)
    if empty:
        checks.append(Check('structured', 'No empty sections', 'Fill or remove the empty section', -3 * empty, 0))
    if skeleton and skeleton.placeholders:
        lines = {LIST_MARK.sub('', line).strip() for line in body.splitlines()}
        if any(p in lines for p in skeleton.placeholders):
            checks.append(Check('structured', 'No skeleton text left', 'Replace the skeleton text', -6, 0))
    return checks


def words_of(body):
    """Words of the body, without the title line and fenced code."""
    return len(WORD.findall(TITLE_LINE.sub('', FENCED.sub('', body), count=1)))


def complete(doc, prof):
    """25 points for reaching the word target of the type; at most 3 for very short documents."""
    words = words_of(body_of(doc))
    if doc.work_type:
        target, floor = prof['record_target'], 20
    else:
        target, floor = prof['targets'].get(first(doc, 'DocType'), 200), 50
    points = 25 * min(words / target, 1)
    if words < floor:
        points = min(points, 3)
    return [Check('complete', 'Long enough for its type', f'Write more: about {max(target - words, 1)} words', points, 25)]


def connected(doc, prof):
    """Backlinks, links to documents and sources, a references section, images; broken links and missing images cost points."""
    body = FENCED.sub('', body_of(doc))
    linked, broken = False, []
    for href in LINK.findall(body):
        if rewrite_md_href(href) is not None:
            path = os.path.normpath(unquote(urlsplit(href).path)).replace(os.sep, '/')
            if path in doc.known_docs:
                linked = True
            else:
                broken.append(path)
        elif bare_link_path(href) is not None:
            broken.append(bare_link_path(href))
    images = IMAGE.findall(body)
    missing = [src for src in images
               if (local := resolve_src(src, doc.source_dir)) is not None and not os.path.isfile(local)]
    checks = [
        Check('connected', 'Linked from another document', 'Link it from another document', 4 if doc.backlinks else 0, 4),
        Check('connected', 'Links to a related document', 'Link to a related document', 3 if linked else 0, 3),
        Check('connected', 'Cites a source', 'Cite a source', 3 if EXTERNAL.search(body) else 0, 3),
        Check('connected', 'References section', 'Add a References section', 3 if SOURCES.search(body) else 0, 3),
        Check('connected', 'Image or diagram', 'Add an image or a diagram',
              2 if images or MERMAID.search(body_of(doc)) else 0, 2),
    ]
    checks += [Check('connected', f'Link to {path} works', f'Fix the broken link to {path}', -3, 0) for path in broken]
    checks += [Check('connected', f'Image {src} is there', f'Add the missing image {src}', -3, 0) for src in missing]
    return checks


def _age_years(doc, today):
    try:
        return (today - date.fromisoformat(first(doc, 'Date')[:10])).days / 365.25
    except ValueError:
        return None


def current(doc, prof, today):
    """A final status, and for knowledge documents, freshness that halves with every half-life."""
    final = any(v in prof['final_status'] for v in values(doc, 'Status'))
    if doc.work_type:
        return [Check('current', 'Final status', 'Set a final status', 20 if final else 10, 20)]
    checks = [Check('current', 'Final status', 'Set a final status', 8 if final else 3, 8)]
    age = _age_years(doc, today)
    if age is None:
        checks.append(Check('current', 'Dated', 'Set a Date', 0, 12))
    else:
        half_life = prof['half_life'].get(first(doc, 'DocType'), 4)
        checks.append(Check('current', 'Recently reviewed', f'Review it: it is {max(int(age), 0)} years old',
                            12 * 0.5 ** (max(age, 0) / half_life), 12))
    return checks


def tier_of(score, status, prof):
    """The tier of a score; retired when any Status value is a retired status."""
    if any(v in prof['retired_status'] for v in status):
        return 'retired'
    tiers = prof['tiers']
    if score >= tiers['exemplary']:
        return 'exemplary'
    if score >= tiers['complete']:
        return 'complete'
    if score >= tiers['basic']:
        return 'basic'
    return 'stub'


def peer_of(doc):
    """The group a document is compared with: its WorkType for records, else its DocType."""
    return doc.work_type or first(doc, 'DocType') or 'Other'


def assess(doc, prof, skeletons, today):
    """Score one document: every check, the five dimensions (0 to their maximum), the total and the tier."""
    checks = findable(doc, prof) + structured(doc, prof, skeletons) + complete(doc, prof) + connected(doc, prof) \
        + current(doc, prof, today)
    dims = {d: max(0, min(MAXIMA[d], sum(c.points for c in checks if c.dim == d))) for d in DIMENSIONS}
    score = round(sum(dims.values()))
    return Assessment(score, tier_of(score, values(doc, 'Status'), prof), dims, checks, peer_of(doc))
