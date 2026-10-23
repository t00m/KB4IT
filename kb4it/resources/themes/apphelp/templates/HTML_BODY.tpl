<%
    ah = var['ah']
    L = ah['labels']
    A = ah['assets']
    chips = ah['page']
%><!doctype html>
<html lang="${ah['lang']}">
<head>
<!-- PAGE METADATA :: START -->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${ah['title']} | ${ah['site_title']}</title>
% if ah['summary']:
<meta name="description" content="${ah['summary']}">
% endif
<!-- PAGE METADATA :: END -->
<!-- COLOUR THEME SETUP :: START -->
<!-- Runs before the page draws: dark or light theme from ?theme= or the saved choice, and embedded mode. -->
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
<!-- COLOUR THEME SETUP :: END -->
<!-- STYLESHEETS :: START -->
<link rel="stylesheet" href="${A}/css/apphelp.css">
% if ah.get('highlight') == 'pygments':
<link rel="stylesheet" href="resources/pygments.css">
% endif
<style>:root { --ah-accent: ${ah['accent']}; }</style>
<!-- STYLESHEETS :: END -->
</head>
<body class="${ah['body_class']}">
<!-- PAGE :: START -->
<a class="ah-skip" href="#ah-main">${L['skip']}</a>
<!-- TOP BAR :: START -->
<header class="ah-header">
  <button class="ah-nav-toggle" id="ah-nav-toggle" type="button" aria-controls="ah-sidebar" aria-expanded="false">${L['menu']}</button>
  <a class="ah-brand" href="index.html">
% if ah['logo']:
    <img src="${ah['logo']}" alt="" width="28" height="28">
% endif
    <span>${ah['site_title']}</span>
  </a>
  <!-- SEARCH BOX :: START -->
  <form class="ah-search" action="search.html" role="search" autocomplete="off">
    <input id="ah-search-input" name="q" type="search" placeholder="${L['search_placeholder']}" aria-label="${L['search']}" aria-controls="ah-search-dropdown">
    <div id="ah-search-dropdown" class="ah-dropdown" hidden></div>
  </form>
  <!-- SEARCH BOX :: END -->
% if ah.get('versions'):
  <select id="ah-version" class="ah-icon-button" aria-label="Version" data-current="${ah['version']}" hidden></select>
% endif
  <button id="ah-theme-toggle" class="ah-icon-button" type="button" aria-label="${L['theme_toggle']}" title="${L['theme_toggle']}">&#9680;</button>
</header>
<!-- TOP BAR :: END -->
<!-- LAYOUT :: START -->
<div class="ah-layout">
  <!-- SIDEBAR :: START -->
  <nav class="ah-sidebar" id="ah-sidebar" aria-label="${L['menu']}">
    <a class="ah-sidebar-top" href="topics.html">${L['topics']}</a>
% if ah.get('editor'):
    <a class="ah-sidebar-top" href="add.html">${L['add']}</a>
% endif
% for section in ah['sections']:
    <details class="ah-section"${' open' if section['current'] else ''}>
      <summary>${section['name']}</summary>
      <ul>
%   for item in section['pages']:
        <li><a href="${item['url']}"${(' aria-current="page"' if item['current'] else '') | n}>${item['title']}</a></li>
%   endfor
      </ul>
    </details>
% endfor
  </nav>
  <!-- SIDEBAR :: END -->
  <!-- MAIN CONTENT :: START -->
  <main class="ah-main" id="ah-main">
% if chips:
    <!-- BREADCRUMB :: START -->
    <nav class="ah-breadcrumb" aria-label="${L['breadcrumb']}"><a href="index.html">${L['home']}</a> <span aria-hidden="true">&#8250;</span> ${chips['section']}</nav>
    <!-- BREADCRUMB :: END -->
% endif
    <!-- ARTICLE :: START -->
    <article class="ah-article">
      <h1>${ah['title']}</h1>
% if chips:
      <!-- PAGE LABELS :: START -->
      <div class="ah-chips">
        <span class="ah-badge ah-badge-${chips['doctype']}">${chips['doctype_label']}</span>
%   for feature in chips['features']:
        <a class="ah-chip" href="topics.html#${feature['anchor']}">${feature['name']}</a>
%   endfor
%   if chips['level']:
        <span class="ah-chip ah-chip-muted">${chips['level']}</span>
%   endif
%   for platform in chips['platforms']:
        <span class="ah-chip ah-chip-muted">${platform}</span>
%   endfor
%   if chips['since']:
        <span class="ah-chip ah-chip-new">${L['new_in']} ${chips['since']}</span>
%   endif
      </div>
%   if chips['plugin']:
      <p class="ah-plugin">${L['plugin']}: <strong>${chips['plugin']}</strong></p>
%   endif
      <!-- PAGE LABELS :: END -->
% endif
% if ah['toc']:
      <!-- INLINE TABLE OF CONTENTS :: START -->
      <details class="ah-toc-inline">
        <summary>${L['on_this_page']}</summary>
        <ul>
%   for item in ah['toc']:
          <li class="ah-toc-l${item['level']}"><a href="#${item['id']}">${item['text']}</a></li>
%   endfor
        </ul>
      </details>
      <!-- INLINE TABLE OF CONTENTS :: END -->
% endif
      <!-- ARTICLE BODY :: START -->
      <div class="ah-content" id="ah-article-body">
${ah['content'] | n}
      </div>
      <!-- ARTICLE BODY :: END -->
% if ah['prev'] or ah['next']:
      <!-- PREVIOUS AND NEXT :: START -->
      <nav class="ah-pager" aria-label="${L['previous']} / ${L['next']}">
%   if ah['prev']:
        <a class="ah-prev" href="${ah['prev']['url']}" rel="prev"><span>${L['previous']}</span>${ah['prev']['title']}</a>
%   endif
%   if ah['next']:
        <a class="ah-next" href="${ah['next']['url']}" rel="next"><span>${L['next']}</span>${ah['next']['title']}</a>
%   endif
      </nav>
      <!-- PREVIOUS AND NEXT :: END -->
% endif
% if ah['related']:
      <!-- RELATED PAGES :: START -->
      <section class="ah-related">
        <h2>${L['related']}</h2>
        <ul class="ah-list">
%   for item in ah['related']:
          <li><span class="ah-badge ah-badge-${item['doctype']}">${item['doctype_label']}</span> <a href="${item['url']}">${item['title']}</a><br><span class="ah-muted">${item['summary']}</span></li>
%   endfor
        </ul>
      </section>
      <!-- RELATED PAGES :: END -->
% endif
    </article>
    <!-- ARTICLE :: END -->
  </main>
  <!-- MAIN CONTENT :: END -->
% if ah['toc']:
  <!-- TABLE OF CONTENTS :: START -->
  <aside class="ah-toc" aria-label="${L['on_this_page']}">
    <p class="ah-toc-title">${L['on_this_page']}</p>
    <ul>
%   for item in ah['toc']:
      <li class="ah-toc-l${item['level']}"><a href="#${item['id']}">${item['text']}</a></li>
%   endfor
    </ul>
  </aside>
  <!-- TABLE OF CONTENTS :: END -->
% endif
</div>
<!-- LAYOUT :: END -->
<!-- FOOTER :: START -->
<footer class="ah-footer">
  <span>${ah['footer_name']}</span>
% if ah['edit_url']:
  <a href="${ah['edit_url']}">${L['edit']}</a>
% endif
% if ah['updated']:
  <span>${L['updated']}: ${ah['updated']}</span>
% endif
  <a href="https://github.com/t00m/KB4IT">${L['built_with']}</a>
</footer>
<!-- FOOTER :: END -->
<!-- PAGE :: END -->
<!-- PAGE SCRIPTS :: START -->
<script>window.APPHELP_LABELS = ${ah['labels_json'] | n};</script>
<script src="search-index.js"></script>
% if ah['load_helpids']:
<script src="helpids.js"></script>
% endif
% if ah.get('versions'):
<script src="../versions.js"></script>
% endif
<script src="${A}/js/search.js"></script>
<script src="${A}/js/apphelp.js"></script>
<!-- PAGE SCRIPTS :: END -->
</body>
</html>
