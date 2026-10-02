<%
    L = var['ah']['labels']
%>
<p class="ah-muted">${L['topics_intro'] | h}</p>
<nav class="ah-topic-index" aria-label="${L['topics'] | h}">
% for group in var['groups']:
  <a class="ah-chip" href="#${group['anchor']}">${group['name'] | h} (${len(group['pages'])})</a>
% endfor
</nav>
% for group in var['groups']:
<section class="ah-topic">
  <h2 id="${group['anchor']}">${group['name'] | h}</h2>
  <ul class="ah-list">
%   for item in group['pages']:
    <li><span class="ah-badge ah-badge-${item['doctype'] | h}">${item['doctype_label'] | h}</span> <a href="${item['url'] | h}">${item['title'] | h}</a><br><span class="ah-muted">${item['summary'] | h}</span></li>
%   endfor
  </ul>
</section>
% endfor
