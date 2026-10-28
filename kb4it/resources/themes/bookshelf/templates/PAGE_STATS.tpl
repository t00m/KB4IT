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
<h1>Statistics</h1>
<!-- TOTALS :: START -->
<div class="bk-stats-summary">
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
% if s.years:
<!-- ACTIVITY :: START -->
<section class="bk-stats-section">
    <h2 id="stats-activity">Activity</h2>
    <p class="bk-stats-note">From ${s.oldest} to ${s.newest}\
% if s.undated:
, ${s.undated} undated
% endif
</p>
    <div class="bk-stats-columns">
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
<section class="bk-stats-section">
    <h2 id="stats-coverage">Property coverage</h2>
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
</section>
<!-- PROPERTY COVERAGE :: END -->
% endif
% if s.duplicates.items or s.rare_keys.items or s.sparse_docs.items:
<!-- METADATA HEALTH :: START -->
<section class="bk-stats-section">
    <h2 id="stats-health">Metadata health</h2>
    <div class="bk-stats-columns">
% if s.duplicates.items:
        <!-- SIMILAR VALUES :: START -->
        <div>
            <h3 id="stats-similar">Similar values</h3>
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
            <h3 id="stats-rare">Keys used once</h3>
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
<section class="bk-stats-section">
    <h2 id="stats-links">Links</h2>
    <p class="bk-stats-note">${s.no_outgoing} of ${s.documents} documents link to no other document.</p>
    <div class="bk-stats-columns">
        <div>
            <h3 id="stats-most-linked">Most linked</h3>
            <ul class="bk-stats-list">
% for doc in s.most_linked:
                <li><a href="${doc.url}">${doc.title}</a> <span class="bk-stats-bar-count">${doc.count}</span></li>
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
