/* AppHelp page behaviour: colour scheme, embedded mode, drawer, FAQ, copy buttons and search UI. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var params = new URLSearchParams(location.search);
  var L = window.APPHELP_LABELS || {};
  var S = window.AppHelpSearch;
  var FACETS = ["Kind", "Feature", "Level", "Platform", "Plugin", "Since"];
  var KEEP = ["embed", "theme"];
  var engine = null;

  function label(name, fallback) { return L[name] || fallback; }
  function link(href) { return S ? S.withParams(href, location.search) : href; }
  function each(selector, fn) { Array.prototype.forEach.call(document.querySelectorAll(selector), fn); }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  function getEngine() {
    if (!engine && S && window.APPHELP_INDEX) { engine = new S.Engine(window.APPHELP_INDEX); }
    return engine;
  }

  function setupScheme() {
    var button = document.getElementById("ah-theme-toggle");
    if (!button) { return; }
    var order = ["auto", "light", "dark"];
    button.addEventListener("click", function () {
      var current = doc.getAttribute("data-theme") || "auto";
      var next = order[(order.indexOf(current) + 1) % order.length];
      if (next === "auto") { doc.removeAttribute("data-theme"); } else { doc.setAttribute("data-theme", next); }
      try {
        if (next === "auto") { localStorage.removeItem("apphelp-theme"); } else { localStorage.setItem("apphelp-theme", next); }
      } catch (e) { /* storage blocked, the choice lasts for this page only */ }
    });
  }

  function setupDrawer() {
    var button = document.getElementById("ah-nav-toggle");
    if (!button) { return; }
    button.addEventListener("click", function () {
      var open = document.body.classList.toggle("ah-drawer-open");
      button.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  function openFaqFromHash() {
    var id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { return; }
    var target = id && document.getElementById(id);
    var details = target && target.closest("details");
    if (details) { details.open = true; target.scrollIntoView(); }
  }

  function setupCopy() {
    each(".ah-copy", function (button) {
      if (!navigator.clipboard) { button.hidden = true; return; }
      button.textContent = label("copy", "Copy");
      button.addEventListener("click", function () {
        var pre = button.parentNode.querySelector("pre");
        if (!pre || !navigator.clipboard) { return; }
        navigator.clipboard.writeText(pre.textContent).then(function () {
          button.textContent = label("copied", "Copied");
          setTimeout(function () { button.textContent = label("copy", "Copy"); }, 1500);
        }, function () { /* clipboard refused */ });
      });
    });
    window.addEventListener("beforeprint", function () { each("details", function (d) { d.open = true; }); });
  }

  function resultItem(hit) {
    var li = el("li", "ah-result");
    var kind = hit.record.k;
    li.appendChild(el("span", "ah-badge ah-badge-" + kind, label("kind_" + kind, kind)));
    li.appendChild(document.createTextNode(" "));
    var a = el("a", "", hit.record.t);
    a.href = link(hit.url);
    li.appendChild(a);
    if (hit.section && hit.section.heading) { li.appendChild(el("span", "ah-muted", " › " + hit.section.heading)); }
    li.appendChild(el("p", "ah-muted", hit.record.s));
    return li;
  }

  function setupDropdown() {
    var input = document.getElementById("ah-search-input");
    var box = document.getElementById("ah-search-dropdown");
    if (!input || !box) { return; }
    var active = -1;
    function close() { box.hidden = true; box.innerHTML = ""; active = -1; }
    function anchors() { return box.querySelectorAll("a"); }
    function highlight(index) {
      var all = anchors();
      if (!all.length) { return; }
      active = (index + all.length) % all.length;
      Array.prototype.forEach.call(all, function (a, n) { a.classList.toggle("ah-active", n === active); });
    }
    input.addEventListener("input", function () {
      var search = getEngine(), query = input.value.trim();
      if (!search || !query) { close(); return; }
      var hits = search.search(query, {}).slice(0, 8);
      box.innerHTML = "";
      if (!hits.length) {
        box.appendChild(el("p", "ah-muted", label("no_results", "No results")));
      } else {
        var list = el("ul", "ah-dropdown-list");
        hits.forEach(function (hit) { list.appendChild(resultItem(hit)); });
        box.appendChild(list);
      }
      box.hidden = false;
      active = -1;
    });
    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") { event.preventDefault(); highlight(active + 1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); highlight(active - 1); }
      else if (event.key === "Escape") { close(); }
      else if (event.key === "Enter" && active >= 0) { event.preventDefault(); location.href = anchors()[active].href; }
    });
    document.addEventListener("click", function (event) {
      if (!box.contains(event.target) && event.target !== input) { close(); }
    });
    document.addEventListener("keydown", function (event) {
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (event.key === "/" && tag !== "INPUT" && tag !== "TEXTAREA") { event.preventDefault(); input.focus(); }
    });
  }

  function setupSearchPage() {
    var search = getEngine();
    var input = document.getElementById("ah-search-page-input");
    if (!search || !input) { return; }
    var form = document.getElementById("ah-search-form");
    var facetsBox = document.getElementById("ah-facets");
    var results = document.getElementById("ah-results");
    var count = document.getElementById("ah-search-count");
    var filters = {};
    FACETS.forEach(function (name) { var v = params.getAll(name); if (v.length) { filters[name] = v; } });
    input.value = params.get("q") || "";

    function syncUrl() {
      var query = new URLSearchParams();
      if (input.value.trim()) { query.set("q", input.value.trim()); }
      Object.keys(filters).forEach(function (name) { filters[name].forEach(function (v) { query.append(name, v); }); });
      KEEP.forEach(function (k) { if (params.has(k)) { query.set(k, params.get(k)); } });
      try { history.replaceState(null, "", "?" + query.toString()); } catch (e) { /* refused under file:// */ }
    }

    function facetRow(name, value, total) {
      var row = el("label", "ah-facet-row");
      var box = el("input");
      box.type = "checkbox";
      box.checked = (filters[name] || []).indexOf(value) !== -1;
      box.addEventListener("change", function () {
        var list = (filters[name] || []).filter(function (v) { return v !== value; });
        if (box.checked) { list.push(value); }
        if (list.length) { filters[name] = list; } else { delete filters[name]; }
        syncUrl();
        render();
      });
      row.appendChild(box);
      var text = name === "Kind" ? label("kind_" + value, value) : value;
      row.appendChild(document.createTextNode(" " + text + " (" + total + ")"));
      return row;
    }

    function render() {
      var counts = search.facets(search.search(input.value, {}));
      var hits = search.search(input.value, filters);
      results.innerHTML = "";
      hits.forEach(function (hit) { results.appendChild(resultItem(hit)); });
      count.textContent = hits.length ? hits.length + " " + label("results", "results") : label("no_results", "No results");
      facetsBox.innerHTML = "";
      FACETS.forEach(function (name) {
        var values = counts[name] ? Object.keys(counts[name]).sort() : [];
        if (!values.length) { return; }
        var set = el("fieldset", "ah-facet");
        set.appendChild(el("legend", "", label("facet_" + name, name)));
        values.forEach(function (value) { set.appendChild(facetRow(name, value, counts[name][value])); });
        facetsBox.appendChild(set);
      });
    }

    form.addEventListener("submit", function (event) { event.preventDefault(); syncUrl(); render(); });
    input.addEventListener("input", function () { syncUrl(); render(); });
    render();
  }

  function setupGo() {
    var box = document.getElementById("ah-go");
    if (!box) { return; }
    var id = params.get("id");
    var map = window.APPHELP_HELPIDS || {};
    if (id && Object.prototype.hasOwnProperty.call(map, id)) {
      location.replace(link(map[id]));
      return;
    }
    var message = document.getElementById("ah-go-message");
    if (message) { message.textContent = label("go_unknown", "Unknown help topic."); }
    var heading = document.querySelector(".ah-article h1");
    if (heading) { heading.textContent = label("not_found_title", "Page not found"); }
  }

  // Keep embed and theme on every internal link and form of the page.
  function setupLinks() {
    if (!params.has("embed") && !params.has("theme")) { return; }
    each("a[href]", function (a) { a.setAttribute("href", link(a.getAttribute("href"))); });
    each("form", function (form) {
      KEEP.forEach(function (k) {
        if (!params.has(k)) { return; }
        var hidden = el("input");
        hidden.type = "hidden";
        hidden.name = k;
        hidden.value = params.get(k);
        form.appendChild(hidden);
      });
    });
  }

  setupScheme();
  setupDrawer();
  setupCopy();
  setupDropdown();
  setupSearchPage();
  setupGo();
  setupLinks();
  openFaqFromHash();
  window.addEventListener("hashchange", openFaqFromHash);
})();
