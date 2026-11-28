% if len(var['rows']) > 0:
<table class="uk-table uk-table-small uk-table-divider uk-table-hover">
    <thead><tr>${var['header'] | n}</tr></thead>
    <tbody>${var['rows'] | n}</tbody>
</table>
% else:
<p>No documents.</p>
% endif
