/* AppHelp search engine: scores the records in window.APPHELP_INDEX. No dependencies. */
(function (root) {
  "use strict";

  var WEIGHTS = { title: 10, keyword: 8, heading: 5, summary: 4, facet: 3, body: 1 };
  var KEEP = ["embed", "theme"];

  function fold(text) {
    return String(text || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }

  function tokenize(text) {
    return fold(text).split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  }

  function has(tokens, word, prefix) {
    for (var i = 0; i < tokens.length; i++) {
      if (prefix ? tokens[i].indexOf(word) === 0 : tokens[i] === word) { return true; }
    }
    return false;
  }

  function prepare(records) {
    return records.map(function (r) {
      var facetWords = (r.g || []).slice();
      Object.keys(r.f || {}).forEach(function (name) { facetWords = facetWords.concat(r.f[name]); });
      return {
        rec: r,
        title: tokenize(r.t),
        keyword: tokenize((r.w || []).join(" ")),
        summary: tokenize(r.s),
        facet: tokenize(facetWords.join(" ")),
        sections: (r.x || []).map(function (s) {
          return { id: s[0], heading: s[1], headingTokens: tokenize(s[1]), body: tokenize(s[2]) };
        })
      };
    });
  }

  // Every word must match somewhere; the last word may be the start of a word.
  function scoreRecord(p, words) {
    var total = 0;
    var sectionScores = p.sections.map(function () { return 0; });
    for (var w = 0; w < words.length; w++) {
      var word = words[w], prefix = w === words.length - 1, top = 0;
      if (has(p.title, word, prefix)) { top = Math.max(top, WEIGHTS.title); }
      if (has(p.keyword, word, prefix)) { top = Math.max(top, WEIGHTS.keyword); }
      if (has(p.summary, word, prefix)) { top = Math.max(top, WEIGHTS.summary); }
      if (has(p.facet, word, prefix)) { top = Math.max(top, WEIGHTS.facet); }
      for (var s = 0; s < p.sections.length; s++) {
        var sec = p.sections[s], here = 0;
        if (has(sec.headingTokens, word, prefix)) { here = WEIGHTS.heading; }
        else if (has(sec.body, word, prefix)) { here = WEIGHTS.body; }
        sectionScores[s] += here;
        top = Math.max(top, here);
      }
      if (top === 0) { return null; }
      total += top;
    }
    var best = null, bestScore = 0;
    for (var i = 0; i < sectionScores.length; i++) {
      if (sectionScores[i] > bestScore) { bestScore = sectionScores[i]; best = p.sections[i]; }
    }
    return { score: total, section: best };
  }

  function matchesFilters(rec, filters) {
    var names = Object.keys(filters || {});
    for (var i = 0; i < names.length; i++) {
      var wanted = filters[names[i]];
      if (!wanted || wanted.length === 0) { continue; }
      var have = (rec.f && rec.f[names[i]]) || [];
      if (!have.some(function (v) { return wanted.indexOf(v) !== -1; })) { return false; }
    }
    return true;
  }

  function Engine(records) {
    this.items = prepare(records || []);
  }

  Engine.prototype.search = function (query, filters) {
    var words = tokenize(query), out = [];
    for (var i = 0; i < this.items.length; i++) {
      var p = this.items[i];
      if (!matchesFilters(p.rec, filters)) { continue; }
      if (words.length === 0) {
        out.push({ record: p.rec, score: 0, section: null, url: p.rec.u });
        continue;
      }
      var hit = scoreRecord(p, words);
      if (hit) {
        var anchor = hit.section && hit.section.id ? "#" + hit.section.id : "";
        out.push({ record: p.rec, score: hit.score, section: hit.section, url: p.rec.u + anchor });
      }
    }
    out.sort(function (a, b) { return b.score - a.score || a.record.t.localeCompare(b.record.t); });
    return out;
  };

  Engine.prototype.facets = function (results) {
    var counts = {};
    results.forEach(function (r) {
      Object.keys(r.record.f || {}).forEach(function (name) {
        counts[name] = counts[name] || {};
        r.record.f[name].forEach(function (v) { counts[name][v] = (counts[name][v] || 0) + 1; });
      });
    });
    return counts;
  };

  function isInternal(href) {
    return Boolean(href) && href.charAt(0) !== "#" && href.charAt(0) !== "/" &&
      !/^[a-z][a-z0-9+.-]*:/i.test(href);
  }

  // Copy embed and theme from the current page's query into an internal link, before its fragment.
  function withParams(href, search) {
    var current = new URLSearchParams(search || "");
    var keep = KEEP.filter(function (k) { return current.has(k); });
    if (!keep.length || !isInternal(href)) { return href; }
    var hash = "", cut = href.indexOf("#");
    if (cut !== -1) { hash = href.slice(cut); href = href.slice(0, cut); }
    var parts = href.split("?");
    var query = new URLSearchParams(parts[1] || "");
    keep.forEach(function (k) { query.set(k, current.get(k)); });
    return parts[0] + "?" + query.toString() + hash;
  }

  root.AppHelpSearch = { Engine: Engine, fold: fold, tokenize: tokenize, withParams: withParams };
})(typeof window !== "undefined" ? window : globalThis);
