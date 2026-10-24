"""techdoc quality: score one document in five dimensions, and compare it with its peers.

Pure functions: no access to the build, only the document's Markdown, its properties and
its backlink count. Every point comes from a named Check, so the page can explain the score.
"""

import copy
import glob
import os
import re
from dataclasses import dataclass, field

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
