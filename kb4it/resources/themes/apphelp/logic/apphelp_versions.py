"""AppHelp versions: each version in its own folder, a latest/ copy and versions.json at the site root."""

import json
import os
import re
import shutil

MARKER = ".kb4it-version"


def version_key(label):
    """Sort key that orders 0.10 after 0.9."""
    return [(0, int(part), "") if part.isdigit() else (1, 0, part) for part in re.split(r"[.\-_]", label)]


def find_versions(site_root) -> list:
    """Labels of the version folders in site_root (folders holding the marker file), newest first."""
    found = []
    for name in os.listdir(site_root):
        if name != "latest" and os.path.isfile(os.path.join(site_root, name, MARKER)):
            found.append(name)
    return sorted(found, key=version_key, reverse=True)


def pages_of(folder) -> list:
    return sorted(name for name in os.listdir(folder) if name.endswith(".html"))


def publish(site_root, current, latest_wanted=""):
    """Mark the current version, refresh latest/, and write versions.json/.js, index.html and helpids.js at the root."""
    with open(os.path.join(site_root, current, MARKER), "w", encoding="utf-8") as fh:
        fh.write(current + "\n")
    labels = find_versions(site_root)
    latest = latest_wanted if latest_wanted in labels else labels[0]
    latest_dir = os.path.join(site_root, "latest")
    if os.path.isdir(latest_dir):
        shutil.rmtree(latest_dir)
    shutil.copytree(os.path.join(site_root, latest), latest_dir)
    os.unlink(os.path.join(latest_dir, MARKER))
    data = {"latest": latest,
            "versions": [{"label": label, "path": label, "pages": pages_of(os.path.join(site_root, label))}
                         for label in labels]}
    payload = json.dumps(data, ensure_ascii=False, indent=1)
    _write(site_root, "versions.json", payload + "\n")
    _write(site_root, "versions.js", f"window.APPHELP_VERSIONS = {payload};\n")
    _write(site_root, "index.html", _redirect("latest/index.html"))
    _write(site_root, ".nojekyll", "")
    helpids = os.path.join(latest_dir, "helpids.js")
    if os.path.isfile(helpids):
        with open(helpids, encoding="utf-8") as fh:
            text = fh.read()
        mapping = json.loads(text.split("=", 1)[1].strip().rstrip(";"))
        prefixed = {ident: f"latest/{url}" for ident, url in mapping.items()}
        _write(site_root, "helpids.js",
               "window.APPHELP_HELPIDS = " + json.dumps(prefixed, ensure_ascii=False, sort_keys=True) + ";\n")
    return labels, latest


def _redirect(url):
    return ("<!doctype html>\n<html><head><meta charset=\"utf-8\">"
            f"<meta http-equiv=\"refresh\" content=\"0; url={url}\"><title>Help</title>"
            f"<script>location.replace(\"{url}\" + location.search + location.hash);</script></head>"
            f"<body><a href=\"{url}\">Open the help</a></body></html>\n")


def _write(folder, name, text):
    with open(os.path.join(folder, name), "w", encoding="utf-8") as fh:
        fh.write(text)
