% if len(var['rows']) > 0:
<table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped uk-text-small uk-height-1-1" style="width: 100%">
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
<div class="uk-flex uk-flex-top uk-flex-center uk-height-viewport uk-background-muted uk-padding-large">
        <span class="uk-text-lead uk-text-danger">No matching records found.</span>
</div>
% endif
