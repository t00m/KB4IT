<ul class="documents">
% for item in var['documents']:
    <li><a href="${item['url']}">${item['title']}</a></li>
% endfor
</ul>
