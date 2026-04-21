= ${var['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

++++
<div class="kb-key-header">
    <span class="kb-key-title">${var['title']}</span>
    <div class="kb-key-meta">
        <span>${len(var['leader'])} value${'s' if len(var['leader']) != 1 else ''}</span>
        <span class="kb-meta-sep">·</span>
        <span>${sum(item['count'] for item in var['leader'])} document${'s' if sum(item['count'] for item in var['leader']) != 1 else ''}</span>
    </div>
</div>

<ul class="uk uk-flex-center" uk-tab>
    <li><a href="#">Cloud</a></li>
    <li><a href="#">Table</a></li>
    <li><a href="#">Leader</a></li>
</ul>

<ul class="uk-switcher uk-margin">
    <li>
        ${var['cloud']}
    </li>
    <li>
        <table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped" style="width:100%">
            <thead>
                <tr>
                    <th><span class="uk-text-bold uk-text-primary">Value</span></th>
                    <th class="uk-width-small"><span class="uk-text-bold uk-text-primary">Documents</span></th>
                </tr>
            </thead>
            <tbody>
% for item in var['leader']:
                <tr>
                    <td><a class="uk-link-heading" href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a></td>
                    <td class="uk-width-small uk-text-right">${item['count']}</td>
                </tr>
% endfor
            </tbody>
        </table>
    </li>
    <li>
% for item in var['leader']:
        <div class="uk-grid-small" uk-grid>
            <div class="uk-width-expand uk-text-bold" uk-leader>
                <a class="uk-link-heading" href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a>
            </div>
            <div>${item['count']}</div>
        </div>
% endfor
    </li>
</ul>
++++
