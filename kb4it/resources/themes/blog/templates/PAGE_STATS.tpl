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
% if s.years:
<!-- ACTIVITY :: START -->
<section class="uk-margin-medium-top">
    <h2 id="stats-activity">Activity</h2>
    <p class="uk-text-meta">From ${s.oldest} to ${s.newest}\
% if s.undated:
, ${s.undated} undated
% endif
</p>
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h3 id="stats-years">Posts per year</h3>
            ${bars(s.years)}
        </div>
        <div>
            <h3 id="stats-months">Last ${len(s.months)} months</h3>
            ${bars(s.months)}
        </div>
    </div>
</section>
<!-- ACTIVITY :: END -->
% endif
% if s.coverage:
<!-- PROPERTY COVERAGE :: START -->
<section class="uk-margin-medium-top">
    <h2 id="stats-coverage">Property coverage</h2>
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
</section>
<!-- PROPERTY COVERAGE :: END -->
% endif
% if s.duplicates.items or s.rare_keys.items or s.sparse_docs.items:
<!-- METADATA HEALTH :: START -->
<section class="uk-margin-medium-top">
    <h2 id="stats-health">Metadata health</h2>
    <div class="uk-child-width-1-3@m" data-uk-grid>
% if s.duplicates.items:
        <!-- SIMILAR VALUES :: START -->
        <div>
            <h3 id="stats-similar">Similar values</h3>
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
            <h3 id="stats-rare">Properties used once</h3>
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
            <h3 id="stats-sparse">Posts with little metadata</h3>
            ${doclist(s.sparse_docs)}
        </div>
        <!-- SPARSE DOCUMENTS :: END -->
% endif
    </div>
</section>
<!-- METADATA HEALTH :: END -->
% endif
% if s.links:
<!-- LINKS :: START -->
<section class="uk-margin-medium-top">
    <h2 id="stats-links">Links</h2>
    <p class="uk-text-meta">${s.no_outgoing} of ${s.documents} posts link to no other post.</p>
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h3 id="stats-most-linked">Most linked</h3>
            <ul class="uk-list uk-list-divider">
% for doc in s.most_linked:
                <li><a href="${doc.url}">${doc.title}</a> <span class="uk-badge">${doc.count}</span></li>
% endfor
            </ul>
        </div>
% if s.orphans.items:
        <!-- ORPHANS :: START -->
        <div>
            <h3 id="stats-orphans">Not linked from any post</h3>
            ${doclist(s.orphans)}
        </div>
        <!-- ORPHANS :: END -->
% endif
    </div>
</section>
<!-- LINKS :: END -->
% endif
