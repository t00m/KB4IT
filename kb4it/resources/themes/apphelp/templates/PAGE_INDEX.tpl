<%
    ah = var['ah']
    L = ah['labels']
%>
<section class="ah-hero">
% if ah['tagline']:
  <p class="ah-tagline">${ah['tagline'] | h}</p>
% endif
  <form class="ah-hero-search" action="search.html" role="search">
    <input name="q" type="search" placeholder="${L['search_placeholder'] | h}" aria-label="${L['search'] | h}">
    <button type="submit">${L['search'] | h}</button>
  </form>
</section>
% if var['new']:
<section class="ah-new">
  <h2 id="new">${L['new_in'] | h} ${ah['version'] | h}</h2>
  <ul class="ah-list">
% for item in var['new']:
    <li><a href="${item['url'] | h}">${item['title'] | h}</a><br><span class="ah-muted">${item['summary'] | h}</span></li>
% endfor
  </ul>
</section>
% endif
<div class="ah-cards">
% for card in var['cards']:
  <section class="ah-card">
    <h2 id="kind-${card['kind'] | h}"><span class="ah-badge ah-badge-${card['kind'] | h}">${card['label'] | h}</span></h2>
    <ul class="ah-list">
%   for item in card['pages']:
      <li><a href="${item['url'] | h}">${item['title'] | h}</a><br><span class="ah-muted">${item['summary'] | h}</span></li>
%   endfor
    </ul>
%   if card['more'] > 0:
    <p><a href="search.html?Kind=${card['kind'] | h}">+${card['more']}</a></p>
%   endif
  </section>
% endfor
</div>
