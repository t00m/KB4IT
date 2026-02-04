#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Cleaner service
"""

import os

from kb4it.core.service import Service

class Deployer(Service):
    """KB4IT Cleaner Service"""

    def _initialize(self):
        """Initialize workflow module."""
        self.srvbes = self.app.get_service('Backend')
        self.log.debug(f"[CLEANUP] - START")

    def
        pattern = os.path.join(self.get_path('source'), '*.*')
        extra = glob.glob(pattern)
        copy_docs(extra, self.get_path('cache'))
        delete_target_contents(self.get_path('dist'))
        self.log.debug(f"Distributed files deleted")
        distributed = self.get_value('docs', 'targets')
        for adoc in distributed:
            source = os.path.join(self.get_path('tmp'), adoc)
            target = self.get_path('www')
            try:
                shutil.copy(source, target)
            except Exception as warning:
                # FIXME
                # ~ self.log.warning(warning)
                # ~ self.log.warning("[CLEANUP] - Missing source file: %s", source)
                pass
        self.log.debug(f"Copy temporary files to distributed directory")

        delete_target_contents(self.get_path('target'))
        self.log.debug(f"Deleted target contents in: %s", self.get_path('target'))
        self.log.debug(f"[CLEANUP]")

