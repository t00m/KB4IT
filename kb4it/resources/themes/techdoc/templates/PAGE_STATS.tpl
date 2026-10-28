<%!
def num(count, one, many):
    return '%d %s' % (count, one if count == 1 else many)

def found(*counts):
    """'a, b and c.' from the (count, one, many) triples whose count is not zero."""
    parts = [num(*triple) for triple in counts if triple[0]]
    return (', '.join(parts[:-1]) + ' and ' + parts[-1] if len(parts) > 1 else parts[0]) + '.'
%>
<% s = var['stats'] %>
<%def name="label(item, text)">\
% if item.url:
<a href="${item.url}">${text}</a>\
% else:
${text}\
% endif
</%def>
<%def name="bars(items)">\
<div class="kb-stats-list">
% for bar in items:
    <div class="kb-stats-row">
        <span class="kb-stats-key">${label(bar, bar.label)}</span>
        <div class="kb-stats-bar-wrap"><div class="kb-stats-bar" style="width: ${bar.pct}%"></div></div>
        <span class="kb-stats-count">${bar.count}</span>
    </div>
% endfor
</div>
</%def>
<%def name="doclist(capped)">\
<ul class="kb-stats-docs">
% for doc in capped.items:
    <li><a href="${doc.url}">${doc.title}</a></li>
% endfor
% if capped.more:
    <li class="kb-stats-more">+${capped.more} more</li>
% endif
</ul>
</%def>
<%def name="card(key, title, summary, details)">\
<div>
    <section class="kb-stats-card">
        <h2 id="stats-${key}">${title}</h2>
        <p class="kb-stats-summary">${summary}</p>
% if details:
        <button class="uk-button uk-button-default uk-button-small" type="button" data-uk-toggle="target: #stats-${key}-details">Details</button>
% endif
    </section>
% if details:
    <!-- ${key.upper()} DETAILS :: START -->
    <div id="stats-${key}-details" class="uk-modal-container" data-uk-modal>
        <div class="uk-modal-dialog uk-modal-body">
            <button class="uk-modal-close-default" type="button" data-uk-close aria-label="Close"></button>
            <h3 id="stats-${key}-title">${title}</h3>
            ${caller.body()}
        </div>
    </div>
    <!-- ${key.upper()} DETAILS :: END -->
% endif
</div>
</%def>
<!-- TOTALS :: START -->
<div class="kb-stats-hero">
    <a class="kb-stat-card" href="all.html">
        <span class="kb-stat-icon" data-uk-icon="icon: file-text; ratio: 1.4"></span>
        <span class="kb-stat-num">${s.documents}</span>
        <span class="kb-stat-label">Documents</span>
    </a>
    <a class="kb-stat-card" href="properties.html">
        <span class="kb-stat-icon" data-uk-icon="icon: tag; ratio: 1.4"></span>
        <span class="kb-stat-num">${s.properties}</span>
        <span class="kb-stat-label">Properties</span>
    </a>
    <a class="kb-stat-card" href="properties.html">
        <span class="kb-stat-icon" data-uk-icon="icon: list; ratio: 1.4"></span>
        <span class="kb-stat-num">${s.values}</span>
        <span class="kb-stat-label">Values</span>
    </a>
    <div class="kb-stat-card">
        <span class="kb-stat-icon" data-uk-icon="icon: calendar; ratio: 1.4"></span>
        <span class="kb-stat-num">${s.dated_pct}%</span>
        <span class="kb-stat-label">Dated</span>
    </div>
    <a class="kb-stat-card" href="bookmarks.html">
        <span class="kb-stat-icon" data-uk-icon="icon: bookmark; ratio: 1.4"></span>
        <span class="kb-stat-num">${s.bookmarks}</span>
        <span class="kb-stat-label">Bookmarks</span>
    </a>
    <div class="kb-stat-card">
        <span class="kb-stat-icon" data-uk-icon="icon: link; ratio: 1.4"></span>
        <span class="kb-stat-num">${s.links}</span>
        <span class="kb-stat-label">Links</span>
    </div>
</div>
<!-- TOTALS :: END -->
<!-- SECTIONS :: START -->
<div class="uk-child-width-1-2@m uk-grid-small uk-grid-match kb-stats-cards" data-uk-grid>
<!-- ACTIVITY :: START -->
<%
    year = s.busiest_year
    if year:
        summary = '%s from %s to %s; the busiest year is %s, with %d.' % (num(s.dated, 'dated document', 'dated documents'), s.oldest, s.newest, year.label, year.count)
        if s.undated:
            summary += ' %s.' % num(s.undated, 'document has no date', 'documents have no date')
    else:
        summary = 'No document has a date.'
%>
<%self:card key="activity" title="Activity" summary="${summary}" details="${bool(s.years)}">
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h4 id="stats-years">Documents per year</h4>
            ${bars(s.years)}
        </div>
        <div>
            <h4 id="stats-months">Last ${len(s.months)} months</h4>
            ${bars(s.months)}
        </div>
    </div>
</%self:card>
<!-- ACTIVITY :: END -->
<!-- PROPERTY COVERAGE :: START -->
<%
    low = s.least_covered
    if low:
        summary = '%s; %d set in every document. Least used: %s, in %d%% of the documents.' % (num(len(s.coverage), 'property', 'properties'), s.full_coverage, low.key, low.pct)
    else:
        summary = 'No document has properties.'
%>
<%self:card key="coverage" title="Property coverage" summary="${summary}" details="${bool(s.coverage)}">
    <div class="uk-overflow-auto">
    <table class="uk-table uk-table-small uk-table-divider uk-table-middle kb-stats-table">
        <thead>
            <tr><th>Property</th><th>Documents</th><th class="uk-text-right">Values</th><th>Top values</th></tr>
        </thead>
        <tbody>
% for row in s.coverage:
            <tr>
                <td><a class="kb-stats-key" href="${row.url}">${row.key}</a></td>
                <td class="kb-stats-cover">
                    <div class="kb-stats-bar-wrap"><div class="kb-stats-bar" style="width: ${row.pct}%"></div></div>
                    <span class="kb-stats-count">${row.docs} (${row.pct}%)</span>
                </td>
                <td class="uk-text-right">${row.values}</td>
                <td>
% for value in row.top:
                    <a class="kb-stats-value" href="${value.url}">${value.value} <span>${value.count}</span></a>
% endfor
                </td>
            </tr>
% endfor
        </tbody>
    </table>
    </div>
</%self:card>
<!-- PROPERTY COVERAGE :: END -->
<!-- METADATA HEALTH :: START -->
<%
    if s.health_issues:
        summary = found((s.duplicates.total, 'group of similar values', 'groups of similar values'),
                        (s.rare_keys.total, 'property used once', 'properties used once'),
                        (s.sparse_docs.total, 'document with little metadata', 'documents with little metadata'))
    else:
        summary = 'No problems found.'
%>
<%self:card key="health" title="Metadata health" summary="${summary}" details="${bool(s.health_issues)}">
    <div class="uk-child-width-1-3@m" data-uk-grid>
% if s.duplicates.items:
        <!-- SIMILAR VALUES :: START -->
        <div>
            <h4 id="stats-similar">Similar values</h4>
            <ul class="kb-stats-docs">
% for group in s.duplicates.items:
                <li>${group.key}:
% for value in group.values:
                    <a class="kb-stats-value" href="${value.url}">${value.value} <span>${value.count}</span></a>
% endfor
                </li>
% endfor
% if s.duplicates.more:
                <li class="kb-stats-more">+${s.duplicates.more} more</li>
% endif
            </ul>
        </div>
        <!-- SIMILAR VALUES :: END -->
% endif
% if s.rare_keys.items:
        <!-- RARE PROPERTIES :: START -->
        <div>
            <h4 id="stats-rare">Properties used once</h4>
            <ul class="kb-stats-docs">
% for rare in s.rare_keys.items:
                <li><a href="${rare.url}">${rare.key}</a> in <a href="${rare.doc.url}">${rare.doc.title}</a></li>
% endfor
% if s.rare_keys.more:
                <li class="kb-stats-more">+${s.rare_keys.more} more</li>
% endif
            </ul>
        </div>
        <!-- RARE PROPERTIES :: END -->
% endif
% if s.sparse_docs.items:
        <!-- SPARSE DOCUMENTS :: START -->
        <div>
            <h4 id="stats-sparse">Documents with little metadata</h4>
            ${doclist(s.sparse_docs)}
        </div>
        <!-- SPARSE DOCUMENTS :: END -->
% endif
    </div>
</%self:card>
<!-- METADATA HEALTH :: END -->
<!-- LINKS :: START -->
<%
    if s.links:
        top = s.most_linked[0]
        summary = '%s between documents; the most linked is %s, with %d. %s.' % (num(s.links, 'link', 'links'), top.title, top.count, num(s.orphans.total, 'document is not linked from any other', 'documents are not linked from any other'))
    else:
        summary = 'No document links to another.'
%>
<%self:card key="links" title="Links" summary="${summary}" details="${bool(s.links)}">
    <p class="kb-stats-note">${s.no_outgoing} of ${s.documents} documents link to no other document.</p>
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h4 id="stats-most-linked">Most linked</h4>
            <ul class="kb-stats-docs">
% for doc in s.most_linked:
                <li><a href="${doc.url}">${doc.title}</a> <span class="kb-stats-count">${doc.count}</span></li>
% endfor
            </ul>
        </div>
% if s.orphans.items:
        <!-- ORPHANS :: START -->
        <div>
            <h4 id="stats-orphans">Not linked from any document</h4>
            ${doclist(s.orphans)}
        </div>
        <!-- ORPHANS :: END -->
% endif
    </div>
</%self:card>
<!-- LINKS :: END -->
</div>
<!-- SECTIONS :: END -->
