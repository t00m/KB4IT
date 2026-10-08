/* KB4IT search box (results as you type) and search page (full results and filters). */
(function () {
  "use strict";
  var FACETS = ["Category", "Tag"];
  var engine = null;

  function getEngine() {
    if (!engine && window.KB4ITSearch && window.KB4IT_INDEX) { engine = new window.KB4ITSearch.Engine(window.KB4IT_INDEX); }
    return engine;
  }

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  function label(hit) {
    return hit.section && hit.section.heading ? hit.section.heading : (hit.record.c || "");
  }

  function setupBox() {
    var input = document.getElementById("kb4it-search-input");
    var box = document.getElementById("kb4it-search-dropdown");
    if (!input || !box) { return; }
    var active = -1;
    function close() { box.hidden = true; box.textContent = ""; active = -1; }
    function render() {
      var search = getEngine(), query = input.value.trim();
      if (!search || !query) { close(); return; }
      var hits = search.search(query, {}).slice(0, 8);
      box.textContent = "";
      if (!hits.length) { box.appendChild(el("a", {href: "search.html?q=" + encodeURIComponent(query)}, "No results; open search")); }
      hits.forEach(function (hit) {
        var link = el("a", {href: hit.url}, hit.record.t);
        if (label(hit)) { link.appendChild(el("small", {}, label(hit))); }
        box.appendChild(link);
      });
      box.hidden = false;
      active = -1;
    }
    input.addEventListener("input", render);
    input.addEventListener("keydown", function (e) {
      var links = box.querySelectorAll("a");
      if (e.key === "Escape") { close(); return; }
      if ((e.key === "ArrowDown" || e.key === "ArrowUp") && links.length) {
        e.preventDefault();
        active = (active + (e.key === "ArrowDown" ? 1 : links.length - 1)) % links.length;
        links.forEach(function (a, i) { a.classList.toggle("active", i === active); });
        links[active].focus({preventScroll: true});
        input.focus();
      }
      if (e.key === "Enter" && active >= 0 && links[active]) { e.preventDefault(); location.href = links[active].href; }
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target) && e.target !== input) { close(); } });
  }

  function setupPage() {
    var page = document.getElementById("kb4it-search-page");
    var input = document.getElementById("kb4it-search-page-input");
    var search = getEngine();
    if (!page || !input || !search) { return; }
    var list = document.getElementById("kb4it-search-results");
    var facetsBox = document.getElementById("kb4it-search-facets");
    var count = document.getElementById("kb4it-search-count");
    var filters = {};
    input.value = new URLSearchParams(location.search).get("q") || "";

    function renderFacets(results) {
      var counts = search.facets(results);
      facetsBox.textContent = "";
      FACETS.forEach(function (name) {
        var values = Object.keys(counts[name] || {}).sort();
        if (!values.length) { return; }
        var set = el("fieldset");
        set.appendChild(el("legend", {}, name));
        values.forEach(function (value) {
          var box = el("input", {type: "checkbox"});
          box.checked = (filters[name] || []).indexOf(value) !== -1;
          box.addEventListener("change", function () {
            var chosen = filters[name] || [];
            filters[name] = box.checked ? chosen.concat([value]) : chosen.filter(function (v) { return v !== value; });
            run();
          });
          var lab = el("label");
          lab.appendChild(box);
          lab.appendChild(document.createTextNode(" " + value + " (" + counts[name][value] + ")"));
          set.appendChild(lab);
        });
        facetsBox.appendChild(set);
      });
    }

    function run() {
      var query = input.value.trim();
      var all = search.search(query, {});
      var hits = search.search(query, filters);
      renderFacets(all);
      list.textContent = "";
      count.textContent = query ? hits.length + (hits.length === 1 ? " result" : " results") : "";
      if (!query) { return; }
      hits.forEach(function (hit) {
        var item = el("li");
        item.appendChild(el("a", {href: hit.url}, hit.record.t));
        if (label(hit)) { item.appendChild(el("div", {"class": "where"}, label(hit))); }
        if (hit.record.s) { item.appendChild(el("div", {}, hit.record.s)); }
        list.appendChild(item);
      });
    }
    document.getElementById("kb4it-search-form").addEventListener("submit", function (e) {
      e.preventDefault();
      history.replaceState(null, "", "search.html?q=" + encodeURIComponent(input.value.trim()));
      run();
    });
    input.addEventListener("input", run);
    run();
  }

  function start() { setupBox(); setupPage(); }
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", start); } else { start(); }
})();
