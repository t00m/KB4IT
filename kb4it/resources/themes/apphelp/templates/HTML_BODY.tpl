<%
    ah = var['ah']
    L = ah['labels']
    A = ah['assets']
    chips = ah['page']
%><!doctype html>
<html lang="${ah['lang'] | h}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${ah['title'] | h} | ${ah['site_title'] | h}</title>
% if ah['summary']:
<meta name="description" content="${ah['summary'] | h}">
% endif
<script>
(function () {
  var d = document.documentElement, p = new URLSearchParams(location.search), t = p.get("theme");
  if (t !== "dark" && t !== "light") {
    try { t = localStorage.getItem("apphelp-theme"); } catch (e) { t = null; }
  }
  if (t === "dark" || t === "light") { d.setAttribute("data-theme", t); }
  if (p.get("embed") === "1") { d.setAttribute("data-embed", "1"); }
  d.className += " ah-js";
})();
</script>
<link rel="stylesheet" href="${A}/css/apphelp.css">
<style>:root { --ah-accent: ${ah['accent']}; }</style>
</head>
<body class="${ah['body_class'] | h}">
<a class="ah-skip" href="#ah-main">${L['skip'] | h}</a>
<header class="ah-header">
  <button class="ah-nav-toggle" id="ah-nav-toggle" type="button" aria-controls="ah-sidebar" aria-expanded="false">${L['menu'] | h}</button>
  <a class="ah-brand" href="index.html">
% if ah['logo']:
    <img src="${ah['logo'] | h}" alt="" width="28" height="28">
% endif
    <span>${ah['site_title'] | h}</span>
  </a>
  <form class="ah-search" action="search.html" role="search" autocomplete="off">
    <input id="ah-search-input" name="q" type="search" placeholder="${L['search_placeholder'] | h}" aria-label="${L['search'] | h}" aria-controls="ah-search-dropdown">
    <div id="ah-search-dropdown" class="ah-dropdown" hidden></div>
  </form>
  <button id="ah-theme-toggle" class="ah-icon-button" type="button" aria-label="${L['theme_toggle'] | h}" title="${L['theme_toggle'] | h}">&#9680;</button>
</header>
<div class="ah-layout">
  <nav class="ah-sidebar" id="ah-sidebar" aria-label="${L['menu'] | h}">
    <a class="ah-sidebar-top" href="topics.html">${L['topics'] | h}</a>
% for section in ah['sections']:
    <details class="ah-section"${' open' if section['current'] else ''}>
      <summary>${section['name'] | h}</summary>
      <ul>
%   for item in section['pages']:
        <li><a href="${item['url'] | h}"${' aria-current="page"' if item['current'] else ''}>${item['title'] | h}</a></li>
%   endfor
      </ul>
    </details>
% endfor
  </nav>
  <main class="ah-main" id="ah-main">
% if chips:
    <nav class="ah-breadcrumb" aria-label="${L['breadcrumb'] | h}"><a href="index.html">${L['home'] | h}</a> <span aria-hidden="true">&#8250;</span> ${chips['section'] | h}</nav>
% endif
    <article class="ah-article">
      <h1>${ah['title'] | h}</h1>
% if chips:
      <div class="ah-chips">
        <span class="ah-badge ah-badge-${chips['doctype'] | h}">${chips['doctype_label'] | h}</span>
%   for feature in chips['features']:
        <a class="ah-chip" href="topics.html#${feature['anchor']}">${feature['name'] | h}</a>
%   endfor
%   if chips['level']:
        <span class="ah-chip ah-chip-muted">${chips['level'] | h}</span>
%   endif
%   for platform in chips['platforms']:
        <span class="ah-chip ah-chip-muted">${platform | h}</span>
%   endfor
%   if chips['since']:
        <span class="ah-chip ah-chip-new">${L['new_in'] | h} ${chips['since'] | h}</span>
%   endif
      </div>
%   if chips['plugin']:
      <p class="ah-plugin">${L['plugin'] | h}: <strong>${chips['plugin'] | h}</strong></p>
%   endif
% endif
% if ah['toc']:
      <details class="ah-toc-inline">
        <summary>${L['on_this_page'] | h}</summary>
        <ul>
%   for item in ah['toc']:
          <li class="ah-toc-l${item['level']}"><a href="#${item['id'] | h}">${item['text'] | h}</a></li>
%   endfor
        </ul>
      </details>
% endif
      <div class="ah-content" id="ah-article-body">
${ah['content']}
      </div>
% if ah['prev'] or ah['next']:
      <nav class="ah-pager" aria-label="${L['previous'] | h} / ${L['next'] | h}">
%   if ah['prev']:
        <a class="ah-prev" href="${ah['prev']['url'] | h}" rel="prev"><span>${L['previous'] | h}</span>${ah['prev']['title'] | h}</a>
%   endif
%   if ah['next']:
        <a class="ah-next" href="${ah['next']['url'] | h}" rel="next"><span>${L['next'] | h}</span>${ah['next']['title'] | h}</a>
%   endif
      </nav>
% endif
% if ah['related']:
      <section class="ah-related">
        <h2>${L['related'] | h}</h2>
        <ul class="ah-list">
%   for item in ah['related']:
          <li><span class="ah-badge ah-badge-${item['doctype'] | h}">${item['doctype_label'] | h}</span> <a href="${item['url'] | h}">${item['title'] | h}</a><br><span class="ah-muted">${item['summary'] | h}</span></li>
%   endfor
        </ul>
      </section>
% endif
    </article>
  </main>
% if ah['toc']:
  <aside class="ah-toc" aria-label="${L['on_this_page'] | h}">
    <p class="ah-toc-title">${L['on_this_page'] | h}</p>
    <ul>
%   for item in ah['toc']:
      <li class="ah-toc-l${item['level']}"><a href="#${item['id'] | h}">${item['text'] | h}</a></li>
%   endfor
    </ul>
  </aside>
% endif
</div>
<footer class="ah-footer">
  <span>${ah['footer_name'] | h}</span>
% if ah['edit_url']:
  <a href="${ah['edit_url'] | h}">${L['edit'] | h}</a>
% endif
% if ah['updated']:
  <span>${L['updated'] | h}: ${ah['updated'] | h}</span>
% endif
  <a href="https://github.com/t00m/KB4IT">${L['built_with'] | h}</a>
</footer>
<script>window.APPHELP_LABELS = ${ah['labels_json']};</script>
<script src="search-index.js"></script>
% if ah['load_helpids']:
<script src="helpids.js"></script>
% endif
<script src="${A}/js/search.js"></script>
<script src="${A}/js/apphelp.js"></script>
</body>
</html>
