<!-- PROPERTIES :: START -->
<div class="kb-props">
<table id="kb-props-table" class="kb4it-datatable uk-table uk-table-small uk-table-divider uk-table-hover uk-table-striped uk-text-small" style="width: 100%" data-kb-order='[[0, "asc"]]'>
    <thead>
        <tr>
            <th><span class="uk-text-secondary">Property</span></th>
            <th class="kb-props-num"><span class="uk-text-secondary">Values</span></th>
            <th class="kb-props-num"><span class="uk-text-secondary">Documents</span></th>
        </tr>
    </thead>
    <tbody>
% for item in var['keys']:
        <tr>
            <td><a class="kb-props-key" href="${item['vfkey']}.html">${item['key']}</a></td>
            <td class="kb-props-num">${item['values']}</td>
            <td class="kb-props-num">${item['docs']}</td>
        </tr>
% endfor
    </tbody>
</table>
</div>
<!-- PROPERTIES :: END -->
