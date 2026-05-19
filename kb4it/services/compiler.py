#!/usr/bin/env python

"""
Service Compiler.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Markdown-to-HTML compiler service
"""

import os
import re
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor as Executor

import markdown as _markdown_lib

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import (get_default_workers, get_source_docs,
                              html_id_for, source_ext)

# Optional TUI callbacks set by kb4it.tui.app before a build, cleared after.
# _progress_callback: called per document,  signature: (basename: str, rc: bool)
# _compile_start_callback: called once with the total doc count,  (total: int)
_progress_callback = None
_compile_start_callback = None


def set_progress_callback(callback) -> None:
    """Register a per-document TUI progress callback."""
    global _progress_callback
    _progress_callback = callback


def clear_progress_callback() -> None:
    """Remove the per-document TUI progress callback."""
    global _progress_callback
    _progress_callback = None


def set_compile_start_callback(callback) -> None:
    """Register a callback invoked with the actual number of docs to compile."""
    global _compile_start_callback
    _compile_start_callback = callback


def clear_compile_start_callback() -> None:
    """Remove the compile-start callback."""
    global _compile_start_callback
    _compile_start_callback = None


class Compiler(Service):
    """KB4IT Compiler Service."""

    def _initialize(self):
        """Initialize compiler service."""
        self.srvbes = self.app.get_service("Backend")
        self.srvthm = self.get_service("Theme")
        self.srvprc = self.get_service("Processor")

    def execute(self):
        """Compile Markdown documents to HTML."""
        self.log.debug("[COMPILER] START")

        # copy online resources to target path
        resources_dir_tmp = os.path.join(self.srvbes.get_path("tmp"), "resources")

        # if path already exists, remove it before copying with copytree()
        if os.path.exists(resources_dir_tmp):
            shutil.rmtree(resources_dir_tmp)
            shutil.copytree(ENV["GPATH"]["RESOURCES"], resources_dir_tmp)
        self.log.debug("[COMPILER] RESOURCES_COPIED")

        distributed = self.srvbes.get_value("docs", "targets")
        targets_count = len(distributed) if distributed else 0
        self.log.debug(f"[COMPILER] TARGETS count={targets_count}")
        max_workers = self.srvbes.get_value("repo", "workers")
        if max_workers is None:
            max_workers = get_default_workers()
        self.log.debug(f"[COMPILER] WORKERS n={max_workers}")
        with Executor(max_workers=max_workers) as exe:
            docs = sorted(get_source_docs(self.srvbes.get_path("tmp")))
            if _compile_start_callback is not None:
                try:
                    _compile_start_callback(len(docs))
                except Exception as err:
                    self.log.debug(f"[COMPILER] CALLBACK_ERROR stage=start err={err}")
            jobs = []
            num = 1
            tmp_dir = self.srvbes.get_path("tmp")

            for doc in docs:
                basename = os.path.basename(doc)
                fmt = source_ext(basename)
                data = {
                    "doc": doc,
                    "format": fmt,
                    "tmp_dir": tmp_dir,
                    "num": num,
                }
                self.log.debug(f"[COMPILER] QUEUE doc={basename} format={fmt}")
                job = exe.submit(self._compile_md, data)
                job.add_done_callback(self.compilation_finished)
                jobs.append(job)
                num += 1

            if num - 1 > 0:
                self.log.debug("[COMPILER] COMPILATION_START")
                for job in jobs:
                    job.result()
                self.log.debug(f"[COMPILER] COMPILED n={num - 1}")
            else:
                self.log.debug("[COMPILER] NOTHING_TO_COMPILE")
            self.log.debug("[COMPILER] END")

    def _compile_md(self, data):
        """Compile a Markdown file in-process via python-markdown.

        Files tagged by Builder.distribute_md() with the theme-html sentinel
        contain pre-rendered HTML and are passed through verbatim,  section
        restructuring would corrupt their UIKit layout.
        """
        doc = data["doc"]
        num = data["num"]
        tmp_dir = data["tmp_dir"]
        try:
            with open(doc, "r", encoding="utf-8") as fh:
                text = fh.read()
            out_path = os.path.join(tmp_dir, html_id_for(os.path.basename(doc)))

            if text.startswith("<!-- kb4it:theme-html -->"):
                _, _, html_fragment = text.partition("-->")
                with open(out_path, "w", encoding="utf-8") as fh:
                    fh.write(html_fragment.lstrip("\n"))
                return doc, True, num

            # Strip YAML frontmatter
            if text.startswith("---"):
                end = text.find("\n---", 3)
                if end >= 0:
                    text = text[end + 4:].lstrip("\n")
            # Strip the first H1 heading,  the title is already shown in the page header
            text = re.sub(r"^#\s+[^\n]+\n?", "", text, count=1)
            md = _markdown_lib.Markdown(
                extensions=["extra", "admonition", "toc", "sane_lists"],
            )
            html_fragment = md.convert(text)
            # Inject a TOC block so extract_toc() can populate the Contents nav menu.
            toc_block = _md_toc_block(md.toc)
            if toc_block:
                html_fragment = toc_block + '\n' + html_fragment
            # Restructure flat headings into sect1/sectionbody divs so the
            # transformation pipeline produces the UIKit accordion layout.
            html_fragment = _restructure_md_sections(html_fragment)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(html_fragment)
            return doc, True, num
        except Exception as err:
            self.log.error(f"[COMPILER] MD_COMPILE_FAIL doc={os.path.basename(doc)} error={err}")
            return doc, False, num

    def compilation_finished(self, future):
        """Once compiled, build page."""
        cur_thread = threading.current_thread().name
        x = future.result()
        if cur_thread != x:
            path_hdoc, rc, num = x
            basename = os.path.basename(path_hdoc)
            self.log.info(f"[COMPILER] COMPILED doc={basename} rc={rc}")
            if _progress_callback is not None:
                try:
                    _progress_callback(basename, rc)
                except Exception as err:
                    self.log.debug(f"[COMPILER] CALLBACK_ERROR stage=progress err={err}")
            if rc is True:
                try:
                    self.srvthm.build_page(path_hdoc)
                except MemoryError:
                    self.log.error("[COMPILER] MEMORY_EXHAUSTED")
                    self.log.error("[COMPILER] HINT use fewer workers or add memory")
                except Exception as error:
                    self.log.error(f"[COMPILER] ERROR {error}")
                    self.print_traceback()
                return x
            else:
                self.log.error(f"[COMPILER] COMPILE_FAILED doc={basename}")
                return x


def _md_toc_block(toc_html: str) -> str:
    """Convert python-markdown TOC HTML to KB4IT's expected sectlevel format.

    python-markdown emits plain <ul> nesting; extract_toc() expects sectlevel1/2/3/4
    class names and a <div id="toctitle"> marker to locate the TOC block.
    """
    if not toc_html or '<li>' not in toc_html:
        return ''
    depth = 0
    result = []
    for line in toc_html.split('\n'):
        s = line.strip()
        if s == '<div class="toc">':
            result.append('<div id="toc" class="toc">')
            result.append('<div id="toctitle">Contents</div>')
        elif s == '<ul>':
            depth += 1
            indent = line[: len(line) - len(line.lstrip())]
            result.append(f'{indent}<ul class="sectlevel{depth}">')
        elif s == '</ul>':
            result.append(line)
            depth = max(0, depth - 1)
        else:
            result.append(line)
    return '\n'.join(result)


def _restructure_md_sections(html: str) -> str:
    """Wrap h2/h3/h4 headings in sect1/sect2/sect3 + sectionbody divs.

    Produces the same nested structure expected by the transformation pipeline,
    so UIKit accordion classes can be applied uniformly.
    """
    _LEVEL_CLASS = {2: "sect1", 3: "sect2", 4: "sect3", 5: "sect4"}

    # Split right before each h2–h5 opening tag
    chunks = re.split(r"(?=<h[2-5][ >])", html)

    if len(chunks) <= 1:
        return html

    result = []
    # Content before the first heading goes in as-is
    if chunks[0]:
        result.append(chunks[0])

    stack: list[int] = []  # stack of currently open heading levels

    for chunk in chunks[1:]:
        m = re.match(r"<(h([2-5]))", chunk)
        if not m:
            result.append(chunk)
            continue

        level = int(m.group(2))
        sect_class = _LEVEL_CLASS.get(level, f"sect{level - 1}")

        # Close all open sections at same level or deeper
        while stack and stack[-1] >= level:
            result.append("</div></div>")  # close sectionbody + sect div
            stack.pop()

        # Extract the heading tag and the following content
        heading_m = re.match(r"(<h\d[^>]*>.*?</h\d>)(.*)", chunk, re.DOTALL)
        if heading_m:
            heading_tag = heading_m.group(1)
            content = heading_m.group(2)
        else:
            result.append(chunk)
            continue

        result.append(f'<div class="{sect_class}">{heading_tag}'
                      f'<div class="sectionbody">{content}')
        stack.append(level)

    # Close any still-open sections
    while stack:
        result.append("</div></div>")
        stack.pop()

    return "".join(result)
