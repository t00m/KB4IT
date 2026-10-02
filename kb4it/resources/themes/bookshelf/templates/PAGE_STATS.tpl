<h1>Statistics</h1>
<div class="bk-stats-summary">
    <div class="bk-stat-card">
        <span class="bk-stat-value">${var['count_docs']}</span>
        <span class="bk-stat-label">Documents</span>
    </div>
    <div class="bk-stat-card">
        <span class="bk-stat-value">${var['count_keys']}</span>
        <span class="bk-stat-label">Metadata Keys</span>
    </div>
</div>
<h2>Key Leaders</h2>
<table class="bk-table">
    <thead>
        <tr>
            <th>Key</th>
            <th>Values</th>
        </tr>
    </thead>
    <tbody>
% for item in var['leader_items']:
        <tr>
            <td><a href="${item['vfkey']}.html">${item['key']}</a></td>
            <td>${item['count_values']}</td>
        </tr>
% endfor
    </tbody>
</table>
