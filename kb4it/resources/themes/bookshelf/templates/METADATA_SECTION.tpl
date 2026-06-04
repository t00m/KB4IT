<dl class="bk-metadata-list">
% for item in var['items']:
<dt class="bk-metadata-key"><a href="${item['vfkey']}.html">${item['key']}</a></dt>
<dd class="bk-metadata-value">${item['labels']}</dd>
% endfor
</dl>
