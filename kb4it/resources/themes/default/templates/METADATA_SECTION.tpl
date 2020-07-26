        <table class="uk-table uk-table-divider uk-table-striped uk-table-hover uk-table-small uk-card uk-card-hover">
% for item in var['items']:
            <tr>
                <td>
                    <a class="uk-link-text" href="${item['vfkey']}.html">
                        <div class="uk-text-bolder uk-text-secondary uk-text-bold uk-text-meta">${item['key']}</div>
                    </a>
                </td>
                <td><div class="uk-flex uk-flex-row uk-flex-wrap uk-text-meta">${item['labels']}</div></td>
            </tr>
% endfor
        </table>