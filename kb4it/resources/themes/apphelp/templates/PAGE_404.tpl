<%
    L = var['ah']['labels']
%>
<p>${L['not_found_text']}</p>
<form class="ah-hero-search" action="search.html" role="search">
  <input name="q" type="search" placeholder="${L['search_placeholder']}" aria-label="${L['search']}">
  <button type="submit">${L['search']}</button>
</form>
<p><a href="index.html">${L['home']}</a> &#183; <a href="topics.html">${L['topics']}</a></p>
