"""techdoc Quality page: quick wins, possible duplicates and the tier mix, from the assessments."""

import re

LIVE_TIERS = ('exemplary', 'complete', 'basic', 'stub')
WORD = re.compile(r'[a-z0-9]{3,}')
# Parts of a title that only date it: numbers, months, weekdays.
DATE_WORD = re.compile(r'^(\d+|january|february|march|april|may|june|july|august|september|october|november|'
                       r'december|monday|tuesday|wednesday|thursday|friday|saturday|sunday)$')


def quick_wins(assessments, prof, limit=50):
    """Documents within 5 points of the next tier with one missing check that gets them there."""
    thresholds = {'stub': ('basic', prof['tiers']['basic']), 'basic': ('complete', prof['tiers']['complete']),
                  'complete': ('exemplary', prof['tiers']['exemplary'])}
    wins = []
    for doc, a in assessments.items():
        if a.tier not in thresholds:
            continue
        nxt, threshold = thresholds[a.tier]
        missing = threshold - a.score
        if missing > 5:
            continue
        gains = [(round(c.max - c.points), c) for c in a.checks if not c.passed and round(c.max - c.points) >= missing]
        if not gains:
            continue
        gain, best = min(gains, key=lambda item: item[0])
        wins.append({'doc': doc, 'score': a.score, 'tier': a.tier, 'next': nxt, 'missing': missing,
                     'check': best.todo, 'key': best.key, 'gain': gain})
    wins.sort(key=lambda w: (w['missing'], -w['score'], w['doc']))
    return wins[:limit]


def _words(title):
    return set(WORD.findall(title.lower()))


def duplicates(titles, threshold=0.8):
    """Pairs of documents whose titles share most words; titles that differ only by a date are left out."""
    words = {doc: _words(title) for doc, title in titles.items()}
    undated = {doc: {w for w in ws if not DATE_WORD.match(w)} for doc, ws in words.items()}
    docs = sorted(d for d in titles if words[d])
    pairs = []
    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            union = words[a] | words[b]
            score = len(words[a] & words[b]) / len(union)
            if score >= threshold and undated[a] != undated[b]:
                pairs.append((a, b, round(score, 2)))
    return pairs


def tier_mix(assessments):
    """Per peer group: live documents per tier, with percentages; largest groups first."""
    groups = {}
    for a in assessments.values():
        if a.tier in LIVE_TIERS:
            groups.setdefault(a.peer, []).append(a.tier)
    mix = []
    for peer, tiers in groups.items():
        counts = {t: tiers.count(t) for t in LIVE_TIERS}
        mix.append({'peer': peer, 'total': len(tiers), 'counts': counts,
                    'pct': {t: round(100 * counts[t] / len(tiers), 1) for t in LIVE_TIERS}})
    mix.sort(key=lambda m: (-m['total'], m['peer']))
    return mix
