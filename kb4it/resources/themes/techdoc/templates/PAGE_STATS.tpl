= Stats

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

++++
<div class="kb-stats-hero">
    <a class="kb-stat-card" href="all.html">
        <span class="kb-stat-icon" uk-icon="icon: file-text; ratio: 1.4"></span>
        <span class="kb-stat-num">${var['count_docs']}</span>
        <span class="kb-stat-label">Documents</span>
    </a>
    <a class="kb-stat-card" href="properties.html">
        <span class="kb-stat-icon" uk-icon="icon: tag; ratio: 1.4"></span>
        <span class="kb-stat-num">${var['count_keys']}</span>
        <span class="kb-stat-label">Properties</span>
    </a>
</div>
<% _max = max((i['count_values'] for i in var['leader_items']), default=1) %>
<div class="kb-stats-list">
% for item in var['leader_items']:
<%  pct = max(4, int(item['count_values'] * 100 / _max)) %>
    <div class="kb-stats-row">
        <a class="kb-stats-key" href="${item['vfkey']}.html">${item['key']}</a>
        <div class="kb-stats-bar-wrap">
            <div class="kb-stats-bar" style="width: ${pct}%"></div>
        </div>
        <a class="kb-stats-count" href="${item['vfkey']}.html">${item['count_values']}</a>
    </div>
% endfor
</div>
++++
