#!/usr/bin/env python

"""
Service Compiler.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Cleaner service
"""

import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor as Executor

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import exec_cmd, get_default_workers, get_source_docs

# Optional TUI progress callback: set by kb4it.tui.app before a build,
# cleared after. Signature: callback(basename: str, rc: bool) -> None.
_progress_callback = None


def set_progress_callback(callback) -> None:
    """Register a TUI progress callback for compilation events."""
    global _progress_callback
    _progress_callback = callback


def clear_progress_callback() -> None:
    """Remove the TUI progress callback."""
    global _progress_callback
    _progress_callback = None


class Compiler(Service):
    """KB4IT Compiler Service."""

    def _initialize(self):
        """Initialize compiler service."""
        self.srvbes = self.app.get_service("Backend")
        self.srvthm = self.get_service("Theme")
        self.srvprc = self.get_service("Processor")

    def execute(self):
        """Compile documents to html with asciidoctor."""
        self.log.debug("[COMPILER] START")
        runtime = self.srvbes.get_dict("runtime")

        # copy online resources to target path
        resources_dir_tmp = os.path.join(self.srvbes.get_path("tmp"), "resources")

        # if path already exists, remove it before copying with copytree()
        if os.path.exists(resources_dir_tmp):
            shutil.rmtree(resources_dir_tmp)
            shutil.copytree(ENV["GPATH"]["RESOURCES"], resources_dir_tmp)
        self.log.debug("[COMPILER] RESOURCES_COPIED")

        adocprops = ""
        for prop in sorted(ENV["CONF"]["ADOCPROPS"]):
            self.log.debug(f"[COMPILER] ADOCPROP name={prop} value={ENV['CONF']['ADOCPROPS'][prop]}")
            if ENV["CONF"]["ADOCPROPS"][prop] is not None:
                if "%s" in ENV["CONF"]["ADOCPROPS"][prop]:
                    adocprops += f"-a {prop}={ENV['CONF']['ADOCPROPS'][prop] % self.srvbes.get_path('target')} "
                else:
                    adocprops += f"-a {prop}={ENV['CONF']['ADOCPROPS'][prop]} "
            else:
                adocprops += f"-a {prop} "
        runtime["adocprops"] = adocprops

        distributed = self.srvbes.get_value("docs", "targets")
        targets_count = len(distributed) if distributed else 0
        self.log.debug(f"[COMPILER] TARGETS count={targets_count}")
        max_workers = self.srvbes.get_value("repo", "workers")
        if max_workers is None:
            max_workers = get_default_workers()
        self.log.debug(f"[COMPILER] WORKERS n={max_workers}")
        with Executor(max_workers=max_workers) as exe:
            docs = sorted(get_source_docs(self.srvbes.get_path("tmp")))
            jobs = []
            num = 1

            kbdict_new = self.srvprc.get_kb_dict()
            for doc in docs:
                basename = os.path.basename(doc)
                cmd = f"asciidoctor -q -s {adocprops} -b html5 -D {self.srvbes.get_path('tmp')} {doc}"
                data = (doc, cmd, num)
                self.log.debug(f"[COMPILER] QUEUE doc={basename}")
                job = exe.submit(self.compilation_started, data)
                job.add_done_callback(self.compilation_finished)
                jobs.append(job)
                num = num + 1

            if num - 1 > 0:
                self.log.debug("[COMPILER] COMPILATION_START")
                for job in jobs:
                    job.result()
                self.log.debug(f"[COMPILER] COMPILED n={num - 1}")
            else:
                self.log.debug("[COMPILER] NOTHING_TO_COMPILE")
            self.log.debug("[COMPILER] END")

    def compilation_started(self, data):
        """Execute compilation."""
        res = exec_cmd(data)
        return res

    def compilation_finished(self, future):
        """Once compiled, build page."""
        cur_thread = threading.current_thread().name
        x = future.result()
        if cur_thread != x:
            path_hdoc, rc, num = x
            basename = os.path.basename(path_hdoc)
            self.log.info(f"[COMPILER] ASCIIDOCTOR doc={basename} rc={rc}")
            if _progress_callback is not None:
                try:
                    _progress_callback(basename, rc)
                except Exception:
                    pass
            if rc is True:
                try:
                    self.srvthm.build_page(path_hdoc)
                except MemoryError:
                    self.log.error("[COMPILER] MEMORY_EXHAUSTED")
                    self.log.error("[COMPILER] HINT use fewer workers or add memory")
                    self.log.error("[COMPILER] EXIT")
                    self.app.stop()
                except Exception as error:
                    self.log.error(f"[COMPILER] ERROR {error}")
                    self.print_traceback()
                    self.app.stop()
                return x
            else:
                self.app.stop()

