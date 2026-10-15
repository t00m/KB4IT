<%
    ah = var['ah']
    L = ah['labels']
%>
<section class="ah-hero">
% if ah['tagline']:
  <p class="ah-tagline">${ah['tagline']}</p>
% endif
  <form class="ah-hero-search" action="search.html" role="search">
    <input name="q" type="search" placeholder="${L['search_placeholder']}" aria-label="${L['search']}">
    <button type="submit">${L['search']}</button>
  </form>
</section>
% if var['new']:
<section class="ah-new">
  <h2 id="new">${L['new_in']} ${ah['version']}</h2>
  <ul class="ah-list">
% for item in var['new']:
    <li><a href="${item['url']}">${item['title']}</a><br><span class="ah-muted">${item['summary']}</span></li>
% endfor
  </ul>
</section>
% endif
% if var['cards']:
<h2 id="doctypes">${L['doctypes']}</h2>
% endif
<div class="ah-cards">
% for card in var['cards']:
  <section class="ah-card">
    <h3 id="doctype-${card['doctype']}"><span class="ah-badge ah-badge-${card['doctype']}">${card['label']}</span></h3>
%   if card['desc']:
    <p class="ah-muted">${card['desc']}</p>
%   endif
    <ul class="ah-list">
%   for item in card['pages']:
      <li><a href="${item['url']}">${item['title']}</a><br><span class="ah-muted">${item['summary']}</span></li>
%   endfor
    </ul>
%   if card['more'] > 0:
    <p><a href="search.html?DocType=${card['doctype']}">+${card['more']}</a></p>
%   endif
  </section>
% endfor
</div>
