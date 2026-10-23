% if len(var['rows']) > 0:
<!-- DOCUMENT LIST :: START -->
<table id="${var['table_id']}" class="kb4it-datatable uk-table uk-table-small uk-table-responsive uk-table-divider uk-table-hover uk-table-striped uk-text-small" style="width: 100%">
    <thead>
        <tr>
            ${var['header'] | n}
        </tr>
    </thead>
    <tbody>
            ${var['rows'] | n}
    </tbody>
</table>
<!-- DOCUMENT LIST :: END -->
% else:
<!-- DOCUMENT LIST :: START -->
<div class="uk-flex uk-flex-top uk-flex-center uk-height-viewport uk-background-muted uk-padding-large">
        <span class="uk-text-lead uk-text-danger">No matching records found.</span>
</div>
<!-- DOCUMENT LIST :: END -->
% endif
