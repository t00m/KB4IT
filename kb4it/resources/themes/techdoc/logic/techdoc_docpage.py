"""techdoc document page: header strip, Summary, banners and the Details groups, as plain data for the templates."""

import re

from techdoc_dashboard import priority_css, status_css

from kb4it.core.documents import joined_value
from kb4it.core.util import valid_filename

# Keys the Details tab never lists.
HIDDEN_KEYS = ('Title', 'Summary', 'Bookmark', 'SystemPage')

SAP_NOTE = re.compile(r'\bnotes?\s+#?(\d{5,8})\b', re.IGNORECASE)
SAP_NOTE_URL = 'https://me.sap.com/notes/'

# A document with one of these statuses must not be followed.
RETIRED_STATUSES = ('Obsolete', 'Deprecated', 'Withdrawn', 'Rejected')


def value_url(props, key, value):
    """Return the page of one value: the day's events page for Date, else the key-value page."""
    if key == 'Date':
        day = value[:10]
        if len(day) == 10 and day.replace('-', '').isdigit():
            return f"events_{day.replace('-', '')}.html"
    return props.get(f'{key}_{value}_Url') or f'{valid_filename(key)}_{valid_filename(value)}.html'


def date_parts(value):
    """Split a Date value into the day (YYYY-MM-DD) and the time without seconds (HH:MM, or '')."""
    day, _, time = value.strip().partition(' ')
    return day, time[:5]


def values(srvdtb, doc_id, key):
    """Return the non-empty values of a key."""
    return [v for v in srvdtb.get_values(doc_id, key) if v]


def summary(srvdtb, doc_id):
    """Return the Summary whole; KB4IT splits values on commas, so they are joined back."""
    return joined_value(srvdtb.get_values(doc_id, 'Summary'))


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
        items = []
        for v in values(srvdtb, doc_id, key):
            item = {'text': v, 'url': value_url(props, key, v), 'time': '', 'full': v}
            if key == 'Date':
                item['text'], item['time'] = date_parts(v)
            items.append(item)
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


def sap_notes(text):
    """Return the SAP note numbers named in a text ("note 123456"), each once, in order."""
    found = []
    for number in SAP_NOTE.findall(text or ''):
        if number not in found:
            found.append(number)
    return found


def info_groups(srvdtb, doc_id, groups, body_md):
    """Return the non-empty groups of the Details tab, then Other with every key not in a group."""
    props = srvdtb.get_doc_properties(doc_id)
    present = [k for k in srvdtb.get_custom_keys(doc_id) if k not in HIDDEN_KEYS]

    def item(key):
        return {'key': key, 'values': [{'text': v, 'url': value_url(props, key, v)} for v in values(srvdtb, doc_id, key)]}

    result = []
    listed = set()
    for group in groups:
        keys = [k for k in group.get('keys', []) if k in present]
        listed.update(group.get('keys', []))
        items = [i for i in (item(k) for k in keys) if i['values']]
        chips = bool(group.get('chips'))
        if chips:
            notes = sap_notes(body_md)
            if notes:
                items.append({'key': 'SAP note', 'values': [{'text': n, 'url': SAP_NOTE_URL + n} for n in notes]})
        if items:
            result.append({'name': group['name'], 'chips': chips, 'items': items})
    other = [i for i in (item(k) for k in present if k not in listed) if i['values']]
    if other:
        result.append({'name': 'Other', 'chips': False, 'items': other})
    return result
