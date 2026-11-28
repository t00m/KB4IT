<table class="uk-table uk-table-small uk-table-divider">
    <thead><tr><th>Property</th><th>Values</th><th>Documents</th></tr></thead>
    <tbody>
% for item in var['keys']:
        <tr><td><a href="${item['vfkey']}.html">${item['key']}</a></td><td>${item['values']}</td><td>${item['docs']}</td></tr>
% endfor
    </tbody>
</table>
