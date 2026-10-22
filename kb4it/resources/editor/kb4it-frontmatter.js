/* KB4IT frontmatter parser, quoting and name rules (ED-06, ED-08, ED-10).
 * No DOM code. Mirrors kb4it/core/documents.py and the name rules of
 * kb4it/core/files.py and kb4it/core/util.py. */
var KB4ITFrontmatter = (function () {
  "use strict";

  var FENCE_RE = /^ {0,3}(`{3,}|~{3,})/;
  var H1_RE = /^#[ \t]+(\S.*?)[ \t]*$/;
  var KEY_RE = /^(?!-[ \t])([^\s#:][^:]*?):(?:[ \t]+(.*))?$/;
  var NUMBER_RE = /^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/;
  var RESERVED_RE = /^(true|false|yes|no|null|on|off|~)$/i;
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
  var TRUES = ["true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"];
  var FALSES = ["false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"];
  var INT_RE = /^(0|-?[1-9][0-9]*)$/;
  var DATE_RE = /^\d{4}-\d\d?-\d\d?$/;
  var NUMERIC_RE = [
    /^[-+]?(0[xob][0-9a-fA-F_]+|([0-9_]+\.?[0-9_]*|\.[0-9_]+)([eE][-+]?[0-9]+)?)$/,
    /^[-+]?[0-9][0-9_]*(:[0-5]?[0-9])+(\.[0-9_]*)?$/,
    /^[-+]?\.(inf|Inf|INF)$|^\.(nan|NaN|NAN)$/,
    /^\d{4}-\d\d?-\d\d?([Tt]|[ \t]+)\d\d?:\d\d/
  ];

  // How yaml.safe_load reads a plain scalar, as the build then sees it: {v: text},
  // {skip: true} for null, or null when the text is a number or timestamp that the
  // build would turn into something else (the property is then complex).
  function resolve(s) {
    if (s === "" || NULLS.indexOf(s) >= 0) { return { skip: true }; }
    if (TRUES.indexOf(s) >= 0) { return { v: "True" }; }
    if (FALSES.indexOf(s) >= 0) { return { v: "False" }; }
    if (INT_RE.test(s) || DATE_RE.test(s)) { return { v: s }; }
    for (var i = 0; i < NUMERIC_RE.length; i++) {
      if (NUMERIC_RE[i].test(s) && /[0-9.]/.test(s)) { return null; }
    }
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

  // A single value that holds a comma is written unquoted: the form refuses commas (ED-07).
  function quote(value) {
    var v = String(value);
    var needs = v === "" ||
      v !== v.trim() ||
      INDICATORS.indexOf(v.charAt(0)) >= 0 ||
      v === "-" || v.indexOf("- ") === 0 || v.indexOf("? ") === 0 ||
      v.indexOf(": ") >= 0 || v.charAt(v.length - 1) === ":" ||
      v.indexOf(" #") >= 0 ||
      RESERVED_RE.test(v) || NUMBER_RE.test(v);
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
      if (result.props[i].key === key) { prop = result.props[i]; break; }
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
    var items = values.map(function (v) {
      return /[\[\]{}]/.test(v) ? dquote(v) : quote(v);
    });
    return key + ": [" + items.join(", ") + "]";
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

  return {
    bounds: bounds,
    parse: parse,
    setValues: setValues,
    quote: quote,
    validFilename: validFilename,
    slugify: slugify,
    firstHeading: firstHeading,
    fileName: fileName
  };
})();
