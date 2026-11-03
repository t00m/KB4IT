"""Data of the events page: the event day of each document and the counts the calendar panel draws."""

import json
from collections import Counter

EVENTS_TABLE = 'kb4it-events-table'


def event_days(events_docs):
    """Return {document: 'YYYY-MM-DD'} from events_docs, which maps year, month and day to documents."""
    days = {}
    for year, months in events_docs.items():
        for month, month_days in months.items():
            for day, docs in month_days.items():
                for doc in docs:
                    days[doc] = f'{year:04d}-{month:02d}-{day:02d}'
    return days


def calendar_json(days):
    """Return the JSON the calendar panel reads: {"days": {"YYYY-MM-DD": number of events}}, safe inside <script>."""
    counts = dict(sorted(Counter(days.values()).items()))
    return json.dumps({'days': counts}, separators=(',', ':')).replace('</', '<\\/')
