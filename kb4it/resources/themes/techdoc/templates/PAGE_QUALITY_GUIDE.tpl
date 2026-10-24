${'##'} How the quality score works {#intro}

Every document gets a score from 0 to 100, shown as a ring under the top bar. Click the ring to open the **Quality** tab: five bars, what the document already has, and the next steps with the points each one adds. Hover over any item for a tip; click it to come to its section on this page.

The score measures structure, metadata, links and age. It does not check that the content is correct.

${'##'} Tiers {#tiers}

| Tier | Score | Look |
|---|---|---|
| Exemplary | ${var['tiers']['exemplary']} and up | gold ring, a gold line under the top bar and a note |
| Complete | ${var['tiers']['complete']} to ${var['tiers']['exemplary'] - 1} | green ring |
| Basic | ${var['tiers']['basic']} to ${var['tiers']['complete'] - 1} | grey ring |
| Stub | under ${var['tiers']['basic']} | grey ring |
| Retired | Status ${', '.join(var['retired'])} | no score |

Records (documents with a `WorkType`: changes, incidents, tasks, meetings) are short by nature. They are judged by the sections of their WorkType skeleton instead of the shape of a DocType, need 60 words instead of 150 to 800, and get points for a final status instead of a recent date. A record is compared with records of the same WorkType.

% for dim in var['dims']:
${'##'} ${dim['title']} (${dim['max']} points) {#dim-${dim['key']}}

${dim['what']}

%     for check in dim['checks']:
${'##'}# ${check['title']} {#${check['key']}}

**What it checks.** ${check['what']}

**How to meet it.** ${check['how']}

%         if check['example']:
~~~~markdown
${check['example'] | n}
~~~~

%         endif
%     endfor
% endfor
${'##'} Skeletons {#skeletons}

A skeleton is the template the Add page starts a document from. The quality score checks that a document has the `##` sections of its skeleton: records use the skeleton of their `WorkType`, other documents the skeleton of their first `Category`.

% for skel in var['skeletons']:
${'##'}# ${skel['title']} {#skeleton-${skel['key']}}

Sections: ${', '.join(skel['headings']) or 'none'}.

~~~~markdown
${skel['text'] | n}
~~~~

% endfor
