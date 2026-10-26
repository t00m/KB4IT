"""techdoc quality: score one document in five dimensions, and compare it with its peers.

Pure functions: no access to the build, only the document's Markdown, its properties and
its backlink count. Every point comes from a named Check, so the page can explain the score.
"""

import copy
import glob
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import unquote, urlsplit

from techdoc_media import resolve_src
from techdoc_quality_guide import CHECKS as GUIDE

from kb4it.core.mdlinks import bare_link_path, rewrite_md_href
from kb4it.core.util import html_id_for

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
    'introduction': 'introduction|description|overview|context|purpose|background',
    'details': 'details|discussion|explanation|background|description',
    'timeline': 'timeline|chronology|events',
    'executive summary': 'summary|overview',
    'findings': 'findings|results|analysis',
    'recommendations': 'recommendation|next steps|actions',
    'acceptance criteria': 'acceptance|criteria|definition of done',
    'attendees': 'attendees|participants',
    'action items': 'action|follow-?up|todo',
}
# Skeleton sections scored under Connected (References section), not again as skeleton sections.
CONNECTED_SECTIONS = re.compile(r'^(references|documentation|related)$')
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
    # The guide entry (quality-guide.html#<key>) and a tip on what to do, for the Quality tab.
    key: str = ''
    tip: str = ''

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
        headings = [h.strip().lower() for h in H2.findall(body) if not CONNECTED_SECTIONS.match(h.strip().lower())]
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
    checks = [Check('findable', f'{key} key', f'Add the {key} key', 1 if values(doc, key) else 0, 1,
                    'check-core-keys', f'Add "{key}: ..." to the frontmatter, between the --- lines.') for key in CORE_KEYS]
    known = prof['known_values']
    present = [key for key in known if values(doc, key)]
    ok = bool(present) and all(v in known[key] for key in present for v in values(doc, key))
    checks.append(Check('findable', 'Known values for Status, Priority and DocType',
                        'Use a known value for Status, Priority and DocType', 3 if ok else 0, 3, 'check-known-values',
                        'Use values such as Status: Released, Priority: Normal, DocType: How-to guide.'))
    checks.append(Check('findable', 'Summary key', 'Add a Summary key', 3 if values(doc, 'Summary') else 0, 3,
                        'check-summary', 'Add "Summary: one sentence on what the document is for" to the frontmatter.'))
    return checks


def _doctype_fit(doctype, body, heads):
    # Name, next step and whether the body has the shape of its DocType.
    numbered = len(NUMBERED.findall(body)) >= 3
    code = bool(FENCED.search(body))
    fits = {
        'How-to guide': ('Fits a how-to guide: numbered steps or a command', 'Add numbered steps or a command', numbered or code,
                         'Write the steps as a numbered list (1. 2. 3.), or put the command in a ``` code block.'),
        'Tutorial': ('Fits a tutorial: numbered steps and a command', 'Add numbered steps and a command', numbered and code,
                     'A tutorial needs a numbered list of steps and at least one ``` code block.'),
        'Reference': ('Fits a reference: a table or a list', 'Add a table or a list of five or more items',
                      bool(TABLE_RULE.search(body)) or len(LIST_ITEM.findall(body)) >= 5,
                      'Put the facts in a Markdown table (| a | b |) or a list of five or more items.'),
        'Explanation': ('Fits an explanation: three or more sections', 'Discuss it in three or more sections', len(heads) >= 3,
                        'Split the explanation into three or more ## sections.'),
    }
    return fits.get(doctype, ('Fits its DocType', 'Set a DocType', False,
                              'Add "DocType: How-to guide" (or Tutorial, Reference, Explanation) to the frontmatter.'))


def structured(doc, prof, skeletons):
    """Sections, context first, DocType fit and skeleton sections; empty sections and skeleton text cost points."""
    body = body_of(doc)
    heads = headings_of(body)
    lower = [h.lower() for h in heads]
    checks = [
        Check('structured', 'Two or more sections', 'Split it into two or more sections',
              5 if len(heads) >= 2 else 3 if heads else 0, 5, 'check-sections',
              'Start each part with a level-2 heading: "## Steps".'),
        Check('structured', 'Opens with context', 'Open with a Description or Introduction section',
              4 if heads and CONTEXT.search(heads[0]) else 0, 4, 'check-context',
              'Make the first section "## Introduction" (or Description, Overview) and say what the document is for.'),
    ]
    if not doc.work_type:
        name, todo, fits, tip = _doctype_fit(first(doc, 'DocType'), body, heads)
        checks.append(Check('structured', name, todo, 8 if fits else 0, 8, 'check-doctype-fit', tip))
    skeleton = skeleton_for(doc, skeletons)
    kind = (doc.work_type or first(doc, 'Category')).lower()
    weight = 16 if doc.work_type else 8
    if skeleton and skeleton.headings:
        share = weight / len(skeleton.headings)
        for index, expected in enumerate(skeleton.headings):
            maximum = (MAXIMA['structured'] - sum(check.max for check in checks)
                       if index == len(skeleton.headings) - 1 else share)
            pattern = SYNONYMS.get(expected, re.escape(expected[:6]))
            found = any(re.search(pattern, h) for h in lower)
            title = expected.capitalize()
            checks.append(Check('structured', f'{title} section', f'Add the {title} section',
                                maximum if found else 0, maximum,
                                'check-skeleton-section',
                                f'Add a "## {title}" section with its content: the {kind} skeleton expects it.'))
    else:
        checks.append(Check('structured', 'Three or more sections', 'Add a third section',
                            weight if len(heads) >= 3 else weight / 2, weight, 'check-third-section',
                            'Split the content into three or more ## sections.'))
    empty = min(len(EMPTY_SECTION.findall(body)), 2)
    if empty:
        checks.append(Check('structured', 'No empty sections', 'Fill or remove the empty section', -3 * empty, 0,
                            'check-empty-section', 'Write something under each heading, or remove the empty heading.'))
    if skeleton and skeleton.placeholders:
        lines = {LIST_MARK.sub('', line).strip() for line in body.splitlines()}
        if any(p in lines for p in skeleton.placeholders):
            checks.append(Check('structured', 'No skeleton text left', 'Replace the skeleton text', -6, 0,
                                'check-skeleton-text', 'Replace the example lines of the skeleton, such as "Step one".'))
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
    return [Check('complete', 'Long enough for its type', f'Write more: about {max(target - words, 1)} words', points, 25,
                  'check-words', f'It has {words} words; the target for its type is {target}. Code blocks do not count.')]


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
        Check('connected', 'Other documents link to it', 'Link it from another document', 4 if doc.backlinks else 0, 4,
              'check-backlinks', 'In a related document, add a link to this file: [Title](FILE-NAME.md).'),
        Check('connected', 'Links to a related document', 'Link to a related document', 3 if linked else 0, 3,
              'check-internal-link', 'Link to another document by its file name: [Restore the database](RESTORE-DB.md).'),
        Check('connected', 'Cites a source', 'Cite a source', 3 if EXTERNAL.search(body) else 0, 3,
              'check-source', 'Add a web link to the source: [SAP Note 736902](https://me.sap.com/notes/736902).'),
        Check('connected', 'References section', 'Add a References section', 3 if SOURCES.search(body) else 0, 3,
              'check-references', 'Add a "## References" section at the end, with one link per line.'),
        Check('connected', 'Image or diagram', 'Add an image or a diagram',
              2 if images or MERMAID.search(body_of(doc)) else 0, 2,
              'check-image', 'Add an image: ![What it shows](resources/images/file.png), or a ```mermaid diagram.'),
    ]
    checks += [Check('connected', f'Link to {path} works', f'Fix the broken link to {path}', -3, 0, 'check-broken-link',
                     f'No document is named {path}. Check the file name and the .md extension.') for path in broken]
    checks += [Check('connected', f'Image {src} is there', f'Add the missing image {src}', -3, 0, 'check-missing-image',
                     f'Copy the image to source/{src}, or correct the path.') for src in missing]
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
        return [Check('current', 'Final status', 'Set a final status', 20 if final else 10, 20, 'check-final-status',
                      'When the work is done, set "Status: Completed".')]
    checks = [Check('current', 'Final status', 'Set a final status', 8 if final else 3, 8, 'check-final-status',
                    'When the document is ready, set "Status: Released".')]
    age = _age_years(doc, today)
    if age is None:
        checks.append(Check('current', 'Dated', 'Set a Date', 0, 12, 'check-dated', 'Add "Date: YYYY-MM-DD" to the frontmatter.'))
    else:
        half_life = prof['half_life'].get(first(doc, 'DocType'), 4)
        checks.append(Check('current', 'Recently reviewed', f'Review it: it is {max(int(age), 0)} years old',
                            12 * 0.5 ** (max(age, 0) / half_life), 12, 'check-freshness',
                            f'Points halve every {half_life} years. Review the content, then set the Date to today.'))
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


def peer_stats(assessments):
    """Ranks and medians per peer group, for quality-index.js; retired documents are left out."""
    groups = {}
    for doc_id, a in assessments.items():
        if a.tier != 'retired':
            groups.setdefault(a.peer, []).append((doc_id, a))
    stats = {'peers': {}, 'docs': {}}
    for peer, members in sorted(groups.items()):
        median = {}
        for dim in DIMENSIONS:
            ordered = sorted(a.dims[dim] for _doc, a in members)
            median[dim] = round(ordered[(len(ordered) - 1) // 2], 1)
        stats['peers'][peer] = {'count': len(members), 'median': median}
        scores = [a.score for _doc, a in members]
        for doc_id, a in members:
            stats['docs'][html_id_for(doc_id)] = {
                'score': a.score, 'tier': a.tier, 'peer': peer,
                'rank': 1 + sum(1 for other in scores if other > a.score),
            }
    return stats


def index_js(stats):
    """The content of quality-index.js."""
    return 'window.KB_QUALITY = ' + json.dumps(stats, ensure_ascii=False, separators=(',', ':')) + ';\n'


TIER_LABELS = {'exemplary': 'Exemplary', 'complete': 'Complete', 'basic': 'Basic', 'stub': 'Stub', 'retired': 'Retired'}
DIM_LABELS = {'findable': 'Findable', 'structured': 'Structured', 'complete': 'Complete', 'connected': 'Connected',
              'current': 'Current'}


def checklist(assessment):
    """The panel's list: done items first, then next steps with the points they add, biggest first.

    Every item has the guide id it links to and a tooltip: what the check measures for a done
    item, what to do for a next step.
    """
    keys = [c for c in assessment.checks if c.dim == 'findable' and c.name.endswith(' key') and c.name != 'Summary key']
    all_keys = bool(keys) and all(c.passed for c in keys)
    done, todo = [], []
    if all_keys:
        done.append(('All core keys set', 'check-core-keys'))
    for check in assessment.checks:
        if all_keys and check in keys:
            continue
        if check.passed:
            done.append((check.name, check.key))
        elif round(check.max - check.points) > 0:
            todo.append((round(check.max - check.points), check.todo, check.key, check.tip))
    todo.sort(key=lambda item: -item[0])
    return ([{'kind': 'ok', 'text': text, 'gain': 0, 'key': key, 'tip': GUIDE.get(key, {}).get('what', '')}
             for text, key in done]
            + [{'kind': 'todo', 'text': text, 'gain': gain, 'key': key, 'tip': tip} for gain, text, key, tip in todo])
