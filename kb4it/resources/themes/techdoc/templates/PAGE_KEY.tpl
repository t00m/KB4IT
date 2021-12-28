= ${var['title']}

++++
    <!-- KEY_PAGE.tpl -->
    <!-- Tabs header :: START-->
    <ul class="uk-flex-center" uk-tab>
        <li><a href="#">Cloud</a></li>
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
