<%!
def num(count, one, many):
    return '%d %s' % (count, one if count == 1 else many)

def found(*counts):
    """'a, b and c.' from the (count, one, many) triples whose count is not zero."""
    parts = [num(*triple) for triple in counts if triple[0]]
    return (', '.join(parts[:-1]) + ' and ' + parts[-1] if len(parts) > 1 else parts[0]) + '.'
%>
<% s = var['stats'] %>
<%def name="bars(items)">\
<div class="bk-stats-bars">
% for bar in items:
    <div class="bk-stats-bar-row">
        <span class="bk-stats-bar-label">${bar.label}</span>
        <span class="bk-stats-bar-track"><span class="bk-stats-bar" style="width: ${bar.pct}%"></span></span>
        <span class="bk-stats-bar-count">${bar.count}</span>
    </div>
% endfor
</div>
</%def>
<%def name="doclist(capped)">\
<ul class="bk-stats-list">
% for doc in capped.items:
    <li><a href="${doc.url}">${doc.title}</a></li>
% endfor
% if capped.more:
    <li class="bk-stats-more">+${capped.more} more</li>
% endif
</ul>
</%def>
<%def name="card(key, title, summary, details)">\
<section class="bk-stats-card">
    <h2 id="stats-${key}">${title}</h2>
    <p class="bk-stats-summary">${summary}</p>
% if details:
    <button class="bk-stats-details" type="button" data-bk-dialog="stats-${key}-details">Details</button>
    <!-- ${key.upper()} DETAILS :: START -->
    <dialog id="stats-${key}-details" class="bk-stats-dialog" aria-labelledby="stats-${key}-title">
        <div class="bk-stats-dialog-body">
            <button class="bk-stats-dialog-close" type="button" data-bk-close aria-label="Close">&times;</button>
            <h3 id="stats-${key}-title">${title}</h3>
            ${caller.body()}
        </div>
    </dialog>
    <!-- ${key.upper()} DETAILS :: END -->
% endif
</section>
</%def>
<h1>Statistics</h1>
<!-- TOTALS :: START -->
<div class="bk-stats-summary-row">
    <a class="bk-stat-card" href="all.html">
        <span class="bk-stat-value">${s.documents}</span>
        <span class="bk-stat-label">Documents</span>
    </a>
    <a class="bk-stat-card" href="properties.html">
        <span class="bk-stat-value">${s.properties}</span>
        <span class="bk-stat-label">Metadata Keys</span>
    </a>
    <a class="bk-stat-card" href="properties.html">
        <span class="bk-stat-value">${s.values}</span>
        <span class="bk-stat-label">Values</span>
    </a>
    <div class="bk-stat-card">
        <span class="bk-stat-value">${s.dated_pct}%</span>
        <span class="bk-stat-label">Dated</span>
    </div>
    <a class="bk-stat-card" href="bookmarks.html">
        <span class="bk-stat-value">${s.bookmarks}</span>
        <span class="bk-stat-label">Bookmarks</span>
    </a>
    <div class="bk-stat-card">
        <span class="bk-stat-value">${s.links}</span>
        <span class="bk-stat-label">Links</span>
    </div>
</div>
<!-- TOTALS :: END -->
<!-- SECTIONS :: START -->
<div class="bk-stats-cards">
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
    <div class="bk-stats-columns">
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
        summary = '%s; %d set in every document. Least used: %s, in %d%% of the documents.' % (num(len(s.coverage), 'key', 'keys'), s.full_coverage, low.key, low.pct)
    else:
        summary = 'No document has metadata keys.'
%>
<%self:card key="coverage" title="Property coverage" summary="${summary}" details="${bool(s.coverage)}">
    <table class="bk-table">
        <thead>
            <tr><th>Key</th><th>Documents</th><th class="bk-col-count">Values</th><th>Top values</th></tr>
        </thead>
        <tbody>
% for row in s.coverage:
            <tr>
                <td><a href="${row.url}">${row.key}</a></td>
                <td class="bk-stats-cover">
                    <span class="bk-stats-bar-track"><span class="bk-stats-bar" style="width: ${row.pct}%"></span></span>
                    <span class="bk-stats-bar-count">${row.docs} (${row.pct}%)</span>
                </td>
                <td class="bk-col-count">${row.values}</td>
                <td>
% for value in row.top:
                    <a class="bk-stats-value" href="${value.url}">${value.value} <span>${value.count}</span></a>
% endfor
                </td>
            </tr>
% endfor
        </tbody>
    </table>
</%self:card>
<!-- PROPERTY COVERAGE :: END -->
<!-- METADATA HEALTH :: START -->
<%
    if s.health_issues:
        summary = found((s.duplicates.total, 'group of similar values', 'groups of similar values'),
                        (s.rare_keys.total, 'key used once', 'keys used once'),
                        (s.sparse_docs.total, 'document with little metadata', 'documents with little metadata'))
    else:
        summary = 'No problems found.'
%>
<%self:card key="health" title="Metadata health" summary="${summary}" details="${bool(s.health_issues)}">
    <div class="bk-stats-columns">
% if s.duplicates.items:
        <!-- SIMILAR VALUES :: START -->
        <div>
            <h4 id="stats-similar">Similar values</h4>
            <ul class="bk-stats-list">
% for group in s.duplicates.items:
                <li>${group.key}:
% for value in group.values:
                    <a class="bk-stats-value" href="${value.url}">${value.value} <span>${value.count}</span></a>
% endfor
                </li>
% endfor
% if s.duplicates.more:
                <li class="bk-stats-more">+${s.duplicates.more} more</li>
% endif
            </ul>
        </div>
        <!-- SIMILAR VALUES :: END -->
% endif
% if s.rare_keys.items:
        <!-- RARE PROPERTIES :: START -->
        <div>
            <h4 id="stats-rare">Keys used once</h4>
            <ul class="bk-stats-list">
% for rare in s.rare_keys.items:
                <li><a href="${rare.url}">${rare.key}</a> in <a href="${rare.doc.url}">${rare.doc.title}</a></li>
% endfor
% if s.rare_keys.more:
                <li class="bk-stats-more">+${s.rare_keys.more} more</li>
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
    <p class="bk-stats-note">${s.no_outgoing} of ${s.documents} documents link to no other document.</p>
    <div class="bk-stats-columns">
        <div>
            <h4 id="stats-most-linked">Most linked</h4>
            <ul class="bk-stats-list">
% for doc in s.most_linked:
                <li><a href="${doc.url}">${doc.title}</a> <span class="bk-stats-bar-count">${doc.count}</span></li>
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
