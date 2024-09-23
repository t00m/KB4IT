= Stats

++++
    <!-- INDEX_TAB_STATS.tpl :: START -->
    <div class="uk-grid-small" uk-grid>
        <div class="uk-width-expand uk-text-bold" uk-leader>
            <a class="uk-link-heading" href="all.html">Documents</a>
        </div>
        <div>
            <a href="all.html">${var['count_docs']}</a>
        </div> <!-- Num of documents -->
    </div>
    <div class="uk-grid-small" uk-grid>
        <div class="uk-width-expand uk-text-bold" uk-leader>
            <a class="uk-link-heading" href="properties.html">Properties</a>
        </div>
        <div><a href="properties.html">${var['count_keys']}</a></div> <!-- Num of properties or keys -->
    </div>
    <!-- Property leader items -->
% for item in var['leader_items']:
    <div class="uk-grid-small" uk-grid>
        <div class="uk-width-1-6@m"></div>
        <div class="uk-width-expand uk-text-bold" uk-leader><a class="uk-link-heading" href="${item['vfkey']}.html">${item['key']}</a></div>
        <div><a href="${item['vfkey']}.html">${item['count_values']}</a></div>
    </div>
% endfor
    <!-- Property leader items -->
++++
