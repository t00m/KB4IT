<!-- VIEW TABS :: START -->
<ul class="uk uk-flex-center" data-uk-tab>
    <li><a href="#">Cloud</a></li>
    <li><a href="#">Table</a></li>
    <li><a href="#">Leader</a></li>
</ul>
<!-- VIEW TABS :: END -->

<!-- VIEWS :: START -->
<ul class="uk-switcher uk-margin">
    <!-- CLOUD VIEW :: START -->
    <li>
        ${var['cloud'] | n}
    </li>
    <!-- CLOUD VIEW :: END -->
    <!-- TABLE VIEW :: START -->
    <li>
        <table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped" style="width:100%">
            <thead>
                <tr class="">
                    <th class=""><span class="uk-text-bold uk-text-primary">Value</span></th>
                    <th class="uk-width-small"><span class="uk-text-bold uk-text-primary">Documents</span></th>
                </tr>
            </thead>
            <tbody>
                % for item in var['leader']:
                    <tr class="uk-width-small">
                        <td class=""><a class="uk-link-heading" href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a></td>
                        <td class="uk-width-small uk-text-right"><span class="uk-text-right">${item['count']}</span></td>
                    </tr>
                % endfor
            </tbody>
            <tfoot>
            </tfoot>
        </table>
    </li>
    <!-- TABLE VIEW :: END -->
    <!-- LIST VIEW :: START -->
    <li>
    % for item in var['leader']:
        <div class="uk-grid-small" data-uk-grid>
            <div class="uk-width-expand uk-text-bold" data-uk-leader>
                <a class="uk-link-heading" href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a>
            </div>
            <div>${item['count']}</div>
        </div>
    % endfor
    </li>
    <!-- LIST VIEW :: END -->
</ul>
<!-- VIEWS :: END -->
