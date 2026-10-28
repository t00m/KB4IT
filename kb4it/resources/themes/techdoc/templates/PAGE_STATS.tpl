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
% if s.years:
<!-- ACTIVITY :: START -->
<section class="kb-stats-section">
    <h2 id="stats-activity">Activity</h2>
    <p class="kb-stats-note">From ${s.oldest} to ${s.newest}\
% if s.undated:
, ${s.undated} undated
% endif
</p>
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h3 id="stats-years">Documents per year</h3>
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
<section class="kb-stats-section">
    <h2 id="stats-coverage">Property coverage</h2>
    <div class="kb-stats-list uk-overflow-auto">
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
</section>
<!-- PROPERTY COVERAGE :: END -->
% endif
% if s.duplicates.items or s.rare_keys.items or s.sparse_docs.items:
<!-- METADATA HEALTH :: START -->
<section class="kb-stats-section">
    <h2 id="stats-health">Metadata health</h2>
    <div class="uk-child-width-1-3@m" data-uk-grid>
% if s.duplicates.items:
        <!-- SIMILAR VALUES :: START -->
        <div>
            <h3 id="stats-similar">Similar values</h3>
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
            <h3 id="stats-rare">Properties used once</h3>
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
            <h3 id="stats-sparse">Documents with little metadata</h3>
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
<section class="kb-stats-section">
    <h2 id="stats-links">Links</h2>
    <p class="kb-stats-note">${s.no_outgoing} of ${s.documents} documents link to no other document.</p>
    <div class="uk-child-width-1-2@m" data-uk-grid>
        <div>
            <h3 id="stats-most-linked">Most linked</h3>
            <ul class="kb-stats-docs">
% for doc in s.most_linked:
                <li><a href="${doc.url}">${doc.title}</a> <span class="kb-stats-count">${doc.count}</span></li>
% endfor
            </ul>
        </div>
% if s.orphans.items:
        <!-- ORPHANS :: START -->
        <div>
            <h3 id="stats-orphans">Not linked from any document</h3>
            ${doclist(s.orphans)}
        </div>
        <!-- ORPHANS :: END -->
% endif
    </div>
</section>
<!-- LINKS :: END -->
% endif
