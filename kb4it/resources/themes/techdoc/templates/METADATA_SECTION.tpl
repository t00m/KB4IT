<ul class="kb-metadata-list">
% for item in var['items']:
<li class="kb-metadata-item">
    <strong><a class="kb-meta-key" href="${item['vfkey']}.html">${item['key']}</a></strong>: ${item['labels']}
</li>
% endfor
</ul>
