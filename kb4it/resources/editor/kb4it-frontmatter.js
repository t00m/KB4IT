/* KB4IT frontmatter parser, quoting and name rules (ED-06, ED-08, ED-10).
 * No DOM code. Mirrors kb4it/core/documents.py and the name rules of
 * kb4it/core/files.py and kb4it/core/util.py. */
var KB4ITFrontmatter = (function () {
  "use strict";

  var FENCE_RE = /^ {0,3}(`{3,}|~{3,})/;
  var H1_RE = /^#[ \t]+(\S.*?)[ \t]*$/;
  var KEY_RE = /^(?!-[ \t])([^\s#:][^:]*?):(?:[ \t]+(.*))?$/;
  var RESERVED_RE = /^(null|~)$/i;
  var INDICATORS = "[]{}&*!|>'\"%@`";

  // Same rule as the build (documents.get_markdown_attributes): the text starts with
  // "---" and the frontmatter closes at the first "\n---" after offset 3.
  function bounds(text) {
    // The build reads sources as utf-8-sig, so a leading BOM is skipped; offsets stay in text.
    var off = text.charCodeAt(0) === 0xFEFF ? 1 : 0;
    if (text.indexOf("---", off) !== off) {
      return { open: false, close: null, start: 0, end: 0 };
    }
    var close = text.indexOf("\n---", off + 3);
    if (close < 0) {
      return { open: true, close: null, start: 0, end: 0 };
    }
    var nl = text.indexOf("\n", off + 3);
    return { open: true, close: close, start: nl + 1, end: close + 1 };
  }

  // Lines of text[start:end] with their offsets; "to" excludes the line break.
  function splitLines(text, start, end) {
    var lines = [];
    var pos = start;
    while (pos < end) {
      var nl = text.indexOf("\n", pos);
      if (nl < 0 || nl >= end) { nl = end; }
      var to = nl;
      if (to > pos && text.charAt(to - 1) === "\r") { to -= 1; }
      lines.push({ text: text.slice(pos, to), from: pos, to: to });
      pos = nl + 1;
    }
    return lines;
  }

  function isContinuation(line) {
    return /^[ \t]/.test(line) || /^-([ \t]|$)/.test(line);
  }

  function unquote(s) {
    // Returns the string for a whole quoted scalar, or null when s is not exactly one.
    var q = s.charAt(0);
    if (s.length < 2 || s.charAt(s.length - 1) !== q) { return null; }
    var inner = s.slice(1, -1);
    var out = "";
    for (var i = 0; i < inner.length; i++) {
      var c = inner.charAt(i);
      if (q === '"' && c === "\\") {
        if (i + 1 >= inner.length) { return null; }
        var n = inner.charAt(++i);
        if (n === "n") { out += "\n"; }
        else if (n === "t") { out += "\t"; }
        else if (n === "\\" || n === '"') { out += n; }
        else if (n === "u" && /^[0-9a-fA-F]{4}$/.test(inner.substr(i + 1, 4))) {
          out += String.fromCharCode(parseInt(inner.substr(i + 1, 4), 16));
          i += 4;
        } else { return null; }
      } else if (q === "'" && c === "'") {
        if (inner.charAt(i + 1) !== "'") { return null; }
        out += "'";
        i++;
      } else if (c === q) {
        return null;
      } else {
        out += c;
      }
    }
    return out;
  }

  function splitFlow(inner) {
    // Split a flow list body on commas outside quotes; null when it is not simple.
    var items = [];
    var cur = "";
    var q = null;
    for (var i = 0; i < inner.length; i++) {
      var c = inner.charAt(i);
      if (q) {
        cur += c;
        if (c === "\\" && q === '"') { cur += inner.charAt(++i); }
        else if (c === q) { q = null; }
      } else if (c === '"' || c === "'") {
        if (cur.trim() !== "") { return null; }
        q = c;
        cur += c;
      } else if (c === ",") {
        items.push(cur);
        cur = "";
      } else if (c === "[" || c === "]" || c === "{" || c === "}") {
        return null;
      } else {
        cur += c;
      }
    }
    if (q) { return null; }
    items.push(cur);
    return items;
  }

  var NULLS = ["null", "Null", "NULL", "~"];

  // How the build's loader (documents.load_frontmatter) reads a plain scalar: {skip: true}
  // for an empty value or null, otherwise {v: text} as written. Numbers, dates, yes and no
  // are text too.
  function resolve(s) {
    if (s === "" || NULLS.indexOf(s) >= 0) { return { skip: true }; }
    return { v: s };
  }

  function scalar(raw) {
    // One list item or scalar: {v}, {skip}, or null when the form is not in the subset.
    var s = raw.trim();
    if (s.charAt(0) === '"' || s.charAt(0) === "'") {
      var u = unquote(s);
      return u === null ? null : { v: u, quoted: true };
    }
    if (/\s#/.test(s) || INDICATORS.indexOf(s.charAt(0)) >= 0) { return null; }
    return resolve(s);
  }

  // Values of the text after "Key:", or null when the form is not in the subset.
  function parseValues(rest) {
    var s = rest.trim();
    if (s === "") { return []; }
    var first = s.charAt(0);
    if (first === "[") {
      if (s.charAt(s.length - 1) !== "]") { return null; }
      var inner = s.slice(1, -1);
      if (inner.trim() === "") { return []; }
      var items = splitFlow(inner);
      if (items === null) { return null; }
      var vals = [];
      for (var i = 0; i < items.length; i++) {
        var r = scalar(items[i]);
        if (r === null) { return null; }
        if (!r.skip) { vals.push(r.v); }
      }
      return vals;
    }
    var one = scalar(s);
    if (one === null) { return null; }
    if (one.skip) { return []; }
    return one.v.split(",").map(function (p) { return p.trim(); });
  }

  function parse(text) {
    var b = bounds(text);
    if (!b.open) { return { ok: false, reason: "missing_frontmatter", props: [] }; }
    if (b.close === null) { return { ok: false, reason: "missing_frontmatter_close", props: [] }; }
    var lines = splitLines(text, b.start, b.end);
    var firstLine = text.slice(0, b.start).split("\n").length - 1;
    var props = [];
    var i = 0;
    while (i < lines.length) {
      var ln = lines[i];
      var m = KEY_RE.exec(ln.text);
      if (!m || /^[ \t]/.test(ln.text)) { i++; continue; }
      var last = i;
      var j = i + 1;
      while (j < lines.length) {
        var t = lines[j].text;
        if (/^\s*(#.*)?$/.test(t)) {
          j++;
        } else if (isContinuation(t)) {
          last = j;
          j++;
        } else {
          break;
        }
      }
      var values = null;
      if (last === i) { values = parseValues(m[2] === undefined ? "" : m[2]); }
      props.push({
        key: m[1].trim(),
        values: values === null ? [] : values,
        complex: values === null,
        line: firstLine + i,
        from: ln.from,
        to: lines[last].to
      });
      i = last + 1;
    }
    return { ok: true, reason: null, props: props };
  }

  // True when the build's loader would not read the plain text as the same string (empty or null).
  function changedByYaml(v) {
    return resolve(v).skip === true;
  }

  // A single value that holds a comma is written unquoted: the form refuses commas (ED-07).
  function quote(value) {
    var v = String(value);
    var needs = v === "" ||
      v !== v.trim() ||
      INDICATORS.indexOf(v.charAt(0)) >= 0 ||
      v === "-" || v.indexOf("- ") === 0 || v.indexOf("? ") === 0 ||
      v.indexOf(": ") >= 0 || v.charAt(v.length - 1) === ":" ||
      v.indexOf(" #") >= 0 ||
      v.charAt(0) === "#" || v.charAt(0) === "," || v === "=" || v === "<<" || v === "?" ||
      v.indexOf("\t") >= 0 ||
      RESERVED_RE.test(v) || changedByYaml(v);
    return needs ? dquote(v) : v;
  }

  function dquote(v) {
    return '"' + String(v).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
  }

  function eolAfter(text, pos) {
    if (text.charAt(pos) === "\r" && text.charAt(pos + 1) === "\n") { return 2; }
    return text.charAt(pos) === "\n" ? 1 : 0;
  }

  function setValues(text, key, values) {
    var result = parse(text);
    if (!result.ok) { return { from: 0, to: 0, insert: "" }; }
    var prop = null;
    for (var i = 0; i < result.props.length; i++) {
      if (result.props[i].key === key) { prop = result.props[i]; }  // the last one wins, as in PyYAML
    }
    var eol = text.indexOf("\r\n") >= 0 ? "\r\n" : "\n";
    if (prop === null) {
      if (values === null) { return { from: 0, to: 0, insert: "" }; }
      var at = bounds(text).end;
      return { from: at, to: at, insert: lineFor(key, values) + eol };
    }
    if (values === null) {
      return { from: prop.from, to: prop.to + eolAfter(text, prop.to), insert: "" };
    }
    return { from: prop.from, to: prop.to, insert: lineFor(key, values) };
  }

  // "Key: a, b" is a plain scalar, and YAML cannot mix quoted and plain parts in one,
  // so when a value of several needs quotes the line is written as a flow list instead.
  function lineFor(key, values) {
    if (!values.length) { return key + ":"; }
    var quoted = values.map(quote);
    var plain = quoted.every(function (q, i) { return q === String(values[i]); });
    if (values.length === 1 || plain) { return key + ": " + quoted.join(", "); }
    return key + ": [" + values.map(quoteForFlow).join(", ") + "]";
  }

  // Python: valid_filename (kb4it/core/files.py). \w is alphanumerics (isalnum) plus "_".
  function validFilename(s) {
    return String(s).trim().replace(/ /g, "_").replace(/[^\p{L}\p{N}_.-]/gu, "").replace(/^\.+/, "");
  }

  // Python: slugify (kb4it/core/util.py).
  function slugify(s) {
    return String(s).normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase()
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  // Python: documents.first_heading. The returned line is relative to the body passed in. Lines split as str.splitlines does.
  function firstHeading(body) {
    var lines = body.split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/);
    if (lines.length && lines[lines.length - 1] === "") { lines.pop(); }
    var fence = null;
    var prevBlank = true;
    var inIndented = false;
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (fence !== null) {
        var stripped = line.trim();
        if (stripped.indexOf(fence) === 0 && stripped.split(fence.charAt(0)).join("") === "") {
          fence = null;
        }
        continue;
      }
      var fm = FENCE_RE.exec(line);
      if (fm) {
        fence = fm[1];
        prevBlank = inIndented = false;
        continue;
      }
      var blank = line.trim() === "";
      if (!blank && /^( {4}|\t)/.test(line) && (prevBlank || inIndented)) {
        inIndented = true;
        prevBlank = false;
        continue;
      }
      if (!blank) { inIndented = false; }
      prevBlank = blank;
      var h = H1_RE.exec(line);
      if (h) { return { title: h[1].trim(), line: i }; }
    }
    return null;
  }

  function fileName(text, category) {
    var b = bounds(text);
    var body = text;
    if (b.open && b.close !== null) { body = text.slice(b.close + 4).replace(/^\n+/, ""); }
    var heading = firstHeading(body);
    var slug = heading ? slugify(heading.title) : "";
    return (slug || category) + ".md";
  }

  // ---- Lint (ED-06) and completion (ED-05) ----

  function lineEnd(text, from) {
    var nl = text.indexOf("\n", from);
    var to = nl < 0 ? text.length : nl;
    if (to > from && text.charAt(to - 1) === "\r") { to -= 1; }
    return to;
  }

  // Index after the closing quote of a quoted scalar starting at s[0], or -1 when unclosed.
  function quoteEnd(s, i) {
    var q = s.charAt(i);
    for (var k = i + 1; k < s.length; k++) {
      var c = s.charAt(k);
      if (q === '"' && c === "\\") { k++; }
      else if (c === q) {
        if (q === "'" && s.charAt(k + 1) === "'") { k++; } else { return k + 1; }
      }
    }
    return -1;
  }

  var ESCAPES = "0abt\tnvfre \"/\\N_LP";

  // First bad escape of a double-quoted scalar s[i..end), as PyYAML scans them, or null.
  function badEscape(s, i, end) {
    for (var k = i + 1; k < end - 1; k++) {
      if (s.charAt(k) !== "\\") { continue; }
      var n = s.charAt(k + 1);
      var width = n === "x" ? 2 : (n === "u" ? 4 : (n === "U" ? 8 : 0));
      if (width) {
        if (!new RegExp("^[0-9a-fA-F]{" + width + "}$").test(s.substr(k + 2, width))) { return "bad escape \\" + n; }
        k += width + 1;
      } else if (ESCAPES.indexOf(n) < 0) {
        return "unsupported escape \\" + n;
      } else {
        k++;
      }
    }
    return null;
  }

  function onlyComment(rest) {
    return rest.trim() === "" || /^\s+#/.test(rest);
  }

  // What the build's YAML loader would reject in a one line value, or null.
  function valueError(raw) {
    var s = raw.trim();
    if (s === "") { return null; }
    var c = s.charAt(0);
    var end;
    if (c === '"' || c === "'") {
      end = quoteEnd(s, 0);
      if (end < 0) { return "unclosed quote"; }
      if (c === '"' && badEscape(s, 0, end)) { return badEscape(s, 0, end); }
      return onlyComment(s.slice(end)) ? null : "text after the closing quote";
    }
    if (c === "[" || c === "{") {
      var stack = [];
      for (var i = 0; i < s.length; i++) {
        var ch = s.charAt(i);
        if (ch === '"' || ch === "'") {
          end = quoteEnd(s, i);
          if (end < 0) { return "unclosed quote"; }
          if (ch === '"' && badEscape(s, i, end)) { return badEscape(s, i, end); }
          i = end - 1;
        } else if (ch === "?") {
          return "a plain item in a flow list cannot contain '?', quote it";
        } else if (ch === "[" || ch === "{") {
          stack.push(ch === "[" ? "]" : "}");
        } else if (ch === "]" || ch === "}") {
          if (stack.pop() !== ch) { return "unbalanced brackets"; }
          if (!stack.length) { return onlyComment(s.slice(i + 1)) ? null : "text after the closing bracket"; }
        }
      }
      return "unclosed bracket";
    }
    if ((c === "|" || c === ">") && !/^[|>][-+0-9]*\s*(#.*)?$/.test(s)) {
      return "text after the block scalar indicator";
    }
    var plain = s.replace(/\s#.*$/, "").trim();
    if (c === "|" || c === ">") { return null; }
    if (plain.charAt(0) === "*") { return "alias without an anchor"; }
    if (plain.charAt(0) === "!" && plain.charAt(1) !== "!") { return "unknown tag"; }
    if (plain.charAt(0) === "%") { return "a plain value cannot start with %"; }
    if (plain === "?" || plain.indexOf("? ") === 0) { return "a plain value cannot start with '? '"; }
    if ("]},".indexOf(plain.charAt(0)) >= 0 && plain !== "") { return "a plain value cannot start with " + plain.charAt(0); }
    if (plain === "=" || plain === "<<") { return "'" + plain + "' is a YAML special value, quote it"; }
    if (plain.indexOf("\t") >= 0) { return "a tab inside a plain value"; }
    if (plain === "-" || plain.indexOf("- ") === 0) { return "a plain value cannot start with '- '"; }
    if (plain.indexOf(": ") >= 0 || plain.charAt(plain.length - 1) === ":") {
      return "a plain value cannot contain ': ', quote it";
    }
    if (plain.charAt(0) === "@" || plain.charAt(0) === "`") { return "a plain value cannot start with " + plain.charAt(0); }
    return null;
  }

  // A key with a plain value on its line followed by an indented line with ': ' is a YAML error.
  function continuationError(text, p, first) {
    var m = KEY_RE.exec(text.slice(p.from, first));
    var v = m && m[2] !== undefined ? m[2].trim() : "";
    if (v === "" || "[{\"'|>".indexOf(v.charAt(0)) >= 0) { return null; }
    var lines = splitLines(text, first + 1, p.to);
    for (var i = 0; i < lines.length; i++) {
      var t = lines[i].text.replace(/(^|\s)#.*$/, "").trim();
      if (t !== "" && (t.indexOf(": ") >= 0 || t.charAt(t.length - 1) === ":")) {
        return { from: lines[i].from, to: lines[i].to, message: "a line continuing a plain value cannot contain ': '" };
      }
    }
    return null;
  }

  function diag(from, to, severity, reason, message) {
    return { from: from, to: to, severity: severity, reason: reason, message: message };
  }

  function has(keys, key) {
    return !!keys && Object.prototype.hasOwnProperty.call(keys, key);
  }

  // Lint mirrors the build line by line. Left to the YAML tree of Task 6: anchors and aliases that are
  // defined (an alias after its anchor is flagged here), nested block mappings, multi-line quoted or
  // flow values, and every other error the full YAML grammar reports.
  function lint(text, keys) {
    var b = bounds(text);
    if (!b.open) {
      return [diag(0, 0, "error", "missing_frontmatter", "The document must start with '---'.")];
    }
    if (b.close === null) {
      return [diag(0, 0, "error", "missing_frontmatter_close", "The frontmatter is not closed with '---'.")];
    }
    var out = [];
    var result = parse(text);
    var lines = splitLines(text, b.start, b.end);
    var covered = [];
    result.props.forEach(function (p) { covered.push([p.from, p.to]); });
    var stray = null;
    lines.forEach(function (ln) {
      if (/^\s*(#.*)?$/.test(ln.text)) { return; }
      var inside = covered.some(function (r) { return ln.from >= r[0] && ln.from <= r[1]; });
      if (!inside && stray === null) { stray = ln; }
    });
    if (!result.props.length && stray !== null) {
      out.push(diag(stray.from, stray.to, "error", "invalid_frontmatter",
        "The frontmatter must be a list of 'Key: value' lines."));
    } else if (stray !== null) {
      out.push(diag(stray.from, stray.to, "error", "yaml_error",
        "This line is not 'Key: value', a continuation, a comment or blank."));
    }
    var seen = {};
    var lastIndex = {};
    result.props.forEach(function (p) { lastIndex[p.key] = p.from; });
    result.props.forEach(function (p) {
      var first = lineEnd(text, p.from);
      var single = first >= p.to;
      if (single) {
        var m = KEY_RE.exec(text.slice(p.from, first));
        var err = m ? valueError(m[2] === undefined ? "" : m[2]) : null;
        if (!err && /^[^:]*:\t/.test(text.slice(p.from, first))) { err = "a tab after the colon"; }
        if (err) {
          out.push(diag(p.from, first, "error", "yaml_error", "YAML error in " + p.key + ": " + err + "."));
          seen[p.key] = true;
          return;
        }
      }
      if (!single) {
        var cerr = continuationError(text, p, first);
        if (cerr) {
          out.push(diag(cerr.from, cerr.to, "error", "yaml_error", "YAML error in " + p.key + ": " + cerr.message + "."));
          seen[p.key] = true;
          return;
        }
      }
      var dup = has(seen, p.key);
      seen[p.key] = true;
      var finalOne = lastIndex[p.key] === p.from;
      if (dup) {
        out.push(diag(p.from, first, "warning", "duplicate_property",
          p.key + " is defined more than once; the build keeps the last one."));
      }
      if (p.key === "Title" || p.key === "title") {
        out.push(diag(p.from, first, "warning", "title_in_frontmatter_ignored",
          "The title comes from the first heading; " + p.key + " in the frontmatter is ignored."));
        return;
      }
      if (!validFilename(p.key)) {
        out.push(diag(p.from, first, "error", "bad_property_name", "'" + p.key + "' cannot be used as a property name."));
        return;
      }
      if (p.complex || !finalOne) { return; }
      var bad = p.values.filter(function (v) { return v && !validFilename(v); });
      if (bad.length) {
        out.push(diag(p.from, first, "error", "bad_property_value",
          "'" + bad[0] + "' cannot be used as a value of " + p.key + "."));
        return;
      }
      if (BLOCKED_KEYS.indexOf(p.key) >= 0) { return; }
      if (!has(keys, p.key)) {
        out.push(diag(p.from, first, "info", "new_property", p.key + " is new in this repository."));
        return;
      }
      var known = keys[p.key].map(function (e) { return e.v; });
      p.values.forEach(function (v) {
        if (v && known.indexOf(v) < 0) {
          out.push(diag(p.from, first, "info", "new_value", "'" + v + "' is a new value for " + p.key + "."));
        }
      });
    });
    var body = text.slice(b.close + 4).replace(/^\n+/, "");
    if (firstHeading(body) === null) {
      out.push(diag(0, 0, "error", "missing_h1_title", "The document needs a '# ' heading outside code."));
    }
    out.sort(function (a, c) { return a.from - c.from; });
    return out;
  }

  // Keys the build never offers as values (self.keys["blocked"] in kb4it/services/database.py),
  // so they are never in the known keys and must not be reported as new.
  var BLOCKED_KEYS = ["Title", "SystemPage", "Date"];

  function count(n, one, many) { return n + " " + (n === 1 ? one : many); }

  // Inside a flow list "[a, b]" PyYAML rejects a plain item with a question mark, a colon, a hash, a comma,
  // brackets or braces, so any such value is double-quoted; otherwise quote() rules.
  function quoteForFlow(v) {
    return /[?:#,\[\]{}]/.test(v) ? dquote(v) : quote(v);
  }

  // An existing plain list item moved into a flow list: quoted as needed there.
  function flowItem(raw) {
    var c = raw.charAt(0);
    if (c === '"' || c === "'") { return raw; }
    return /[?:#,\[\]{}]/.test(raw) ? dquote(raw) : raw;
  }

  // Index of the "#" that starts a trailing comment (after whitespace, outside quotes), or -1.
  function commentStart(s) {
    var q = null;
    for (var i = 0; i < s.length; i++) {
      var c = s.charAt(i);
      if (q) {
        if (q === '"' && c === "\\") { i++; }
        else if (c === q) { q = null; }
      } else if ((c === '"' || c === "'") && /(^|[,\[])\s*$/.test(s.slice(0, i))) {
        q = c;
      } else if (c === "#" && i > 0 && /\s/.test(s.charAt(i - 1))) {
        return i;
      }
    }
    return -1;
  }

  // Frontmatter extent for the cursor: while the closing fence is missing it runs to the end.
  function completeRegion(text) {
    var b = bounds(text);
    if (!b.open) { return null; }
    var off = text.charCodeAt(0) === 0xFEFF ? 1 : 0;
    var nl = text.indexOf("\n", off + 3);
    if (nl < 0) { return null; }
    return { start: nl + 1, end: b.close === null ? text.length : b.close };
  }

  // Option shape: {label, insert, detail, from?, to?}. Without from/to the option replaces
  // [result.from, cursor] with insert. With them it replaces [from, to] instead; this is used to rewrite
  // a whole plain comma list as a flow list when a value that needs quoting joins other items,
  // because the build reads quotes inside a plain list as part of the value.
  function complete(text, pos, keys) {
    var region = completeRegion(text);
    if (region === null || pos < region.start || pos > region.end) { return null; }
    var lineStart = text.lastIndexOf("\n", pos - 1) + 1;
    var prefix = text.slice(lineStart, pos);
    if (prefix.charAt(prefix.length - 1) === "\r") { return null; }
    if (/^[ \t]/.test(prefix) || /^(-([ \t]|$)|#)/.test(prefix)) { return null; }
    var lineTo = lineEnd(text, lineStart);
    var m = /^([^\s#:][^:]*?):([ \t]*)(.*)$/.exec(prefix);
    if (!m) {
      if (prefix.indexOf(":") >= 0) { return null; }
      var present = {};
      splitLines(text, region.start, Math.min(region.end, text.length)).forEach(function (ln) {
        if (ln.from === lineStart) { return; }
        var km = KEY_RE.exec(ln.text);
        if (km && !/^[ \t]/.test(ln.text)) { present[km[1].trim()] = true; }
      });
      var names = Object.keys(keys || {}).filter(function (k) {
        return k !== "Title" && k !== "title" && !present[k];
      });
      return {
        from: lineStart,
        options: names.map(function (k) {
          return { label: k, insert: k + ": ", detail: count(keys[k].length, "value", "values") };
        })
      };
    }
    var key = m[1].trim();
    if (!has(keys, key)) { return null; }
    var valueFrom = lineStart + prefix.length - m[3].length;
    var valueTo = lineTo;
    var whole = text.slice(valueFrom, valueTo);
    var ci = commentStart(whole);
    var comment = ci >= 0 ? whole.slice(ci) : "";
    var rest = ci >= 0 ? whole.slice(0, ci) : whole;
    var cursor = Math.min(m[3].length, rest.length);
    // Items of the value with their offsets inside rest; the one holding the cursor is being typed.
    var items = [];
    var at = 0;
    rest.split(",").forEach(function (part) {
      items.push({ from: at, to: at + part.length, text: part });
      at += part.length + 1;
    });
    var current = items[items.length - 1];
    for (var i = 0; i < items.length; i++) {
      if (cursor <= items[i].to) { current = items[i]; break; }
    }
    var flow = rest.trim().charAt(0) === "[";
    var existing = {};
    items.forEach(function (it) {
      if (it === current) { return; }
      var r = scalar(it.text.replace(/^\s*\[/, "").replace(/\]\s*$/, ""));
      if (r && !r.skip) { existing[r.v] = true; }
    });
    var head = current.text.slice(0, Math.max(0, Math.min(cursor, current.to) - current.from));
    var lead = head.length - head.replace(/^[\s\[]+/, "").length;
    var from = valueFrom + current.from + lead;
    var pad = "";
    if (m[2] === "" && current === items[0] && !flow) { pad = " "; }
    var others = items.filter(function (it) {
      return it !== current && it.text.replace(/^\s*\[|\]\s*$/g, "").trim() !== "";
    });
    var list = keys[key].filter(function (e) { return !existing[e.v]; })
      .map(function (e, idx) { return { e: e, idx: idx }; })
      .sort(function (a, c) { return (c.e.c - a.e.c) || (a.idx - c.idx); });
    return {
      from: from,
      options: list.map(function (x) {
        var v = x.e.v;
        if (!flow && others.length && quote(v) !== v) {
          var parts = [];
          items.forEach(function (it) {
            var raw = it.text.trim();
            if (it === current) {
              parts.push(quoteForFlow(v));
              // text after the cursor in this item is an existing value: keep it
              var tail = it.text.slice(cursor - it.from).trim();
              if (cursor < it.to && tail !== "") { parts.push(flowItem(tail)); }
            } else if (raw !== "") { parts.push(flowItem(raw)); }
          });
          return {
            label: v,
            insert: (m[2] === "" ? " " : "") + "[" + parts.join(", ") + "]" + (comment ? " " + comment : ""),
            detail: count(x.e.c, "document", "documents"),
            from: valueFrom,
            to: valueTo
          };
        }
        return {
          label: v,
          insert: pad + (flow ? quoteForFlow(v) : quote(v)),
          detail: count(x.e.c, "document", "documents")
        };
      })
    };
  }

  return {
    bounds: bounds,
    parse: parse,
    setValues: setValues,
    quote: quote,
    validFilename: validFilename,
    slugify: slugify,
    firstHeading: firstHeading,
    fileName: fileName,
    lint: lint,
    complete: complete
  };
})();
