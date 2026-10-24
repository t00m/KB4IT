"""techdoc records: the type of work a document records, read from WorkType or from an older Category."""

from kb4it.core.util import valid_filename

# Category values that older repositories use for the type of work.
RECORD_TYPES = ('Change', 'Incident', 'Task', 'Meeting')


def work_type(srvdtb, doc_id):
    """Return the type of work of a document, or '' when it is not a record."""
    worktypes = [v for v in srvdtb.get_values(doc_id, 'WorkType') if v]
    if worktypes:
        return worktypes[0]
    for value in srvdtb.get_values(doc_id, 'Category'):
        if value in RECORD_TYPES:
            return value
    return ''


def event_type(srvdtb, doc_id):
    """Return the type of work of a document, else its first Category, else ''."""
    return work_type(srvdtb, doc_id) or srvdtb.get_values(doc_id, 'Category')[0] or ''


def docs_of_work_type(srvdtb, value):
    """Return the documents whose type of work is value, newest first, each once."""
    candidates = set(srvdtb.get_docs_by_key_value('WorkType', value))
    candidates.update(srvdtb.get_docs_by_key_value('Category', value))
    docs = [doc_id for doc_id in candidates if work_type(srvdtb, doc_id) == value]
    # sort_by_date treats an empty list as "every document"
    return srvdtb.sort_by_date(docs) if docs else []


def kind_url(srvdtb, value):
    """Return the page that lists a type of work: the WorkType page once the key is in use, else the Category page."""
    if not value:
        return ''
    key = 'WorkType' if srvdtb.get_docs_by_key_value('WorkType', value) else 'Category'
    return f"{valid_filename(key)}_{valid_filename(value)}.html"
