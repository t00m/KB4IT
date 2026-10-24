"""techdoc document page: the header strip, the Summary and the banners, as plain data for the templates."""

from techdoc_dashboard import priority_css, status_css

from kb4it.core.util import valid_filename

# A document with one of these statuses must not be followed.
RETIRED_STATUSES = ('Obsolete', 'Deprecated', 'Withdrawn', 'Rejected')


def value_url(props, key, value):
    """Return the page of one value: the day's events page for Date, else the key-value page."""
    if key == 'Date':
        day = value[:10]
        if len(day) == 10 and day.replace('-', '').isdigit():
            return f"events_{day.replace('-', '')}.html"
    return props.get(f'{key}_{value}_Url') or f'{valid_filename(key)}_{valid_filename(value)}.html'


def values(srvdtb, doc_id, key):
    """Return the non-empty values of a key."""
    return [v for v in srvdtb.get_values(doc_id, key) if v]


def summary(srvdtb, doc_id):
    """Return the Summary whole; KB4IT splits values on commas, so they are joined back."""
    return ', '.join(values(srvdtb, doc_id, 'Summary'))


def header_strip(srvdtb, doc_id, conf):
    """Return the badges and links of the header strip, as set in theme.json header_keys."""
    props = srvdtb.get_doc_properties(doc_id)
    badges = []
    for key in conf.get('badges', []):
        for value in values(srvdtb, doc_id, key):
            css = {'Priority': priority_css, 'Status': status_css}.get(key, lambda _v: 'kb-label-doctype')(value)
            badges.append({'key': key, 'text': value, 'css': css, 'url': value_url(props, key, value)})
    links = []
    for key in conf.get('links', []):
        items = [{'text': v, 'url': value_url(props, key, v)} for v in values(srvdtb, doc_id, key)]
        if items:
            links.append({'key': key, 'items': items})
    return {'badges': badges, 'links': links}


def banners(srvdtb, doc_id):
    """Return the banners of a document: production, retired, then draft."""
    found = []
    if 'Production' in values(srvdtb, doc_id, 'Environment'):
        sids = values(srvdtb, doc_id, 'SID')
        text = 'This document changes production systems'
        found.append({'kind': 'prod', 'label': 'Production',
                      'text': f"{text}: {', '.join(sids)}." if sids else f'{text}.'})
    statuses = values(srvdtb, doc_id, 'Status')
    retired = [s for s in statuses if s in RETIRED_STATUSES]
    if retired:
        found.append({'kind': 'retired', 'label': retired[0], 'text': 'Do not follow this document.'})
    if 'Draft' in statuses:
        found.append({'kind': 'draft', 'label': 'Draft', 'text': 'Not final. Check with the author before you follow it.'})
    return found
