${var['cloud'] | n}
<ul class="uk-list uk-list-divider">
% for item in var['leader']:
    <li><a href="${item['vfkey']}_${item['vfvalue']}.html">${item['name']}</a> <span class="uk-badge">${item['count']}</span></li>
% endfor
</ul>
