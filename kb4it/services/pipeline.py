#!/usr/bin/env python

"""
The pipeline of one build: the Processor, Compiler and Deployer, made once the theme is known.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from kb4it.core.log import get_logger
from kb4it.services.compiler import Compiler
from kb4it.services.deployer import Deployer
from kb4it.services.processor import Processor


class Pipeline:
    """Stages 3, 5 and 6 of a build, with their collaborators given rather than looked up (AR-03).

    The backend makes it at the end of stage 1, when the theme is loaded, and keeps it as
    `backend.pipeline` for the rest of the build. A new build makes a new pipeline.
    """

    def __init__(self, backend, db, theme, settings, callbacks=None, log_file=None):
        self.log = get_logger("Pipeline")
        self.settings = settings
        self.processor = Processor(backend, db, theme)
        self.compiler = Compiler(backend, db, theme, self.processor, callbacks)
        self.deployer = Deployer(backend, theme, log_file)
        self.log.debug("[PIPELINE] READY services=Processor,Compiler,Deployer")

    def service(self, name):
        """Return the Processor, Compiler or Deployer of this build by name, or None."""
        return {"Processor": self.processor, "Compiler": self.compiler, "Deployer": self.deployer}.get(name)
