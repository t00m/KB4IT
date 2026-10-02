<div class="bk-key-header">
    <h1 class="bk-key-title">Property: ${var['title']}</h1>
    <div class="bk-key-meta">
        <span>${len(var['leader'])} value${'s' if len(var['leader']) != 1 else ''}</span>
        <span class="bk-meta-sep">-</span>
        <span>${sum(item['count'] for item in var['leader'])} document${'s' if sum(item['count'] for item in var['leader']) != 1 else ''}</span>
    </div>
</div>

<div class="bk-key-tabs">
    <button class="bk-tab-btn bk-tab-active" data-tab="cloud">Cloud</button>
    <button class="bk-tab-btn" data-tab="table">Table</button>
    <button class="bk-tab-btn" data-tab="leader">Leader</button>
</div>

<div class="bk-tab-content bk-tab-content-active" id="tab-cloud">
    ${var['cloud']}
</div>
<div class="bk-tab-content" id="tab-table">
    <table class="bk-table bk-table-key">
        <thead>
            <tr>
                <th>Value</th>
                <th class="bk-col-count">Documents</th>
            </tr>
        </thead>
        <tbody>
% for item in var['leader']:
            <tr>
                <td><a href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a></td>
                <td class="bk-col-count">${item['count']}</td>
            </tr>
% endfor
        </tbody>
    </table>
</div>
<div class="bk-tab-content" id="tab-leader">
% for item in var['leader']:
    <div class="bk-leader-row">
        <a href="${item['vfkey']}_${item['vfvalue']}.html" class="bk-leader-name">${item['name']}</a>
        <span class="bk-leader-count">${item['count']}</span>
    </div>
% endfor
</div>
