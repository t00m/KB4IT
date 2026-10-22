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

  // ---- ED-07: Properties pane ----

  var NO_COMMA = "A value cannot contain a comma: KB4IT splits values on commas.";
  var NEW_PROP = "__new__";
  var expanded = {};  // cat -> {key: true}: rows whose word cloud is open
  var focusKey = {};  // cat -> key whose value input gets the focus after a redraw

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  // Word cloud of {v, c} items, weights as in the old accordion. pick(value) is called on a click.
  function buildCloud(items, pick) {
    var cloud = el("div", "kb-wcloud");
    if (!items || !items.length) {
      cloud.appendChild(el("span", "kb-wcloud-empty", "No values yet"));
      return cloud;
    }
    var maxC = 1;
    items.forEach(function (it) { if (it.c > maxC) { maxC = it.c; } });
    var logMax = Math.log(1 + maxC) || 1;
    items.forEach(function (it) {
      var sp = el("span", "kb-wcloud-word", it.v);
      sp.style.setProperty("--kb-weight", (Math.log(1 + it.c) / logMax).toFixed(3));
      sp.setAttribute("title", it.c + (it.c === 1 ? " document" : " documents"));
      sp.setAttribute("role", "button");
      sp.setAttribute("tabindex", "0");
      sp.setAttribute("data-value", it.v);
      sp.addEventListener("click", function () { pick(it.v); });
      sp.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); pick(it.v); }
      });
      cloud.appendChild(sp);
    });
    return cloud;
  }

  // One entry per key, in text order; the last occurrence wins, as PyYAML does.
  function rowsOf(parsed) {
    var order = [];
    var byKey = {};
    parsed.props.forEach(function (p) {
      if (!byKey[p.key]) { order.push(p.key); }
      byKey[p.key] = p;
    });
    return order.map(function (k) { return byKey[k]; });
  }

  // Replaces the property's line (one transaction, so undo restores it) and redraws the pane.
  function change(cat, key, values) {
    var view = E.views[cat];
    var c = KB4ITFrontmatter.setValues(view.state.doc.toString(), key, values);
    if (c && (c.from !== c.to || c.insert !== "")) {
      view.dispatch({ changes: { from: c.from, to: c.to, insert: c.insert }, userEvent: "input.form" });
    }
    focusKey[cat] = key;
    E.renderPane(cat);
  }

  function addValue(cat, prop, value, message) {
    var v = value.trim();
    if (!v) { return; }
    if (v.indexOf(",") !== -1) { message.textContent = NO_COMMA; return; }
    if (prop.values.indexOf(v) !== -1) { message.textContent = "Already there: " + v; return; }
    change(cat, prop.key, prop.values.concat([v]));
  }

  function suggestionsFor(prop, typed) {
    var q = typed.trim().toLowerCase();
    return (E.keys()[prop.key] || []).filter(function (it) {
      return prop.values.indexOf(it.v) === -1 && (!q || it.v.toLowerCase().indexOf(q) !== -1);
    }).sort(function (a, b) { return b.c - a.c || a.v.localeCompare(b.v); }).slice(0, 12);
  }

  function buildValueInput(cat, prop, message) {
    var wrap = el("div", "kb-value-wrap");
    var input = el("input", "kb-value-input uk-input uk-form-small");
    input.setAttribute("type", "text");
    input.setAttribute("placeholder", "Add a value");
    input.setAttribute("autocomplete", "off");
    var list = el("ul", "kb-suggest");
    list.hidden = true;
    var active = -1;

    function items() { return Array.prototype.slice.call(list.children); }
    function mark(i) {
      active = i;
      items().forEach(function (li, n) { li.classList.toggle("kb-suggest-active", n === i); });
    }
    function refresh() {
      while (list.firstChild) { list.removeChild(list.firstChild); }
      var found = suggestionsFor(prop, input.value);
      found.forEach(function (it) {
        var li = el("li", "kb-suggest-item");
        li.setAttribute("data-value", it.v);
        li.appendChild(el("span", "kb-suggest-value", it.v));
        li.appendChild(el("span", "kb-suggest-count", String(it.c)));
        li.addEventListener("mousedown", function (event) {
          event.preventDefault();
          addValue(cat, prop, it.v, message);
        });
        list.appendChild(li);
      });
      list.hidden = !found.length;
      active = -1;
    }

    input.addEventListener("input", function () {
      message.textContent = input.value.indexOf(",") !== -1 ? NO_COMMA : "";
      refresh();
    });
    input.addEventListener("focus", refresh);
    input.addEventListener("blur", function () { list.hidden = true; });
    input.addEventListener("keydown", function (event) {
      var shown = items();
      if (event.key === "ArrowDown" && shown.length) {
        event.preventDefault();
        list.hidden = false;
        mark((active + 1) % shown.length);
      } else if (event.key === "ArrowUp" && shown.length) {
        event.preventDefault();
        mark((active - 1 + shown.length) % shown.length);
      } else if (event.key === "Enter") {
        event.preventDefault();
        var chosen = active >= 0 && !list.hidden ? shown[active].getAttribute("data-value") : input.value;
        addValue(cat, prop, chosen, message);
      } else if (event.key === "Escape" && !list.hidden) {
        event.stopPropagation();
        list.hidden = true;
      }
    });
    wrap.appendChild(input);
    wrap.appendChild(list);
    return wrap;
  }

  function buildRow(cat, prop) {
    var row = el("div", "kb-prop-row");
    row.setAttribute("data-key", prop.key);
    var head = el("div", "kb-prop-head");
    head.appendChild(el("span", "kb-prop-name", prop.key));
    var tools = el("span", "kb-prop-tools");
    if (!prop.complex) {
      var toggle = el("button", "kb-cloud-toggle uk-button uk-button-link", "Cloud");
      toggle.setAttribute("type", "button");
      toggle.setAttribute("title", "Show the values used in the repository");
      var remove = el("button", "kb-prop-remove uk-button uk-button-link", "Remove");
      remove.setAttribute("type", "button");
      remove.setAttribute("title", "Remove this property");
      remove.addEventListener("click", function () { change(cat, prop.key, null); });
      tools.appendChild(toggle);
      tools.appendChild(remove);
      head.appendChild(tools);
      row.appendChild(head);

      var chips = el("div", "kb-chips");
      prop.values.forEach(function (v) {
        var chip = el("span", "kb-chip");
        chip.setAttribute("data-value", v);
        chip.appendChild(el("span", "kb-chip-text", v));
        var x = el("button", "kb-chip-remove", "×");
        x.setAttribute("type", "button");
        x.setAttribute("title", "Remove " + v);
        x.addEventListener("click", function () {
          change(cat, prop.key, prop.values.filter(function (o) { return o !== v; }));
        });
        chip.appendChild(x);
        chips.appendChild(chip);
      });
      row.appendChild(chips);
      var message = el("div", "kb-prop-msg");
      message.setAttribute("role", "status");
      row.appendChild(buildValueInput(cat, prop, message));
      row.appendChild(message);

      var cloudHost = el("div", "kb-cloud-host");
      cloudHost.hidden = !(expanded[cat] && expanded[cat][prop.key]);
      cloudHost.appendChild(buildCloud(E.keys()[prop.key], function (v) { addValue(cat, prop, v, message); }));
      toggle.addEventListener("click", function () {
        expanded[cat] = expanded[cat] || {};
        expanded[cat][prop.key] = cloudHost.hidden;
        cloudHost.hidden = !cloudHost.hidden;
      });
      row.appendChild(cloudHost);
    } else {
      row.appendChild(head);
      row.appendChild(el("div", "kb-prop-complex", "Edit this property in the text"));
    }
    return row;
  }

  // The selector of properties of the repository that the document does not have, plus a free name.
  function buildAdder(cat, present) {
    var wrap = el("div", "kb-add-wrap");
    var select = el("select", "kb-add-prop uk-select uk-form-small");
    var first = el("option", "", "Add property...");
    first.setAttribute("value", "");
    select.appendChild(first);
    Object.keys(E.keys()).sort(function (a, b) {
      return a.toLowerCase().localeCompare(b.toLowerCase());
    }).forEach(function (name) {
      if (present[name]) { return; }
      var o = el("option", "", name);
      o.setAttribute("value", name);
      select.appendChild(o);
    });
    var free = el("option", "", "New property...");
    free.setAttribute("value", NEW_PROP);
    select.appendChild(free);

    var box = el("div", "kb-new-prop");
    box.hidden = true;
    var name = el("input", "kb-new-prop-name uk-input uk-form-small");
    name.setAttribute("type", "text");
    name.setAttribute("placeholder", "Property name");
    var ok = el("button", "kb-new-prop-add uk-button uk-button-small uk-button-default", "Add");
    ok.setAttribute("type", "button");
    var message = el("div", "kb-prop-msg");
    message.setAttribute("role", "status");

    function create() {
      var n = name.value.trim();
      if (!n || KB4ITFrontmatter.validFilename(n) !== n) {
        message.textContent = "'" + n + "' cannot be used as a property name.";
        return;
      }
      if (present[n]) { message.textContent = "The document already has " + n + "."; return; }
      change(cat, n, []);
    }
    ok.addEventListener("click", create);
    name.addEventListener("keydown", function (event) {
      if (event.key === "Enter") { event.preventDefault(); create(); }
    });
    select.addEventListener("change", function () {
      message.textContent = "";
      if (select.value === NEW_PROP) {
        box.hidden = false;
        name.focus();
      } else if (select.value) {
        change(cat, select.value, []);
      } else {
        box.hidden = true;
      }
    });
    box.appendChild(name);
    box.appendChild(ok);
    wrap.appendChild(select);
    wrap.appendChild(box);
    wrap.appendChild(message);
    return wrap;
  }

  // Draws the Properties pane from the frontmatter of the editor text.
  E.renderPane = function (cat) {
    var container = document.getElementById("kb-props-" + cat);
    var view = E.views[cat];
    if (!container || !view) { return; }
    clear(container);
    var pane = container.closest(".kb-pane-right");
    if (pane) { pane.classList.toggle("kb-props-dark", pageIsDark()); }
    var parsed = KB4ITFrontmatter.parse(view.state.doc.toString());
    if (!parsed.ok) {
      container.appendChild(el("div", "kb-prop-error", "Fix the frontmatter in the text to edit the properties here."));
      return;
    }
    var present = {};
    var rows = rowsOf(parsed);
    rows.forEach(function (p) {
      present[p.key] = true;
      container.appendChild(buildRow(cat, p));
    });
    container.appendChild(buildAdder(cat, present));
    var key = focusKey[cat];
    focusKey[cat] = null;
    if (key) {
      var rowNode = Array.prototype.find.call(container.querySelectorAll(".kb-prop-row"), function (n) {
        return n.getAttribute("data-key") === key;
      });
      var input = rowNode && rowNode.querySelector(".kb-value-input");
      if (input) { input.focus(); }
    }
  };

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
    } else if (!E.dirty(cat) || window.confirm(DISCARD)) {
      view.setState(freshState(cat));
    } else {
      view.dispatch({ effects: look[cat].reconfigure(lookFor(pageIsDark())) });
    }
    E.renderPane(cat);
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
