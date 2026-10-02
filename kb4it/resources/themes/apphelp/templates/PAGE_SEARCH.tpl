<%
    L = var['ah']['labels']
%>
<div id="ah-search-page" class="ah-search-page">
  <form id="ah-search-form" class="ah-hero-search" action="search.html" role="search">
    <input id="ah-search-page-input" name="q" type="search" placeholder="${L['search_placeholder'] | h}" aria-label="${L['search'] | h}">
    <button type="submit">${L['search'] | h}</button>
  </form>
  <div class="ah-search-grid">
    <aside id="ah-facets" class="ah-facets" aria-label="${L['filters'] | h}"></aside>
    <div>
      <p id="ah-search-count" class="ah-muted" aria-live="polite"></p>
      <ol id="ah-results" class="ah-results"></ol>
    </div>
  </div>
  <noscript><p><a href="topics.html">${L['topics'] | h}</a></p></noscript>
</div>
