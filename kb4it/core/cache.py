#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CacheManager - Intelligent caching system for KB4IT
Handles hash-based change detection and cache invalidation
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


@dataclass
class CacheEntry:
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


class CacheManager:
    """
    Manages intelligent caching for KB4IT documents.

    Features:
    - Hash-based change detection (content + metadata)
    - Persistent cache across sessions
    - Automatic cache invalidation
    - Cache statistics and reporting
    - Orphaned cache cleanup
    """

    def __init__(self, cache_dir: Path, db_dir: Path, project_name: str):
        """
        Initialize the CacheManager

        Args:
            cache_dir: Directory where compiled HTML files are stored
            db_dir: Directory where cache database is stored
            project_name: Name of the project (for unique cache file)
        """
        self.cache_dir = Path(cache_dir)
        self.db_dir = Path(db_dir)
        self.project_name = project_name

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # Cache database file
        self.db_file = self.db_dir / f"cache_{project_name}.json"

        # In-memory cache
        self._cache: Dict[str, CacheEntry] = {}

        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'new_entries': 0
        }

        self.log = get_logger('Cache')

        # Load existing cache
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache database from disk"""
        if not self.db_file.exists():
            self.log.info(f"[CACHE] - No existing cache found for {self.project_name}")
            self.log.warning(f"[CACHE] - Cache dir: {self.db_file}")
            return

        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._cache = {
                doc_id: CacheEntry.from_dict(entry_data)
                for doc_id, entry_data in data.items()
            }

            self.log.info(f"Loaded cache with {len(self._cache)} entries")

        except (json.JSONDecodeError, KeyError) as e:
            self.log.error(f"Failed to load cache: {e}. Starting fresh.")
            self._cache = {}

    def save_cache(self) -> None:
        """Persist cache database to disk"""
        try:
            data = {
                doc_id: entry.to_dict()
                for doc_id, entry in self._cache.items()
            }

            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            self.log.debug(f"Saved cache with {len(self._cache)} entries")

        except Exception as e:
            self.log.error(f"Failed to save cache: {e}")

    @staticmethod
    def compute_hash(content: Any) -> str:
        """
        Compute SHA-256 hash of content

        Args:
            content: String content or dict to hash

        Returns:
            Hexadecimal hash string
        """
        if isinstance(content, dict):
            # Sort keys for consistent hashing
            content = json.dumps(content, sort_keys=True)

        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def is_cached(self, doc_id: str, content_hash: str, metadata_hash: str) -> bool:
        """
        Check if document is cached and unchanged

        Args:
            doc_id: Document identifier
            content_hash: Current content hash
            metadata_hash: Current metadata hash

        Returns:
            True if cached and unchanged, False otherwise
        """
        if doc_id not in self._cache:
            self._stats['misses'] += 1
            return False

        entry = self._cache[doc_id]

        # Check if hashes match
        if (entry.content_hash == content_hash and
            entry.metadata_hash == metadata_hash):

            # Verify cached file still exists
            if entry.compiled_path.exists():
                self._stats['hits'] += 1
                self.log.debug(f"Cache HIT: {doc_id}")
                return True
            else:
                self.log.warning(f"Cached file missing: {entry.compiled_path}")
                self._invalidate_entry(doc_id)
                return False

        self._stats['misses'] += 1
        self.log.debug(f"Cache MISS: {doc_id} (hash mismatch)")
        return False

    def add_entry(
        self,
        doc_id: str,
        content_hash: str,
        metadata_hash: str,
        compiled_path: Path,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Add or update cache entry

        Args:
            doc_id: Document identifier
            content_hash: Content hash
            metadata_hash: Metadata hash
            compiled_path: Path to compiled HTML file
            metadata: Document metadata
        """
        entry = CacheEntry(
            doc_id=doc_id,
            content_hash=content_hash,
            metadata_hash=metadata_hash,
            compiled_path=compiled_path,
            last_compiled=datetime.now().isoformat(),
            metadata=metadata
        )

        if doc_id in self._cache:
            self.log.debug(f"Updating cache entry: {doc_id}")
        else:
            self._stats['new_entries'] += 1
            self.log.debug(f"Adding new cache entry: {doc_id}")

        self._cache[doc_id] = entry

    def get_entry(self, doc_id: str) -> Optional[CacheEntry]:
        """Get cache entry by document ID"""
        return self._cache.get(doc_id)

    def _invalidate_entry(self, doc_id: str) -> None:
        """Remove entry from cache"""
        if doc_id in self._cache:
            del self._cache[doc_id]
            self._stats['invalidations'] += 1
            self.log.debug(f"Invalidated cache entry: {doc_id}")

    def invalidate_documents(self, doc_ids: Set[str]) -> int:
        """
        Invalidate multiple documents

        Args:
            doc_ids: Set of document IDs to invalidate

        Returns:
            Number of entries invalidated
        """
        count = 0
        for doc_id in doc_ids:
            if doc_id in self._cache:
                self._invalidate_entry(doc_id)
                count += 1

        return count

    def clean_orphaned_entries(self, valid_doc_ids: Set[str]) -> int:
        """
        Remove cache entries for documents that no longer exist

        Args:
            valid_doc_ids: Set of currently valid document IDs

        Returns:
            Number of orphaned entries removed
        """
        orphaned = set(self._cache.keys()) - valid_doc_ids
        count = 0

        for doc_id in orphaned:
            entry = self._cache[doc_id]

            # Remove cached file if it exists
            if entry.compiled_path.exists():
                try:
                    entry.compiled_path.unlink()
                    self.log.debug(f"Deleted orphaned file: {entry.compiled_path}")
                except Exception as e:
                    self.log.error(f"Failed to delete {entry.compiled_path}: {e}")

            self._invalidate_entry(doc_id)
            count += 1

        if count > 0:
            self.log.info(f"Cleaned {count} orphaned cache entries")

        return count

    def get_cached_documents(self) -> Set[str]:
        """Get set of all cached document IDs"""
        return set(self._cache.keys())

    def needs_compilation(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        Determine if document needs compilation

        Args:
            doc_id: Document identifier
            content: Document content
            metadata: Document metadata
            force: Force compilation regardless of cache

        Returns:
            Tuple of (needs_compilation, reason)
        """
        if force:
            return True, "Forced compilation"

        content_hash = self.compute_hash(content)
        metadata_hash = self.compute_hash(metadata)

        if not self.is_cached(doc_id, content_hash, metadata_hash):
            if doc_id not in self._cache:
                return True, "Not in cache"
            else:
                return True, "Content or metadata changed"

        return False, "Cached and unchanged"

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_entries': len(self._cache),
            'cache_hits': self._stats['hits'],
            'cache_misses': self._stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'invalidations': self._stats['invalidations'],
            'new_entries': self._stats['new_entries'],
            'cache_size_mb': self._calculate_cache_size()
        }

    def _calculate_cache_size(self) -> float:
        """Calculate total size of cached files in MB"""
        total_size = 0
        # ~ for entry in self._cache.values():
            # ~ if entry.compiled_path.exists():
                # ~ total_size += entry.compiled_path.stat().st_size

        return round(total_size / (1024 * 1024), 2)

    def reset_statistics(self) -> None:
        """Reset statistics counters"""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'new_entries': 0
        }

    def clear_all(self) -> None:
        """Clear all cache entries and delete cached files"""
        for entry in self._cache.values():
            if entry.compiled_path.exists():
                try:
                    entry.compiled_path.unlink()
                except Exception as e:
                    self.log.error(f"Failed to delete {entry.compiled_path}: {e}")

        self._cache.clear()
        self._stats['invalidations'] = len(self._cache)

        # Remove cache database
        if self.db_file.exists():
            self.db_file.unlink()

        self.log.info("Cache completely cleared")

    def export_metadata(self, output_file: Path) -> None:
        """
        Export all cached metadata to a JSON file

        Args:
            output_file: Path to output JSON file
        """
        metadata_export = {
            doc_id: {
                'metadata': entry.metadata,
                'last_compiled': entry.last_compiled,
                'content_hash': entry.content_hash,
                'metadata_hash': entry.metadata_hash
            }
            for doc_id, entry in self._cache.items()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_export, f, indent=2)

        self.log.info(f"Exported metadata for {len(metadata_export)} documents")

    def print_cache_report(self):
        """Display detailed cache report"""
        stats = self.get_statistics()
        self.log.debug(f"[BACKEND/CACHE] - Cache Performance Report:")
        self.log.debug(f"[BACKEND/CACHE] -   📊 Total cached documents: {stats['total_entries']}")
        self.log.debug(f"[BACKEND/CACHE] -   ✅ Cache hits: {stats['cache_hits']}")
        self.log.debug(f"[BACKEND/CACHE] -   ❌ Cache misses: {stats['cache_misses']}")
        self.log.debug(f"[BACKEND/CACHE] -   🎯 Hit rate: {stats['hit_rate_percent']}%")
        self.log.debug(f"[BACKEND/CACHE] -   🗑️  Invalidations: {stats['invalidations']}")
        self.log.debug(f"[BACKEND/CACHE] -   ➕ New entries: {stats['new_entries']}")
        self.log.debug(f"[BACKEND/CACHE] -   💾 Cache size: {stats['cache_size_mb']} MB")

# Example usage functions
def example_basic_usage():
    """Example: Basic cache usage"""
    from pathlib import Path

    # Initialize cache manager
    cache = CacheManager(
        cache_dir=Path("/tmp/kb4it/cache"),
        db_dir=Path("/tmp/kb4it/db"),
        project_name="my_docs"
    )

    # Check if document needs compilation
    doc_id = "example.adoc"
    content = "= My Document\n\nSome content here."
    metadata = {"Title": "My Document", "Author": "John Doe"}

    needs_compile, reason = cache.needs_compilation(doc_id, content, metadata)

    if needs_compile:
        print(f"Document needs compilation: {reason}")

        # ... perform compilation ...
        compiled_path = Path("/tmp/kb4it/cache/example.html")

        # Add to cache
        cache.add_entry(
            doc_id=doc_id,
            content_hash=cache.compute_hash(content),
            metadata_hash=cache.compute_hash(metadata),
            compiled_path=compiled_path,
            metadata=metadata
        )
    else:
        print(f"Using cached version: {reason}")

    # Save cache
    cache.save_cache()

    # Print statistics
    stats = cache.get_statistics()
    print(f"\nCache Statistics:")
    print(f"  Entries: {stats['total_entries']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    print(f"  Cache Size: {stats['cache_size_mb']} MB")


def example_batch_processing():
    """Example: Batch document processing with cache"""
    from pathlib import Path

    cache = CacheManager(
        cache_dir=Path("/tmp/kb4it/cache"),
        db_dir=Path("/tmp/kb4it/db"),
        project_name="my_docs"
    )

    documents = [
        ("doc1.adoc", "Content 1", {"Title": "Doc 1"}),
        ("doc2.adoc", "Content 2", {"Title": "Doc 2"}),
        ("doc3.adoc", "Content 3", {"Title": "Doc 3"}),
    ]

    to_compile = []

    # Check each document
    for doc_id, content, metadata in documents:
        needs_compile, reason = cache.needs_compilation(doc_id, content, metadata)

        if needs_compile:
            to_compile.append((doc_id, content, metadata))
            print(f"Will compile: {doc_id} ({reason})")
        else:
            print(f"Cached: {doc_id}")

    print(f"\nCompiling {len(to_compile)} of {len(documents)} documents")

    # Compile only what's needed
    for doc_id, content, metadata in to_compile:
        # ... compilation logic ...
        print(f"Compiling {doc_id}...")

        compiled_path = Path(f"/tmp/kb4it/cache/{doc_id.replace('.adoc', '.html')}")

        cache.add_entry(
            doc_id=doc_id,
            content_hash=cache.compute_hash(content),
            metadata_hash=cache.compute_hash(metadata),
            compiled_path=compiled_path,
            metadata=metadata
        )

    # Clean orphaned entries
    valid_ids = {doc_id for doc_id, _, _ in documents}
    orphaned = cache.clean_orphaned_entries(valid_ids)
    print(f"\nCleaned {orphaned} orphaned entries")

    # Save cache
    cache.save_cache()

    # Show statistics
    stats = cache.get_statistics()
    print(f"\nFinal Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # Run examples
    print("=== Basic Usage Example ===\n")
    example_basic_usage()

    print("\n\n=== Batch Processing Example ===\n")
    example_batch_processing()
