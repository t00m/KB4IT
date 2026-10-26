<!-- STATISTICS :: START -->
<div class="uk-grid-small" data-uk-grid>
    <div class="uk-width-expand uk-text-bold" data-uk-leader>
        <a class="uk-link-heading" href="all.html">Documents</a>
    </div>
    <div>
        <a href="all.html">${var['count_docs']}</a>
    </div>
</div>
<div class="uk-grid-small" data-uk-grid>
    <div class="uk-width-expand uk-text-bold" data-uk-leader>
        <a class="uk-link-heading" href="properties.html">Properties</a>
    </div>
    <div><a href="properties.html">${var['count_keys']}</a></div>
</div>
<!-- VALUES PER PROPERTY :: START -->
% for item in var['leader_items']:
<div class="uk-grid-small" data-uk-grid>
    <div class="uk-width-1-6@m"></div>
    <div class="uk-width-expand uk-text-bold" data-uk-leader><a class="uk-link-heading" href="${item['vfkey']}.html">${item['key']}</a></div>
    <div><a href="${item['vfkey']}.html">${item['count_values']}</a></div>
</div>
% endfor
<!-- VALUES PER PROPERTY :: END -->
<!-- STATISTICS :: END -->
