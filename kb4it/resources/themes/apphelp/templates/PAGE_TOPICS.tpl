<%
    L = var['ah']['labels']
%>
<p class="ah-muted">${L['topics_intro']}</p>
<nav class="ah-topic-index" aria-label="${L['topics']}">
% for group in var['groups']:
  <a class="ah-chip" href="#${group['anchor']}">${group['name']} (${len(group['pages'])})</a>
% endfor
</nav>
% for group in var['groups']:
<section class="ah-topic">
  <h2 id="${group['anchor']}">${group['name']}</h2>
  <ul class="ah-list">
%   for item in group['pages']:
    <li><span class="ah-badge ah-badge-${item['doctype']}">${item['doctype_label']}</span> <a href="${item['url']}">${item['title']}</a><br><span class="ah-muted">${item['summary']}</span></li>
%   endfor
  </ul>
</section>
% endfor
