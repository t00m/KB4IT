"""Rewrite the content blocks of a document body.

Code blocks get a bar with a language label and a copy button; a block over
LONG_CODE_LINES lines is folded to FOLDED_CODE_LINES and gets a "Show all"
button. Tables get the UIkit table style and are wrapped so wide ones
scroll sideways and long ones keep their header; a long table with a plain
grid (one header row, no merged cells) is also marked for search and sort.
Author tabs from pymdownx.tabbed get a print-only label inside each panel,
because the tab bar is not printed.

The function runs on the HTML produced by the compiler, so the markup it
creates is plain HTML that the browser can use without JavaScript: the copy
and fold buttons, the back-to-top link and the table search are switched on
by blocks.js.
"""

from html import escape

from lxml import etree
from lxml import html as lhtml

LONG_CODE_LINES = 30
FOLDED_CODE_LINES = 20
STICKY_TABLE_ROWS = 15

# UIkit classes every table of a body gets.
TABLE_CLASSES = "uk-table uk-table-small uk-table-divider uk-table-hover uk-table-striped"

# The class of the theme's document lists (all documents, bookmarks, property pages), set up by the page header.
DATATABLE_CLASS = "kb4it-datatable"


def enhance_blocks(html, table_filter=True):
    """Wrap the code blocks and tables of a body and label the panels of author tabs.

    With table_filter, tables over STICKY_TABLE_ROWS rows that DataTables can read get search and sort.
    """
    if "<pre" not in html and "<table" not in html and "tabbed-set" not in html:
        return html
    root = lhtml.fragment_fromstring(html, create_parent="div")
    changed = False
    for pre in list(root.iter("pre")):
        changed = _code_block(pre) or changed
    for table in list(root.iter("table")):
        changed = _table(table, table_filter) or changed
    changed = _tab_labels(root) or changed
    if not changed:
        return html
    out = escape(root.text, quote=False) if root.text else ""
    return out + "".join(lhtml.tostring(child, encoding="unicode") for child in root)


def _code_block(pre):
    if _has_class(pre, "mermaid") or _has_ancestor_class(pre, "kb-code"):
        return False
    code = next((child for child in pre if child.tag == "code"), None)
    language = _language(pre, code)
    lines = _line_count(pre.text_content())
    wrapper = etree.Element("div")
    wrapper.set("class", "kb-code kb-code-long" if lines > LONG_CODE_LINES else "kb-code")
    bar = etree.SubElement(wrapper, "div")
    bar.set("class", "kb-code-bar")
    if language:
        label = etree.SubElement(bar, "span")
        label.set("class", "kb-code-lang")
        label.text = language
    copy = etree.SubElement(bar, "button")
    copy.set("type", "button")
    copy.set("class", "kb-code-copy kb-noprint")
    copy.set("aria-label", "Copy code")
    icon = etree.SubElement(copy, "span")
    icon.set("data-uk-icon", "icon: copy")
    icon.set("aria-hidden", "true")
    text = etree.SubElement(copy, "span")
    text.set("class", "kb-code-copy-text")
    text.text = "Copy"
    _wrap(pre, wrapper)
    if lines > LONG_CODE_LINES:
        show = etree.SubElement(wrapper, "button")
        show.set("type", "button")
        show.set("class", "kb-code-show kb-noprint")
        show.set("data-lines", str(lines))
        show.text = f"Show all {lines} lines"
    return True


def _table(table, table_filter=True):
    if _has_ancestor_class(table, "kb-table"):
        return False
    rows = len(table.xpath("./tbody/tr")) or max(len(table.xpath("./tr")) - 1, 0)
    # A document list of the theme is a DataTable already, started by the page header; it keeps its classes.
    listing = _has_class(table, DATATABLE_CLASS)
    names = (table.get("class") or "").split()
    if not listing:
        table.set("class", " ".join(names + [n for n in TABLE_CLASSES.split() if n not in names]))
    classes = ["kb-table", "uk-overflow-auto"]
    if rows > STICKY_TABLE_ROWS:
        classes.append("kb-table-sticky")
        if table_filter and not listing and _plain_grid(table):
            classes.append("kb-table-filter")
    wrapper = etree.Element("div")
    wrapper.set("class", " ".join(classes))
    _wrap(table, wrapper)
    return True


def _plain_grid(table):
    """True when DataTables can read the table: one header row, no merged cells, no nested table, full rows."""
    head = table.xpath("./thead/tr")
    body = table.xpath("./tbody/tr")
    if len(head) != 1 or not body or table.xpath(".//table") or table.xpath(".//*[@rowspan or @colspan]"):
        return False
    width = len(head[0].xpath("./th|./td"))
    return width > 0 and all(len(row.xpath("./th|./td")) == width for row in body)


def _tab_labels(root):
    changed = False
    for tabset in root.iter():
        if not _has_class(tabset, "tabbed-set"):
            continue
        labels_box = _child_with_class(tabset, "tabbed-labels")
        content_box = _child_with_class(tabset, "tabbed-content")
        if labels_box is None or content_box is None:
            continue
        labels = [child for child in labels_box if child.tag == "label"]
        panels = [child for child in content_box if _has_class(child, "tabbed-block")]
        if len(labels) != len(panels):
            continue
        for label, panel in zip(labels, panels):
            if any(_has_class(child, "kb-tab-print") for child in panel):
                continue
            caption = etree.Element("p")
            caption.set("class", "kb-tab-print")
            caption.text = (label.text_content() or "").strip()
            panel.insert(0, caption)
            changed = True
    return changed


def _child_with_class(element, name):
    return next((child for child in element if _has_class(child, name)), None)


def _language(pre, code):
    for element in (code, pre):
        language = _class_language(element)
        if language:
            return language
    for element in pre.iterancestors():
        language = _class_language(element)
        if language:
            return language
    return ""


def _class_language(element):
    if element is None:
        return ""
    for name in (element.get("class") or "").split():
        if name.startswith("language-") and len(name) > len("language-"):
            return name[len("language-"):]
    return ""


def _line_count(text):
    text = text.rstrip("\n")
    return len(text.split("\n")) if text else 0


def _has_class(element, name):
    return name in (element.get("class") or "").split()


def _has_ancestor_class(element, name):
    return any(_has_class(ancestor, name) for ancestor in element.iterancestors())


def _wrap(node, wrapper):
    """Put wrapper where node was, keeping the text that followed it."""
    parent = node.getparent()
    index = parent.index(node)
    tail = node.tail
    node.tail = None
    parent.remove(node)
    wrapper.append(node)
    wrapper.tail = tail
    parent.insert(index, wrapper)
