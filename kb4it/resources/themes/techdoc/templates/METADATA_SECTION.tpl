<table class="uk-table uk-table-divider uk-table-striped uk-table-hover uk-table-small uk-card uk-card-small uk-card-hover">
<thead class="">
    <tr class="">
        <th class="uk-width-small"><span class="uk-text-bold">Property</span></th>
        <th class=""><span class="uk-text-bold">Values</span></th>
    </tr>
</thead>
<tbody class="">
% for item in var['items']:
    <tr class="">
        <td class="">
            <a class="uk-link-text" href="${item['vfkey']}.html">
                <div class="uk-text-bolder uk-text-secondary uk-text-bold uk-text-meta">${item['key']}</div>
            </a>
        </td>
        <td class=""><div class="uk-flex uk-flex-row uk-flex-wrap uk-text-meta">${item['labels']}</div></td>
    </tr>
% endfor
</tbody>
<tfoot>
</tfoot>
</table>
