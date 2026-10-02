<%
    L = var['ah']['labels']
%>
<p>${L['not_found_text'] | h}</p>
<form class="ah-hero-search" action="search.html" role="search">
  <input name="q" type="search" placeholder="${L['search_placeholder'] | h}" aria-label="${L['search'] | h}">
  <button type="submit">${L['search'] | h}</button>
</form>
<p><a href="index.html">${L['home'] | h}</a> &#183; <a href="topics.html">${L['topics'] | h}</a></p>
