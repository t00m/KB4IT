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
<table class="uk-table uk-table-small uk-table-middle uk-margin-remove">
    <tbody>
% for bar in items:
        <tr>
            <td class="uk-table-shrink uk-text-nowrap">${label(bar, bar.label)}</td>
            <td><progress class="uk-progress uk-margin-remove" value="${bar.pct}" max="100">${bar.count}</progress></td>
            <td class="uk-table-shrink uk-text-right">${bar.count}</td>
        </tr>
% endfor
    </tbody>
</table>
</%def>
<%def name="doclist(capped)">\
<ul class="uk-list uk-list-divider">
% for doc in capped.items:
    <li><a href="${doc.url}">${doc.title}</a></li>
% endfor
% if capped.more:
    <li class="uk-text-meta">+${capped.more} more</li>
% endif
</ul>
</%def>
<%def name="card(key, title, summary, details)">\
<div>
    <section class="uk-card uk-card-default uk-card-small uk-card-body">
        <h2 id="stats-${key}">${title}</h2>
        <p>${summary}</p>
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
<div class="uk-child-width-1-3 uk-child-width-1-6@m uk-grid-small uk-text-center" data-uk-grid>
    <div><a class="uk-card uk-card-default uk-card-small uk-card-body uk-display-block uk-link-reset" href="all.html"><span class="uk-text-large uk-text-bold uk-display-block">${s.documents}</span><span class="uk-text-meta">Documents</span></a></div>
    <div><a class="uk-card uk-card-default uk-card-small uk-card-body uk-display-block uk-link-reset" href="properties.html"><span class="uk-text-large uk-text-bold uk-display-block">${s.properties}</span><span class="uk-text-meta">Properties</span></a></div>
    <div><a class="uk-card uk-card-default uk-card-small uk-card-body uk-display-block uk-link-reset" href="properties.html"><span class="uk-text-large uk-text-bold uk-display-block">${s.values}</span><span class="uk-text-meta">Values</span></a></div>
    <div><div class="uk-card uk-card-default uk-card-small uk-card-body"><span class="uk-text-large uk-text-bold uk-display-block">${s.dated_pct}%</span><span class="uk-text-meta">Dated</span></div></div>
    <div><a class="uk-card uk-card-default uk-card-small uk-card-body uk-display-block uk-link-reset" href="bookmarks.html"><span class="uk-text-large uk-text-bold uk-display-block">${s.bookmarks}</span><span class="uk-text-meta">Bookmarks</span></a></div>
    <div><div class="uk-card uk-card-default uk-card-small uk-card-body"><span class="uk-text-large uk-text-bold uk-display-block">${s.links}</span><span class="uk-text-meta">Links</span></div></div>
</div>
<!-- TOTALS :: END -->
<!-- SECTIONS :: START -->
<div class="uk-child-width-1-2@m uk-grid-small uk-grid-match uk-margin-top" data-uk-grid>
<!-- ACTIVITY :: START -->
<%
    year = s.busiest_year
    if year:
        summary = '%s from %s to %s; the busiest year is %s, with %d.' % (num(s.dated, 'dated post', 'dated posts'), s.oldest, s.newest, year.label, year.count)
        if s.undated:
            summary += ' %s.' % num(s.undated, 'post has no date', 'posts have no date')
    else:
        summary = 'No post has a date.'
%>
<%self:card key="activity" title="Activity" summary="${summary}" details="${bool(s.years)}">
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h4 id="stats-years">Posts per year</h4>
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
        summary = '%s; %d set in every post. Least used: %s, in %d%% of the posts.' % (num(len(s.coverage), 'property', 'properties'), s.full_coverage, low.key, low.pct)
    else:
        summary = 'No post has properties.'
%>
<%self:card key="coverage" title="Property coverage" summary="${summary}" details="${bool(s.coverage)}">
    <div class="uk-overflow-auto">
    <table class="uk-table uk-table-small uk-table-divider uk-table-middle">
        <thead>
            <tr><th>Property</th><th>Posts</th><th class="uk-text-right">Values</th><th>Top values</th></tr>
        </thead>
        <tbody>
% for row in s.coverage:
            <tr>
                <td class="uk-text-bold"><a class="uk-link-heading" href="${row.url}">${row.key}</a></td>
                <td class="uk-width-small"><progress class="uk-progress uk-margin-remove" value="${row.pct}" max="100">${row.pct}%</progress><span class="uk-text-meta">${row.docs} (${row.pct}%)</span></td>
                <td class="uk-text-right">${row.values}</td>
                <td>
% for value in row.top:
                    <a class="uk-label uk-label-default" href="${value.url}">${value.value} ${value.count}</a>
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
                        (s.sparse_docs.total, 'post with little metadata', 'posts with little metadata'))
    else:
        summary = 'No problems found.'
%>
<%self:card key="health" title="Metadata health" summary="${summary}" details="${bool(s.health_issues)}">
    <div class="uk-child-width-1-3@m" data-uk-grid>
% if s.duplicates.items:
        <!-- SIMILAR VALUES :: START -->
        <div>
            <h4 id="stats-similar">Similar values</h4>
            <ul class="uk-list uk-list-divider">
% for group in s.duplicates.items:
                <li>${group.key}:
% for value in group.values:
                    <a class="uk-label uk-label-warning" href="${value.url}">${value.value} ${value.count}</a>
% endfor
                </li>
% endfor
% if s.duplicates.more:
                <li class="uk-text-meta">+${s.duplicates.more} more</li>
% endif
            </ul>
        </div>
        <!-- SIMILAR VALUES :: END -->
% endif
% if s.rare_keys.items:
        <!-- RARE PROPERTIES :: START -->
        <div>
            <h4 id="stats-rare">Properties used once</h4>
            <ul class="uk-list uk-list-divider">
% for rare in s.rare_keys.items:
                <li><a href="${rare.url}">${rare.key}</a> in <a href="${rare.doc.url}">${rare.doc.title}</a></li>
% endfor
% if s.rare_keys.more:
                <li class="uk-text-meta">+${s.rare_keys.more} more</li>
% endif
            </ul>
        </div>
        <!-- RARE PROPERTIES :: END -->
% endif
% if s.sparse_docs.items:
        <!-- SPARSE DOCUMENTS :: START -->
        <div>
            <h4 id="stats-sparse">Posts with little metadata</h4>
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
        summary = '%s between posts; the most linked is %s, with %d. %s.' % (num(s.links, 'link', 'links'), top.title, top.count, num(s.orphans.total, 'post is not linked from any other', 'posts are not linked from any other'))
    else:
        summary = 'No post links to another.'
%>
<%self:card key="links" title="Links" summary="${summary}" details="${bool(s.links)}">
    <p class="uk-text-meta">${s.no_outgoing} of ${s.documents} posts link to no other post.</p>
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h4 id="stats-most-linked">Most linked</h4>
            <ul class="uk-list uk-list-divider">
% for doc in s.most_linked:
                <li><a href="${doc.url}">${doc.title}</a> <span class="uk-badge">${doc.count}</span></li>
% endfor
            </ul>
        </div>
% if s.orphans.items:
        <!-- ORPHANS :: START -->
        <div>
            <h4 id="stats-orphans">Not linked from any post</h4>
            ${doclist(s.orphans)}
        </div>
        <!-- ORPHANS :: END -->
% endif
    </div>
</%self:card>
<!-- LINKS :: END -->
</div>
<!-- SECTIONS :: END -->
