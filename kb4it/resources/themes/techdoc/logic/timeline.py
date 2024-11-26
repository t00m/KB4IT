from datetime import datetime, timedelta

from kb4it.core.service import Service
from kb4it.core.util import valid_filename
from kb4it.core.util import guess_datetime
from kb4it.core.util import get_human_datetime

class Timeline(Service):
    """Generate JSON data for TimelineJS"""

    def initialize(self):
        super(Timeline, self).__init__()
        self.get_services()

    def get_services(self):
        self.srvbes = self.get_service('Backend')
        self.srvbld = self.get_service('Builder')
        self.srvdtb = self.get_service('DB')

    def get_all(self):
        repo = self.srvbes.get_repo_parameters()
        event_types = repo['timeline']
        sortby = repo['sort'][0]
        data = {}
        data['events'] = []

        for doc in self.srvdtb.get_documents():
            if self.srvdtb.is_system(doc):
                continue
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category in event_types:
                event = {}
                title = self.srvdtb.get_values(doc, 'Title')[0]
                url = f"{doc.replace('.adoc', '.html')}"
                timestamp = self.srvdtb.get_values(doc, sortby)[0]
                dt = guess_datetime(timestamp)
                if dt is None:
                    self.log.error(f"[THEME/TIMELINE] - Error in document '{doc}' with timestamp {timestamp}")
                    continue
                human_date = get_human_datetime(dt)
                text = f"<p>Saved in Category <b>{category}</b> on {human_date}</p><p>Access to <a href='{url}' target='_top'>document</a></p>"
                event['start_date'] = {}
                event['start_date']['year'] = str(dt.year)
                event['start_date']['month'] = str(dt.month)
                event['start_date']['day'] = str(dt.day)
                event['text'] = {}
                event['text']['headline'] = title
                event['text']['text'] = text
                event['group'] = category
                data['events'].append(event)

        return data

