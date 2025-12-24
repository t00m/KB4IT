#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cache Manager.
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: helping module for caching KB4IT objects
"""

import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from kb4it.core.log import get_logger

from kb4it.core.env import ENV
from kb4it.core.util import json_load
from kb4it.core.service import Service



@dataclass
class KB4ITObject:
    """Represents a cached document with its metadata"""
    doc_id: str
    content_hash: str
    metadata_hash: str
    compiled_path: Path
    last_compiled: str
    metadata: Dict[str, Any]

    @property
    def combined_hash(self) -> str:
        """Combined hash for quick comparison"""
        return self.content_hash + self.metadata_hash

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['compiled_path'] = str(self.compiled_path)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Create from dictionary"""
        data['compiled_path'] = Path(data['compiled_path'])
        return cls(**data)

class CacheManager(Service):
    """KB4IT Cache Manager"""

    def initialize(self):
        """"""
