"""techdoc quality guide: what each quality check measures and how to meet it.

One entry per check id. The Quality tab uses "what" as the tooltip of a passed item and
links every item to the guide page (quality-guide.html#<id>), which shows "how" and the
Markdown "example".
"""

DIMS = {
    'findable': ('Findable', 'Can a reader find the document and know what it is? Points for the frontmatter keys, known values and a Summary.'),
    'structured': ('Structured', 'Is it organised like its kind? Points for sections, a first section that gives context, the shape of its type and the sections of its skeleton.'),
    'complete': ('Complete', 'Is there enough of it? Points for words, up to the target of its type.'),
    'connected': ('Connected', 'Is it part of the knowledge base? Points for links to and from other documents, sources, references and images.'),
    'current': ('Current', 'Can a reader trust it today? Points for a final status and a recent Date.'),
}

CHECKS = {
    'check-core-keys': {
        'title': 'Core keys',
        'dim': 'findable',
        'what': 'The frontmatter has the core keys: Author, Date, DocType, Category, Status, Tag, Topic, Scope and Product.',
        'how': 'Add each missing key to the frontmatter, between the two `---` lines at the top of the file. One point per key.',
        'example': '---\nAuthor: Ana Pérez\nDate: 2026-10-24\nDocType: How-to guide\nCategory: Procedure\nStatus: Released\n'
                   'Tag: certificate, renewal\nTopic: Security\nScope: SAP Administration\nProduct: ADS\n---',
    },
    'check-known-values': {
        'title': 'Known values',
        'dim': 'findable',
        'what': 'Status, Priority and DocType use values the theme knows, so lists, colours and filters work.',
        'how': 'Use one of these values. Status: New, Open, Draft, Planned, Completed, Released, Finished, Successful, '
               'Deprecated, Obsolete, Withdrawn, Rejected. Priority: Critical, Very high, High, Medium, Normal, Low. '
               'DocType: Tutorial, How-to guide, Reference, Explanation. The list is in the `quality` block of `theme.json`.',
        'example': 'Status: Released\nPriority: Normal\nDocType: How-to guide',
    },
    'check-summary': {
        'title': 'Summary',
        'dim': 'findable',
        'what': 'A one-sentence Summary says what the document is for. It shows under the title, in search results and in link previews.',
        'how': 'Add a `Summary` key with one sentence. Put it in double quotes when it contains a colon.',
        'example': 'Summary: "Renew the Adobe ReaderRights credential before it expires and register it in ADS."',
    },
    'check-sections': {
        'title': 'Two or more sections',
        'dim': 'structured',
        'what': 'The body is split into `##` sections, so readers can skim it and the table of contents works.',
        'how': 'Start each part with a level-2 heading. One section gives 3 of the 5 points.',
        'example': '## Description\n\nWhat this is about.\n\n## Steps\n\n1. First step.',
    },
    'check-context': {
        'title': 'Opens with context',
        'dim': 'structured',
        'what': 'The first section gives context: Description, Introduction, Overview, Summary, Objective, Context or Problem.',
        'how': 'Make the first `##` section one of those names, and say in a few lines what the document is for and when to use it.',
        'example': '## Introduction\n\nThe ReaderRights credential expires every year. This guide renews it.',
    },
    'check-doctype-fit': {
        'title': 'Fits its DocType',
        'dim': 'structured',
        'what': 'The body has the shape of its DocType.',
        'how': 'How-to guide: three or more numbered steps, or a command in a code block. Tutorial: both. '
               'Reference: a table, or a list of five or more items. Explanation: three or more sections. '
               'Without a DocType, set one first.',
        'example': '1. Open transaction SU01.\n2. Enter the user name.\n3. Click Change.\n\n```bash\nsapcontrol -nr 00 -function GetProcessList\n```\n\n'
                   '| Parameter | Value |\n|---|---|\n| login/min_password_lng | 8 |',
    },
    'check-skeleton-section': {
        'title': 'Skeleton sections',
        'dim': 'structured',
        'what': 'The document has the sections of its skeleton, the template for its Category or WorkType.',
        'how': 'Add each missing section as a `##` heading, with its content. Similar names count: Overview also matches '
               'Description, Introduction or Information; Impact matches Scope, Risk or Justification; Rollback matches '
               'Fallback or Backout; Verification matches Validation or Check; Resolution matches Solution or Fix. '
               'A References section in a skeleton is scored once, under Connected. '
               'The skeletons are listed at the end of this page.',
        'example': '## Timeline\n\n- 09:10 Alert received.\n- 09:25 Service restarted.',
    },
    'check-third-section': {
        'title': 'Three or more sections',
        'dim': 'structured',
        'what': 'Documents without a skeleton for their Category get full points with three or more sections.',
        'how': 'Split the content into at least three `##` sections, or set a Category that has a skeleton.',
        'example': '## Description\n\n## Steps\n\n## References',
    },
    'check-empty-section': {
        'title': 'No empty sections',
        'dim': 'structured',
        'what': 'Every heading has content under it.',
        'how': 'Write something under the empty heading, or remove the heading. Each empty section costs 3 points, at most 6.',
        'example': '## Rollback\n\nRestore the previous kernel from /usr/sap/SID/SYS/exe/old.',
    },
    'check-skeleton-text': {
        'title': 'No skeleton text left',
        'dim': 'structured',
        'what': 'The example text of the skeleton, such as "Step one" or "List prerequisites here.", has been replaced.',
        'how': 'Replace every line of example text from the skeleton with your own content.',
        'example': '',
    },
    'check-words': {
        'title': 'Long enough for its type',
        'dim': 'complete',
        'what': 'The body reaches the word target of its type: how-to guide 150, reference 200, explanation 500, '
                'tutorial 800, records 60. Code blocks do not count.',
        'how': 'Explain the why, the prerequisites and the result, not only the commands. A document under 50 words '
               '(records: 20) gets at most 3 points. Words beyond the target add nothing.',
        'example': '',
    },
    'check-backlinks': {
        'title': 'Other documents link to it',
        'dim': 'connected',
        'what': 'At least one other document links to this one, so readers can reach it by following links.',
        'how': 'In a related document, add a link to this file. The page then lists it under "Linked from".',
        'example': 'See also [Renew the ReaderRights credential](SAP-BC-ADS-READERRIGHTS.md).',
    },
    'check-internal-link': {
        'title': 'Links to a related document',
        'dim': 'connected',
        'what': 'The document links to another document of the knowledge base.',
        'how': 'Link to the file name with the `.md` extension. KB4IT turns it into a link to the page. '
               'A link to a section adds `#` and the section id.',
        'example': 'Before you start, [stop the batch jobs](SAP-BC-TSK-SUSPEND-JOBS.md#steps).',
    },
    'check-source': {
        'title': 'Cites a source',
        'dim': 'connected',
        'what': 'The document cites an external source: an SAP note, vendor documentation, a ticket.',
        'how': 'Add a web link. SAP notes named in the text ("note 736902") are also shown in the Details tab.',
        'example': 'See [SAP Note 736902](https://me.sap.com/notes/736902) and the '
                   '[ADS documentation](https://help.sap.com/docs/).',
    },
    'check-references': {
        'title': 'References section',
        'dim': 'connected',
        'what': 'A section named References, Documentation or Related collects the links.',
        'how': 'Add a `## References` section at the end, with one link per line.',
        'example': '## References\n\n- [SAP Note 736902](https://me.sap.com/notes/736902)\n- [Restore the database](RESTORE-DB.md)',
    },
    'check-image': {
        'title': 'Image or diagram',
        'dim': 'connected',
        'what': 'The document has an image or a diagram.',
        'how': 'Copy the image to `source/resources/images/` and link it with a descriptive alt text, which becomes '
               'the caption. A Mermaid code block also counts.',
        'example': '![User list in transaction SU01](resources/images/su01-users.png)\n\n```mermaid\nflowchart LR\n  A[Alert] --> B[Restart]\n```',
    },
    'check-broken-link': {
        'title': 'Working links',
        'dim': 'connected',
        'what': 'Every link to another document points to a document that exists.',
        'how': 'Check the file name and its `.md` extension, or create the missing document. Each broken link costs 3 '
               'points. `kb4it verify` lists them all.',
        'example': '[Restore the database](RESTORE-DB.md)',
    },
    'check-missing-image': {
        'title': 'Images present',
        'dim': 'connected',
        'what': 'Every image the document shows exists in the source folder.',
        'how': 'Copy the file to the path in the link, under `source/`, or correct the path. Each missing image costs '
               '3 points; the page shows a grey box instead.',
        'example': '![Transport log](resources/images/stms-log.png)',
    },
    'check-final-status': {
        'title': 'Final status',
        'dim': 'current',
        'what': 'The Status is final: Released, Completed, Finished or Successful.',
        'how': 'When the document is ready, set a final status. A draft or an open item gets fewer points '
               '(records: 10 of 20).',
        'example': 'Status: Released',
    },
    'check-freshness': {
        'title': 'Recently reviewed',
        'dim': 'current',
        'what': 'The Date is recent. The points halve every 3 years for how-to guides and tutorials, 4 for references '
                'and 8 for explanations. Records do not lose points with age.',
        'how': 'Review the content: check commands, versions and screenshots. Then set the Date to the day of the review.',
        'example': 'Date: 2026-10-24',
    },
    'check-dated': {
        'title': 'Dated',
        'dim': 'current',
        'what': 'The document has a Date in a format KB4IT reads.',
        'how': 'Add a `Date` key as `YYYY-MM-DD`, `YYYY-MM-DD HH:MM` or `YYYY-MM-DD HH:MM:SS`.',
        'example': 'Date: 2026-10-24',
    },
}
