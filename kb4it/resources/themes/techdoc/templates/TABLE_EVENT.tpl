<table class="uk-table uk-table-responsive uk-table-striped uk-table-divider uk-table-hover">
    <caption></caption>
    <thead>
        <tr>
            <th class="uk-text-bold uk-text-primary">Date</th>
            <th class="uk-text-bold uk-text-primary">Team</th>
            <th class="uk-text-bold uk-text-primary">Title</th>
            <th class="uk-text-bold uk-text-primary">Category</th>
            <th class="uk-text-bold uk-text-primary">Scope</th>
            <th class="uk-text-bold uk-text-primary">Status</th>
        </tr>
    </thead>
    <tfoot>
        <tr>
            <td></td>
        </tr>
    </tfoot>
    <tbody>
% for row in var['rows']:
        <tr>
            <td class="uk-text-meta">${row['timestamp']}</td>
            <td class="uk-text-meta">${row['team']}</td>
            <td class="uk-text-meta">${row['title']}</td>
            <td class="uk-text-meta">${row['category']}</td>
            <td class="uk-text-meta">${row['scope']}</td>
            <td class="uk-text-meta">${row['status']}</td>
        </tr>
% endfor
    </tbody>
</table>
