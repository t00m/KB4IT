= ${var['title']}

++++
<!-- KEY_PAGE.tpl -->
<!-- Tabs header :: START-->
<!--
<div class="uk-flex uk-flex-center"><h1 class="uk-text-large">${var['title']}</h1></div>
-->
<ul class="uk uk-flex-center" uk-tab>
    <li><a href="#">Cloud</a></li>
    <li><a href="#">Table</a></li>
    <li><a href="#">Leader</a></li>
</ul>
<!-- Tabs header :: END -->

<!-- Tabs content :: START-->
<ul class="uk-switcher uk-margin">
    <!-- Cloud :: Start -->
    <li>
        ${var['cloud']}
    </li>
    <!-- Cloud :: End -->
    <!-- Table :: Start -->
    <li>
        <table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped" style="width:100%">
            <thead>
                <tr class="">
                    <th><span class="uk-text-bold uk-text-primary">Value</span></th>
                </tr>
            </thead>
            <tbody>
                % for item in var['leader']:
                    <tr class="">
                        <td><a class="uk-link-heading" href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a></td>
                    </tr>
                % endfor
            </tbody>
            <tfoot>
            </tfoot>
        </table>
    </li>
    <!-- Table :: End -->
    <!-- Leader :: Start -->
    <li>
    % for item in var['leader']:
        <!-- Leader row :: Start -->
        <div class="uk-grid-small" uk-grid>
            <div class="uk-width-expand uk-text-bold" uk-leader>
                <a class="uk-link-heading" href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a>
            </div>
            <div>${item['count']}</div>
        </div>
        <!-- Leader row :: End -->
    % endfor
    </li>
    <!-- Leader :: End-->
</ul>
<!-- Tabs content :: END-->
++++
