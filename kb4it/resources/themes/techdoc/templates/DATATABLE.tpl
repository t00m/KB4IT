% if len(var['rows']) > 0:
<table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped uk-text-small" style="width: 100%">
    <thead class="">
        <tr class="">
            ${var['header']}
        </tr>
    </thead>
    <tbody class="">
            ${var['rows']}
    </tbody>
    <tfoot class="">
    </tfoot>
</table>
% else:
<h1 class="uk-heading-small">No documents found</h1>
% endif
