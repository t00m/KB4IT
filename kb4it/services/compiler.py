#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Cleaner service
"""

import datetime
import os
import random
import shutil
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor as Executor


from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import exec_cmd
from kb4it.core.util import get_default_workers
from kb4it.core.util import get_hash_from_file
from kb4it.core.util import get_source_docs


class Compiler(Service):
    """KB4IT Compiler Service"""

    def _initialize(self):
        """Initialize compiler service"""
        self.srvbes = self.app.get_service('Backend')
        self.srvthm = self.get_service('Theme')

    def execute(self):
        """Compile documents to html with asciidoctor."""
        self.log.debug(f"[COMPILER] - START")
        runtime = self.srvbes.get_dict('runtime')
        dcomps = datetime.datetime.now()

        # copy online resources to target path
        # ~ resources_dir_source = GPATH['THEMES']
        resources_dir_tmp = os.path.join(self.srvbes.get_path('tmp'), 'resources')
        #if path already exists, remove it before copying with copytree()
        if os.path.exists(resources_dir_tmp):
            shutil.rmtree(resources_dir_tmp)
            shutil.copytree(ENV['GPATH']['RESOURCES'], resources_dir_tmp)
        self.log.debug(f"Global resources copied to {resources_dir_tmp}")

        adocprops = ''
        for prop in ENV['CONF']['ADOCPROPS']:
            self.log.debug(f"CONF[ASCIIDOC] PARAM[{prop}] VALUE[{ENV['CONF']['ADOCPROPS'][prop]}]")
            if ENV['CONF']['ADOCPROPS'][prop] is not None:
                if '%s' in ENV['CONF']['ADOCPROPS'][prop]:
                    adocprops += '-a {}={} '.format(prop, ENV['CONF']['ADOCPROPS'][prop] % self.srvbes.get_path('target'))
                else:
                    adocprops += '-a {}={} '.format(prop, ENV['CONF']['ADOCPROPS'][prop])
            else:
                adocprops += '-a %s ' % prop
        runtime['adocprops'] = adocprops
        #self.log.debug(f"[COMPILATION] - Parameters passed to Asciidoctor: %s", adocprops)

        # ~ distributed = self.srvthm.get_distributed()
        distributed = self.srvbes.get_value('docs', 'targets')
        max_workers = self.srvbes.get_value('repo', 'workers')
        if max_workers is None:
            max_workers = get_default_workers()
        self.log.debug(f"Number or compiling workers: {max_workers}")
        with Executor(max_workers=max_workers) as exe:
            docs = get_source_docs(self.srvbes.get_path('tmp'))
            jobs = []
            jobcount = 0
            num = 1
            # ~ self.log.debug(f"Generating jobs")
            for doc in docs:
                COMPILE = True
                basename = os.path.basename(doc)
                if basename in distributed:
                    distributed_file = os.path.join(self.srvbes.get_path('dist'), basename)
                    cached_file = os.path.join(self.srvbes.get_path('cache'), basename.replace('.adoc', '.html'))
                    if os.path.exists(distributed_file) and os.path.exists(cached_file):
                        cached_hash = get_hash_from_file(distributed_file)
                        current_hash = get_hash_from_file(doc)
                        if cached_hash == current_hash:
                            COMPILE = False


                if COMPILE or self.params['force']:
                    cmd = "asciidoctor -q -s {} -b html5 -D {} {}".format(adocprops, self.srvbes.get_path('tmp'), doc)
                    #self.log.debug(f"CMD[%s]", cmd)
                    data = (doc, cmd, num)
                    self.log.debug(f"DOC[{basename}] compiles in JOB[{num}]")
                    job = exe.submit(self.compilation_started, data)
                    job.add_done_callback(self.compilation_finished)
                    jobs.append(job)
                    num = num + 1
                else:
                    self.log.debug(f"DOC[{basename}] cached. Avoid compiling")

            if num-1 > 0:
                self.log.debug("[COMPILATION] - START")
                # ~ self.log.debug(f"[COMPILATION] - %3s%% done", "0")
                for job in jobs:
                    adoc, res, jobid = job.result()
                    self.log.debug(f"DOC[{os.path.basename(adoc)}] compiled successfully")
                    jobcount += 1
                    if jobcount % ENV['CONF']['MAX_WORKERS'] == 0:
                        pct = int(jobcount * 100 / len(docs))
                        # ~ self.log.info("[COMPILATION] - %3s%% done", str(pct))
                        self.log.debug(f"STATS - JOB[{jobid}/{num -1}] Compilation progress: {pct}% done")

                dcompe = datetime.datetime.now()
                comptime = dcompe - dcomps
                duration = comptime.seconds
                if duration == 0:
                    duration = 1
                avgspeed = int((num - 1) / duration)
                pct = int(jobcount * 100 / len(docs))
                self.log.debug(f"STATS - JOB[{jobid}/{num -1}] Compilation progress: {pct}% done")
                self.log.debug(f"STATS - Compilation time: {comptime.seconds} seconds")
                self.log.debug(f"STATS - Compiled docs: {num - 1}")
                self.log.debug(f"STATS - Avg. Speed: {avgspeed} docs/sec")
            else:
                self.log.debug(f"STATS - Nothing to compile!")
            self.log.debug(f"[COMPILATION] - END")

    def compilation_started(self, data):
        (doc, cmd, num) = data
        res = exec_cmd(data)
        return res

    def compilation_finished(self, future):
        time.sleep(random.random())
        cur_thread = threading.current_thread().name
        x = future.result()
        if cur_thread != x:
            path_hdoc, rc, num = x
            basename = os.path.basename(path_hdoc)
            # ~ self.log.debug(f"[COMPILATION] - Job[%s] for Doc[%s] has RC[%s]", num, basename, rc)
            try:
                html = self.srvthm.build_page(path_hdoc)
            except MemoryError:
                self.log.error("Memory exhausted!")
                self.log.error("Please, consider using less workers or add more memory to your system")
                self.log.error("The application will exit now...")
                self.app.stop()
                sys.exit(errno.ENOMEM)
            except Exception as error:
                self.log.error(error)
                self.print_traceback()
                self.app.stop()
            return x

    def _finalize(self):
        pass
