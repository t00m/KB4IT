"""Turn the compiled Markdown fragment of a page into AppHelp article HTML."""

import html as htmllib

import lxml.html
from lxml import etree


def _inner_html(element) -> str:
    parts = [htmllib.escape(element.text or "", quote=False)]
    parts += [lxml.html.tostring(child, encoding="unicode") for child in element]
    return "".join(parts)


def _drop(element):
    """Remove an element but keep the text that follows it."""
    parent = element.getparent()
    if element.tail:
        previous = element.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or "") + element.tail
        else:
            parent.text = (parent.text or "") + element.tail
    parent.remove(element)


def _move_children(source, dest):
    dest.text = source.text
    for child in list(source):
        dest.append(child)


def _wrap_code(pre):
    box = lxml.html.Element("div", {"class": "ah-code"})
    tail, pre.tail = pre.tail, None
    pre.addprevious(box)
    box.tail = tail
    button = lxml.html.Element("button", {"class": "ah-copy", "type": "button"})
    button.text = "Copy"
    box.append(button)
    box.append(pre)


def _faq(root):
    for sect in root.xpath('./div[@class="sect1"]'):
        heading = sect.find("h2")
        if heading is None:
            continue
        details = lxml.html.Element("details", {"class": "ah-faq"})
        if heading.get("id"):
            details.set("id", heading.get("id"))
        summary = etree.SubElement(details, "summary")
        _move_children(heading, summary)
        answer = etree.SubElement(details, "div", {"class": "ah-faq-answer"})
        body = sect.find('div[@class="sectionbody"]')
        if body is not None:
            _move_children(body, answer)
        tail = sect.tail
        sect.getparent().replace(sect, details)
        details.tail = tail


def _troubleshooting(root, labels):
    cause = labels.get("ts_cause", "Cause").lower()
    fix = labels.get("ts_fix", "Fix").lower()
    for h3 in root.iter("h3"):
        text = h3.text_content().strip().lower()
        if text.startswith(cause):
            h3.set("class", "ah-cause")
        elif text.startswith(fix):
            h3.set("class", "ah-fix")


def _tutorial(root):
    first = next((child for child in root if isinstance(child.tag, str)), None)
    if first is not None and first.tag == "div":
        classes = (first.get("class") or "").split()
        if "admonition" in classes and "note" in classes:
            first.set("class", " ".join(classes + ["ah-prereq"]))


def _toc(root, layout):
    if layout == "faq":
        return [{"level": 2, "id": d.get("id"), "text": d.find("summary").text_content().strip()}
                for d in root.xpath("./details[@id]")]
    return [{"level": int(h.tag[1]), "id": h.get("id"), "text": h.text_content().strip()}
            for h in root.iter("h2", "h3") if h.get("id")]


def transform(fragment: str, doctype: str, layout: str = "", labels: dict | None = None) -> tuple:
    """Return the article HTML and its table of contents for a page of the given type and layout."""
    if not fragment.strip():
        return "", []
    root = lxml.html.fragment_fromstring(fragment, create_parent="div")
    for toc in root.xpath('.//div[@id="toc"]'):
        _drop(toc)
    for img in root.iter("img"):
        img.set("loading", "lazy")
    for pre in list(root.iter("pre")):
        _wrap_code(pre)
    if layout == "faq":
        _faq(root)
    elif layout == "troubleshooting":
        _troubleshooting(root, labels or {})
    if doctype == "tutorial":
        _tutorial(root)
    toc = _toc(root, layout)
    return _inner_html(root).strip(), toc
