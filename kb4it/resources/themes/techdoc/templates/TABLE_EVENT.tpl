<table class="uk-table uk-table-responsive uk-table-striped uk-table-divider uk-table-hover">
    <caption></caption>
    <thead>
        <tr>
            <th class="uk-text-bold">Date</th>
            <th class="uk-text-bold">Team</th>
            <th class="uk-text-bold">Title</th>
            <th class="uk-text-bold">Category</th>
            <th class="uk-text-bold">Scope</th>
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
            <td>${row['timestamp']}</td>
            <td>${row['team']}</td>
            <td>${row['title']}</td>
            <td>${row['category']}</td>
            <td>${row['scope']}</td>
        </tr>
% endfor
    </tbody>
</table>
