"""techdoc dashboard: the home page with its panels of statistics, open items and events."""

from calendar import monthrange
from datetime import datetime, timedelta

from kb4it.core.util import guess_datetime, html_id_for, valid_filename

PRIORITY_RANK = {
    'Critical': 0,
    'Very high': 1,
    'High': 2,
    'Medium': 3,
    'Normal': 4,
    'Low': 5,
}

PRIORITY_CSS = {
    'Critical': 'uk-label-danger',
    'Very high': 'uk-label-danger',
    'High': 'uk-label-danger',
    'Medium': 'uk-label-warning',
    'Normal': 'uk-label-warning',
    'Low': 'kb-label-muted',
    'Unknown': 'kb-label-muted',
}

STATUS_CSS = {
    'New': 'uk-label-danger',
    'Open': 'uk-label-danger',
    'Draft': 'uk-label-warning',
    'Planned': 'uk-label-warning',
    'Completed': 'uk-label-success',
    'Finished': 'uk-label-success',
    'Released': 'uk-label-success',
    'Successful': 'uk-label-success',
    'Deprecated': 'kb-label-muted',
    'Obsolete': 'kb-label-muted',
}

OPEN_STATUSES = {'New', 'Open', 'Draft', 'Planned'}

OPEN_ITEM_CATEGORIES = ['Incident', 'Change', 'Task']


def priority_css(value):
    """Return the label modifier class for a Priority value."""
    return PRIORITY_CSS.get(value, 'kb-label-muted')


def status_css(value):
    """Return the label modifier class for a Status value."""
    return STATUS_CSS.get(value, 'kb-label-muted')


class DashboardMixin:
    """Home page of techdoc (index.html); part of techdoc's Theme class."""

    def build_page_index(self, var):
        """Create landing page."""
        repo = self.srvbes.get_dict('repo')
        runtime = self.srvbes.get_dict('runtime')
        filenames = runtime['docs']['filenames']
        now = datetime.now()
        var['dt_now'] = now

        if 'index.md' in filenames:
            self.log.info("[THEME] INDEX_SKIP reason=user_generated")
            return

        var['page']['title'] = var['repo']['title']
        var['page']['stats'] = self._build_index_stats()
        var['page']['open_items'] = self._build_index_open_items()
        var['page']['alert_bar'] = self._build_index_alert_bar()
        var['page']['diataxis'] = self._build_index_diataxis()
        var['page']['events_panel'] = self._build_index_events_panel(now)
        var['page']['recent_events'] = self._build_index_recent_events(now)
        var['page']['monitoring_panel'] = self._build_index_monitoring_panel()

        page = self.template('PAGE_INDEX').render(var=var)
        self.distribute_md('index', page)

        self.srvdtb.add_document('index.md')
        self.srvdtb.add_document_key('index.md', 'Title', var['repo']['title'])
        self.srvdtb.add_document_key('index.md', 'SystemPage', 'Yes')

    def _build_index_stats(self):
        """Counters shown in the hero stats bar."""
        count_docs = 0
        count_bookmarks = 0
        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            count_docs += 1
            bookmark = self.srvdtb.get_values(docId, 'Bookmark')[0]
            if bookmark in ('Yes', 'True'):
                count_bookmarks += 1

        count_authors = len(self.srvdtb.get_all_values_for_key('Author'))
        count_categories = len(self.srvdtb.get_all_values_for_key('Category'))

        count_events = 0
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    count_events += len(self.events_docs[year][month][day])

        return [
            {'num': count_docs,       'label': 'Documents',  'url': 'all.html'},
            {'num': count_authors,    'label': 'Authors',    'url': 'Author.html'},
            {'num': count_categories, 'label': 'Categories', 'url': 'Category.html'},
            {'num': count_events,     'label': 'Events',     'url': 'events.html'},
            {'num': count_bookmarks,  'label': 'Bookmarks',  'url': 'bookmarks.html'},
        ]

    def _index_doc_row(self, docId):
        """Build one index row dict with badge data for a document."""
        props = self.srvdtb.get_doc_properties(docId)
        title = props.get('Title', docId)
        if isinstance(title, list):
            title = title[0] if title else docId
        url = props.get('Title_Url', html_id_for(docId))
        ts = self.srvdtb.get_doc_timestamp(docId)
        date = ''
        if ts:
            try:
                dt = guess_datetime(ts)
                date = dt.strftime('%b %d') if dt else ts[:10]
            except Exception:
                date = ts[:10]
        category = self.srvdtb.get_values(docId, 'Category')[0]
        priority = self.srvdtb.get_values(docId, 'Priority')[0]
        status = self.srvdtb.get_values(docId, 'Status')[0]
        return {
            'date': date,
            'timestamp': ts or '',
            'title': title,
            'url': url,
            'category': category,
            'priority': priority,
            'priority_css': priority_css(priority) if priority else '',
            'status': status,
            'status_css': status_css(status) if status else '',
        }

    def _build_index_alert_bar(self, limit=5):
        """Recent changes and incidents for the alert bar below the hero."""
        def _rows(category):
            rows = []
            for docId in self.srvdtb.get_docs_by_key_value('Category', category)[:limit]:
                rows.append(self._index_doc_row(docId))
            return rows

        return {
            'changes': _rows('Change'),
            'incidents': _rows('Incident'),
        }

    def _build_index_open_items(self, limit=7):
        """Incidents, changes and tasks whose Status is still open.

        Rows are ranked by Priority first, then by date, newest first.
        Documents without a Status never show up here, so repositories
        that do not use the property keep a clean index.
        """
        rows = []
        for category in OPEN_ITEM_CATEGORIES:
            for docId in self.srvdtb.get_docs_by_key_value('Category', category):
                if self.srvdtb.is_system(docId):
                    continue
                status = self.srvdtb.get_values(docId, 'Status')[0]
                if status not in OPEN_STATUSES:
                    continue
                rows.append(self._index_doc_row(docId))
        rows.sort(key=lambda r: r['timestamp'], reverse=True)
        rows.sort(key=lambda r: PRIORITY_RANK.get(r['priority'], len(PRIORITY_RANK)))
        return rows[:limit]

    def _build_index_diataxis(self):
        """Diátaxis cards,  one per DocType value."""
        diataxis = [
            {'name': 'Tutorial',     'css': 'tutorial',    'icon': 'bolt',
             'label': 'Tutorials',
             'desc': 'Learning-oriented lessons that take you through a series of steps.'},
            {'name': 'How-to guide', 'css': 'howto',       'icon': 'cog',
             'label': 'How-to guides',
             'desc': 'Goal-oriented recipes to solve a specific problem.'},
            {'name': 'Reference',    'css': 'reference',   'icon': 'file-text',
             'label': 'Reference',
             'desc': 'Information-oriented technical descriptions of the machinery.'},
            {'name': 'Explanation',  'css': 'explanation', 'icon': 'comment',
             'label': 'Explanations',
             'desc': 'Understanding-oriented discussions that clarify a topic.'},
        ]
        key = 'DocType'
        for item in diataxis:
            docs = self.srvdtb.get_docs_by_key_value(key, item['name'])
            item['count'] = len(docs)
            item['url'] = "%s_%s.html" % (valid_filename(key), valid_filename(item['name'])) if docs else None
        return diataxis

    def _build_index_events_panel(self, now):
        """Rows for current and next month events."""
        cur_first = now.replace(day=1)
        cur_last = cur_first.replace(day=monthrange(cur_first.year, cur_first.month)[1])
        nxt_first = cur_last + timedelta(days=1)

        today = now.date()

        def rows_for(year, month):
            rows = []
            try:
                days = self.events_docs[year][month]
            except KeyError:
                return rows
            for day in sorted(days.keys()):
                if datetime(year, month, day).date() < today:
                    continue
                for docId in days[day]:
                    props = self.srvdtb.get_doc_properties(docId)
                    title = props.get('Title', docId)
                    if isinstance(title, list):
                        title = title[0] if title else docId
                    url = props.get('Title_Url', html_id_for(docId))
                    categories = self.srvdtb.get_values(docId, 'Category')
                    category = categories[0] if categories and categories[0] else ''
                    rows.append({
                        'date': datetime(year, month, day).strftime('%b %d'),
                        'title': title,
                        'url': url,
                        'category': category,
                    })
            return rows

        return {
            'current': {
                'label': '%s · Current' % cur_first.strftime('%B %Y'),
                'url': 'events_%04d%02d.html' % (cur_first.year, cur_first.month),
                'rows': rows_for(cur_first.year, cur_first.month),
            },
            'next': {
                'label': '%s · Next' % nxt_first.strftime('%B %Y'),
                'url': 'events_%04d%02d.html' % (nxt_first.year, nxt_first.month),
                'rows': rows_for(nxt_first.year, nxt_first.month),
            },
        }

    def _build_index_recent_events(self, now):
        """Events from yesterday back to one month ago, newest first."""
        yesterday = datetime(now.year, now.month, now.day) - timedelta(days=1)
        month_ago_month = now.month - 1 if now.month > 1 else 12
        month_ago_year = now.year if now.month > 1 else now.year - 1
        month_ago_day = min(now.day, monthrange(month_ago_year, month_ago_month)[1])
        month_ago = datetime(month_ago_year, month_ago_month, month_ago_day)

        rows = []
        for year in sorted(self.events_docs.keys()):
            for month in sorted(self.events_docs[year].keys()):
                for day in sorted(self.events_docs[year][month].keys()):
                    d = datetime(year, month, day)
                    if d < month_ago or d > yesterday:
                        continue
                    for docId in self.events_docs[year][month][day]:
                        props = self.srvdtb.get_doc_properties(docId)
                        title = props.get('Title', docId)
                        if isinstance(title, list):
                            title = title[0] if title else docId
                        url = props.get('Title_Url', html_id_for(docId))
                        categories = self.srvdtb.get_values(docId, 'Category')
                        category = categories[0] if categories and categories[0] else ''
                        rows.append({
                            'date': d.strftime('%b %d'),
                            'title': title,
                            'url': url,
                            'category': category,
                        })
        rows.reverse()
        return rows

    def _build_index_monitoring_panel(self):
        """Articles with Topic=Monitoring, grouped by Periodicity."""
        monitoring_docs = self.srvdtb.get_docs_by_key_value('Topic', 'Monitoring')
        groups = {}
        for docId in monitoring_docs:
            if self.srvdtb.is_system(docId):
                continue
            props = self.srvdtb.get_doc_properties(docId)
            title = props.get('Title', docId)
            if isinstance(title, list):
                title = title[0] if title else docId
            url = props.get('Title_Url', html_id_for(docId))
            periodicities = self.srvdtb.get_values(docId, 'Periodicity')
            if not periodicities or not periodicities[0]:
                continue
            periodicity = periodicities[0]
            groups.setdefault(periodicity, []).append({'title': title, 'url': url})

        return [
            {
                'periodicity': p,
                'url': 'Periodicity_%s.html' % p.replace(' ', '_'),
                'rows': groups[p],
            }
            for p in sorted(groups.keys())
        ]
