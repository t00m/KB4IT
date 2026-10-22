/* KB4IT editor of the techdoc Add page (ED-04, ED-05, ED-06).
 * Needs codemirror.min.js (KB4ITEditor.cm) and kb4it-frontmatter.js, loaded before it.
 * Document data reaches the DOM only through textContent, setAttribute or CodeMirror. */
(function (E) {
  "use strict";

  var cm = E.cm;
  var TAB = "    ";
  var DISCARD = "Discard your changes and start again?";

  E.views = {};
  var base = {};      // text at creation or at the last save, per category
  var look = {};      // Compartment of the light or dark look, per category
  var data = null;

  // keys: {Key: [{v, c}]} of the repository; skeletons: {cat: Markdown}.
  function load() {
    if (!data) {
      data = {
        keys: JSON.parse(document.getElementById("kb-add-keys").textContent),
        skeletons: JSON.parse(document.getElementById("kb-add-skeletons").textContent)
      };
    }
    return data;
  }

  E.keys = function () { return load().keys; };

  // YYYY-MM-DD in local time.
  function timestamp() {
    var d = new Date();
    var p = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  }

  // The skeleton of a category with today's date and a title placeholder.
  E.skeleton = function (cat) {
    var lines = load().skeletons[cat].split("\n");
    var out = [];
    var inFm = false, fmDone = false, fmCount = 0, titleReplaced = false;
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (!fmDone && line.trim() === "---") {
        fmCount++;
        if (fmCount === 1) { inFm = true; out.push(line); continue; }
        if (fmCount === 2) { inFm = false; fmDone = true; out.push(line); continue; }
      }
      if (inFm) {
        out.push(/^Date:/.test(line) ? "Date: " + timestamp() : line);
      } else if (fmDone && !titleReplaced && /^#\s+/.test(line)) {
        out.push("# " + cat.charAt(0).toUpperCase() + cat.slice(1) + " title");
        titleReplaced = true;
      } else {
        out.push(line);
      }
    }
    return out.join("\n");
  };

  // True when the first opaque background from body up is dark (same rule as kb4it-render.js).
  function pageIsDark() {
    for (var el = document.body; el; el = el.parentElement) {
      var rgb = getComputedStyle(el).backgroundColor.match(/^rgba?\(([^)]*)\)/);
      if (!rgb) { continue; }
      var c = rgb[1].split(/[\s,\/]+/).map(parseFloat);
      if (c.length > 3 && c[3] === 0) { continue; }
      return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255 < 0.5;
    }
    return false;
  }

  // Colours come from the custom properties of kb4it-editor.css.
  var t = cm.tags;
  var highlight = cm.HighlightStyle.define([
    { tag: t.heading, color: "var(--kb4it-cm-heading)", fontWeight: "bold" },
    { tag: t.emphasis, fontStyle: "italic" },
    { tag: t.strong, fontWeight: "bold" },
    { tag: t.strikethrough, textDecoration: "line-through" },
    { tag: [t.link, t.url], color: "var(--kb4it-cm-link)" },
    { tag: t.monospace, color: "var(--kb4it-cm-code)" },
    { tag: t.quote, color: "var(--kb4it-cm-quote)", fontStyle: "italic" },
    { tag: [t.processingInstruction, t.contentSeparator, t.meta, t.list], color: "var(--kb4it-cm-mark)" },
    { tag: [t.propertyName, t.definition(t.propertyName)], color: "var(--kb4it-cm-key)" },
    { tag: [t.string, t.content], color: "var(--kb4it-cm-text)" },
    { tag: [t.atom, t.bool, t.number, t.keyword], color: "var(--kb4it-cm-atom)" },
    { tag: t.comment, color: "var(--kb4it-cm-comment)", fontStyle: "italic" },
    { tag: t.invalid, color: "var(--kb4it-cm-invalid)" }
  ]);

  function lookFor(dark) {
    return [
      cm.EditorView.theme({
        "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground":
          { backgroundColor: "var(--kb4it-cm-selection)" }
      }, { dark: dark }),
      cm.EditorView.editorAttributes.of({ "class": dark ? "kb4it-cm kb4it-cm-dark" : "kb4it-cm" }),
      cm.syntaxHighlighting(highlight)
    ];
  }

  // Tab with a selection indents its lines; on an empty cursor it inserts four spaces. Escape then Tab
  // still leaves the editor (CodeMirror's tab focus mode).
  function insertTab(view) {
    if (!view.state.selection.main.empty) { return cm.indentMore(view); }
    view.dispatch(view.state.replaceSelection(TAB), { scrollIntoView: true, userEvent: "input" });
    return true;
  }

  // ED-05: property names and values of the repository, from KB4ITFrontmatter.complete.
  function completionSource(context) {
    var result = KB4ITFrontmatter.complete(context.state.doc.toString(), context.pos, E.keys());
    if (!result || !result.options.length) { return null; }
    return {
      from: result.from,
      options: result.options.map(function (o) {
        var option = { label: o.label, detail: o.detail, type: "text" };
        if (typeof o.from === "number") {
          // A whole-value rewrite (plain list turned into a flow list).
          option.apply = function (view) {
            view.dispatch({
              changes: { from: o.from, to: o.to, insert: o.insert },
              selection: { anchor: o.from + o.insert.length },
              userEvent: "input.complete"
            });
          };
        } else {
          option.apply = o.insert;
        }
        return option;
      })
    };
  }

  // Error nodes of the YAML tree inside the frontmatter, one per line.
  function yamlTreeErrors(state) {
    var text = state.doc.toString();
    var b = KB4ITFrontmatter.bounds(text);
    var out = [];
    if (!b.open || b.close === null) { return out; }
    var lines = {};
    cm.syntaxTree(state).iterate({
      from: b.start,
      to: b.end,
      enter: function (node) {
        if (!node.type.isError) { return; }
        var line = state.doc.lineAt(Math.min(node.from, b.end));
        if (line.from < b.start || line.from >= b.end || lines[line.number]) { return; }
        lines[line.number] = true;
        out.push({
          from: line.from, to: line.to, severity: "error", reason: "yaml_error",
          message: "YAML syntax error in the frontmatter."
        });
      }
    });
    return out;
  }

  // ED-06: the line checks of KB4ITFrontmatter plus the YAML tree errors that they do not report.
  function diagnosticsOf(state) {
    var found = KB4ITFrontmatter.lint(state.doc.toString(), E.keys());
    var reported = found.some(function (d) { return d.reason === "yaml_error" || d.reason === "invalid_frontmatter"; });
    if (!reported) { found = found.concat(yamlTreeErrors(state)); }
    return found;
  }

  E.diagnostics = function (cat) {
    var view = E.views[cat];
    if (!view) { return []; }
    return diagnosticsOf(view.state).map(function (d) {
      return { reason: d.reason, severity: d.severity, from: d.from, to: d.to, message: d.message };
    });
  };

  function lintSource(view) {
    return diagnosticsOf(view.state).map(function (d) {
      var to = d.to;
      if (to <= d.from) { to = view.state.doc.lineAt(d.from).to; }
      return { from: d.from, to: Math.max(to, d.from), severity: d.severity, message: d.message, source: d.reason };
    });
  }

  // Every extension of a category's editor. Later features append theirs here.
  E.extensions = function (cat) {
    if (!look[cat]) { look[cat] = new cm.Compartment(); }
    return [
      cm.lineNumbers(),
      cm.highlightActiveLine(),
      cm.drawSelection(),
      cm.history(),
      cm.closeBrackets(),
      cm.EditorView.lineWrapping,
      cm.EditorState.tabSize.of(4),
      cm.indentUnit.of(TAB),
      cm.autocompletion({ override: [completionSource] }),
      cm.linter(lintSource, { delay: 150 }),
      cm.lintGutter(),
      cm.keymap.of([{ key: "Tab", run: insertTab }, { key: "Shift-Tab", run: cm.indentLess }]),
      cm.keymap.of([].concat(cm.closeBracketsKeymap, cm.defaultKeymap, cm.searchKeymap, cm.historyKeymap)),
      cm.yamlFrontmatter({ content: cm.markdown() }),
      look[cat].of(lookFor(pageIsDark()))
    ];
  };

  function freshState(cat) {
    var doc = E.skeleton(cat);
    base[cat] = doc;
    return cm.EditorState.create({ doc: doc, extensions: E.extensions(cat) });
  }

  E.text = function (cat) {
    var view = E.views[cat];
    return view ? view.state.doc.toString() : "";
  };

  // True when the text differs from the one at creation or at the last save.
  E.dirty = function (cat) {
    return !!E.views[cat] && E.text(cat) !== base[cat];
  };

  // Called after a save: the current text becomes the clean one.
  E.markClean = function (cat) {
    if (E.views[cat]) { base[cat] = E.text(cat); }
  };

  function clear(node) {
    while (node.firstChild) { node.removeChild(node.firstChild); }
  }

  // Right pane: one accordion entry per property with a word cloud of its values.
  function buildAccordion(cat) {
    var container = document.getElementById("kb-accord-" + cat);
    if (!container) { return; }
    clear(container);
    var keys = E.keys();
    var ul = document.createElement("ul");
    ul.setAttribute("uk-accordion", "");
    Object.keys(keys).sort(function (a, b) {
      return a.toLowerCase().localeCompare(b.toLowerCase());
    }).forEach(function (name) {
      var items = keys[name];
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.className = "uk-accordion-title";
      a.setAttribute("href", "");
      a.appendChild(document.createTextNode(name));
      if (items.length > 0) {
        var count = document.createElement("span");
        count.className = "kb-accord-count";
        count.textContent = "(" + items.length + ")";
        a.appendChild(count);
      }
      var content = document.createElement("div");
      content.className = "uk-accordion-content";
      var cloud = document.createElement("div");
      cloud.className = "kb-wcloud";
      if (items.length > 0) {
        var maxC = 1;
        items.forEach(function (it) { if (it.c > maxC) { maxC = it.c; } });
        var logMax = Math.log(1 + maxC) || 1;
        items.forEach(function (it) {
          var sp = document.createElement("span");
          sp.className = "kb-wcloud-word";
          sp.style.setProperty("--kb-weight", (Math.log(1 + it.c) / logMax).toFixed(3));
          sp.textContent = it.v;
          sp.setAttribute("title", it.c + (it.c === 1 ? " document" : " documents"));
          cloud.appendChild(sp);
        });
      } else {
        var empty = document.createElement("span");
        empty.className = "kb-wcloud-empty";
        empty.textContent = "No values yet";
        cloud.appendChild(empty);
      }
      content.appendChild(cloud);
      li.appendChild(a);
      li.appendChild(content);
      ul.appendChild(li);
    });
    container.appendChild(ul);
  }

  // Creates the editor on the first open; on a later open, starts again unless the
  // user keeps an edited document.
  E.open = function (cat) {
    var view = E.views[cat];
    if (!view) {
      var host = document.getElementById("kb-editor-" + cat);
      // Escape belongs to the editor (search, completion, then Tab to leave): the modal must not close.
      host.addEventListener("keydown", function (event) {
        if (event.key === "Escape") { event.stopPropagation(); }
      });
      view = new cm.EditorView({ state: freshState(cat), parent: host });
      E.views[cat] = view;
      buildAccordion(cat);
    } else if (!E.dirty(cat) || window.confirm(DISCARD)) {
      view.setState(freshState(cat));
    } else {
      view.dispatch({ effects: look[cat].reconfigure(lookFor(pageIsDark())) });
    }
    var shown = UIkit.modal("#modal-add-" + cat).show();
    var ready = function () { view.requestMeasure(); view.focus(); };
    if (shown && typeof shown.then === "function") { shown.then(ready); } else { ready(); }
  };

  // Clipboard API first; a hidden textarea and execCommand where it is not allowed.
  E.copy = function (cat) {
    var text = E.text(cat);
    var done = function () {
      UIkit.notification({ message: "Copied to clipboard", status: "success", timeout: 2000 });
    };
    var fallback = function () {
      var area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(area);
      if (ok) { done(); } else {
        UIkit.notification({ message: "Copy failed: select the text and copy it by hand", status: "danger" });
      }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  };
})(KB4ITEditor);
